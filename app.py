
from pathlib import Path
import duckdb
import streamlit as st
from agent.entity_resolver import detect_entity_followup
from agent.sql_generator import generate_sql
from database.query_executor import run_query
from agent.context_builder import build_context
from guardrails.sql_validator import validate_sql
from guardrails.context_validator import validate_context
from guardrails.answer_validator import validate_answer
from guardrails.hallucination_checker import check_hallucination
from guardrails.result_validator import validate_result
from agent.contextual_question_builder import build_contextual_question
from agent.metric_resolver import detect_metric_followup
from agent.metric_question_builder import build_metric_question
from agent.time_resolver import detect_time_followup
from agent.time_question_builder import build_time_question
from agent.context_continuation_resolver import detect_context_continuation
from agent.context_continuation_builder import build_context_continuation_question
from agent.insight_generator import (
    generate_insight,
    generate_followup_insight
)
from agent.conversation_state import (
    create_conversation_state,
    update_conversation_state
)
from agent.chart_generator import (
    should_generate_chart,
    get_chart_config,
    prepare_chart_dataframe
)
from agent.plotly_chart_renderer import (
    render_bar_chart,
    render_line_chart
)
from guardrails.relevance_validator import (
    is_ipl_relevant
)


#DEBUG_MODE = False
# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IPL Intelligence Agent",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "ipl.db"


# ============================================================
# DATABASE INFORMATION
# ============================================================

@st.cache_data
def get_database_statistics():
    """
    Retrieve IPL dataset statistics from DuckDB.
    """

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM matches) AS match_count,

                (SELECT COUNT(*) FROM deliveries)
                    AS delivery_count,

                (
                    SELECT COUNT(DISTINCT season)
                    FROM matches
                ) AS season_count,

                (
                    SELECT MIN(
                        TRY_CAST(
                            SUBSTRING(season, 1, 4)
                            AS INTEGER
                        )
                    )
                    FROM matches
                ) AS first_season,

                (
                    SELECT MAX(
                        TRY_CAST(
                            SUBSTRING(season, 1, 4)
                            AS INTEGER
                        )
                    )
                    FROM matches
                ) AS last_season
            """
        ).fetchone()

        return {
            "matches": row[0],
            "deliveries": row[1],
            "season_count": row[2],
            "first_season": row[3],
            "last_season": row[4],
        }

    finally:
        connection.close()


# ============================================================
# SESSION STATE
# ============================================================

if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_question" not in st.session_state:
    st.session_state.last_question = None

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

if "last_context" not in st.session_state:
    st.session_state.last_context = None
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = (
        create_conversation_state()
    )

# ============================================================
# LOAD DATASET STATISTICS
# ============================================================

try:
    stats = get_database_statistics()

except Exception as error:
    st.error(
        "The IPL database could not be opened. "
        "Confirm that `ipl.db` is in the same folder as `app.py`."
    )

    st.exception(error)
    st.stop()


matches = stats["matches"]
deliveries = stats["deliveries"]
season_count = stats["season_count"]
first_season = stats["first_season"]
last_season = stats["last_season"]

coverage = f"{first_season}–{last_season}"


# ============================================================
# HELPER FUNCTIONS FOR QUESTION PROCESSING, FOLLOW-UP DETECTION, 
# AND INSIGHT GENERATION.
# ============================================================

def clean_question(question):
    """
    Clean and validate a user's question.
    """

    if question is None:
        return ""

    return question.strip()

# ********************************************************
# the following function is used to detect simple follow-up questions 
# that ask for reasoning behind a previous answer. 
# It checks if the question matches common follow-up phrases like "why", "how", or "explain".

def is_followup_question(question: str):
    """
    Detect simple follow-up questions.
    """

    if not question:
        return False

    question = (
        question.strip()
                .lower()
                .replace("?", "")
                .replace(".", "")
                .replace("!", "")
                .replace(",", "")
                .replace("'", "")
    )

    followup_keywords = [
        "why",
        "how",
        "explain",
        "more",
        "reason",
        "agree",
        "justify",
        "prove",
        "disagree",
        "really",
        "evidence",
        "are you sure",
        "sure"
    ]

    return question in followup_keywords

#****************************************************************
# SAVE ANALYSIS STATE

def save_analysis_state(
    question,
    generated_sql,
    result,
    insight,
    context,
):
    """
    Save the latest successful analytical result
    and update accumulated conversation state.
    """
    #st.write(st.session_state.conversation_state)

    st.session_state.last_question = (
        question
    )

    st.session_state.last_sql = (
        generated_sql
    )

    st.session_state.last_result = (
        result
    )

    st.session_state.last_answer = (
        insight
    )

    st.session_state.last_context = (
        context
    )

    st.session_state.conversation_state = (
        update_conversation_state(
            st.session_state.conversation_state,
            question,
            context,
        )
    )

# ********************************************************
# The following function is used to detect acknowledgement messages
def is_acknowledgement(
    question: str
):
    """
    Detect acknowledgement messages.
    """

    if not question:
        return False

    question = (
        question.strip()
                .lower()
                .replace("?", "")
                .replace(".", "")
                .replace("!", "")
                .replace(",", "")
                .replace("'", "")
    )

    acknowledgements = [
        "ok",
        "okay",
        "thanks",
        "thank you",
        "got it",
        "understood",
        "cool",
        "nice",
        "great",
        "perfect",
        "makes sense"
    ]

    return question in acknowledgements

# ********************************************
# The following function to generate insights.

def run_ipl_analysis(question):
    """
    Send the question to Gemini, generate SQL,
    execute it through the DuckDB tool and return
    the SQL and generate an insight when required.
    """

    #validate_relevance(question)

    generated_sql = generate_sql(question)

    validate_sql(generated_sql)

    query_result = run_query(generated_sql)

    validate_result(query_result)

    context = build_context(
        question,
        query_result
    )

    validate_context(
        context
    )

    if context["needs_insight"]:
        try:
            insight = generate_insight(
                question,
                query_result,
                context
            )

            validate_answer(insight)

            hallucination_result = (
                check_hallucination(insight, context)
            )

            #print(
            #    "Hallucination check result: ",
            #    hallucination_result
            #)

        except Exception as error:

            print(
                "Insight generation fallback: ",
                error
            )
            insight = create_direct_answer(
                question,
                query_result
            )
    else:
        insight = create_direct_answer(
            question,
            query_result
        )

    return generated_sql, query_result, insight, context

# The following function is used to create a simple human-readable 
# answer from the retrieved result. It does not use Gemini for 
# narrative insight yet.

def create_direct_answer(question, result):
    """
    Create a simple human-readable answer from the
    retrieved result.

    This does not use Gemini for narrative insight yet.
    """

    if result is None or result.empty:
        return (
            "The analysis completed successfully, but no matching "
            "IPL records were found."
        )

    if len(result) == 1:
        first_row = result.iloc[0]

        values = []

        for column in result.columns:
            value = first_row[column]

            values.append(
                f"**{column.replace('_', ' ').title()}:** {value}"
            )

        return (
            f"Based on the IPL dataset, the answer to "
            f"“{question}” is:\n\n"
            + "  \n".join(values)
        )

    return (
        f"The analysis returned **{len(result):,} results** "
        f"for the question:\n\n"
        f"**{question}**\n\n"
        "The leading results are shown in the Data tab."
    )

# The following function is used to display user-friendly error messages. 
# It checks the error message and provides a more understandable 
# explanation to the user, along with suggestions for resolving the issue.

def display_error(error):
    """
    Display user-friendly error messages.
    """

    error_text = str(error)

    if (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "quota" in error_text.lower()
    ):
        st.error(
            "Gemini's request quota has been reached. "
            "Please wait for the quota to reset or select "
            "another available Gemini model in `config.py`."
        )

    elif "Binder Error" in error_text:
        st.error(
            "Gemini generated SQL containing a column, table, "
            "or datatype that does not match the IPL database."
        )

        with st.expander(
            "View technical error",
            expanded=False,
        ):
            st.exception(error)

    elif "Conversion Error" in error_text:
        st.error(
            "The generated SQL could not convert one of the "
            "IPL data values into the expected datatype."
        )

        with st.expander(
            "View technical error",
            expanded=False,
        ):
            st.exception(error)

    elif "Catalog Error" in error_text:
        st.error(
            "The generated SQL referenced an IPL database "
            "table or column that does not exist."
        )

        with st.expander(
            "View technical error",
            expanded=False,
        ):
            st.exception(error)

    elif "Blocked SQL command" in error_text:
        st.error(
            "The query was blocked by the SQL safety validator."
        )

    elif (
        "503" in error_text
        or "UNAVAILABLE" in error_text
        or "high demand" in error_text.lower()
    ):
        st.error(
            "Gemini is currently experiencing high demand. "
            "Please try again in a few moments."
        )

    else:
        st.error(
            "The IPL question could not be processed."
        )

        with st.expander(
            "View technical error",
            expanded=False,
        ):
            st.exception(error)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🏏 IPL Intelligence")

    st.caption(
        "Your AI-powered analyst for the "
        "Indian Premier League."
    )

    st.subheader("Popular Questions")

    st.markdown(
        """
        🏏 Who scored the most runs?

        🎯 Who took the most wickets?

        ⚡ Best death-over batter?

        🔥 Top powerplay wicket takers?

        🏆 Most Player of the Match awards?

        🏟 Which venue hosted the most matches?
            """,
        unsafe_allow_html=True
    )
    
# ============================================================
# PRODUCT HEADER
# ============================================================

#st.title("🏏 IPL Intelligence Agent")

st.markdown(
    """
    <h1 style='text-align: center;'>
        🏏 IPL Intelligence Agent
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h3 style='text-align: center;'>
        AI-Powered Cricket Analytics for the Indian Premier League
    </h3>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align:center;
             font-size:20px; 
             color:#666666;'>
        Ask. Analyze. Discover.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align:center;
              color:#666666;
              font-size:16px;'>
        Explore IPL players, teams, venues, powerplays,
        death overs, chasing performance and match-winning trends
        using natural language.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div style="
        background-color:#e8f0fe;
        padding:14px;
        border-radius:8px;
        display:flex;
        justify-content:space-around;
        align-items:center;
        font-size:16px;
        font-weight:450;
    ">
        <div style="flex:1; text-align:left;">
            📅 Coverage: {coverage}
        </div>
        <div style="flex:1; text-align:center;">
            🏏 Matches: {matches:,}
        </div>
        <div style="flex:1; text-align:right;">
            📊 Deliveries: {deliveries:,}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================================
# USERS QUESTION INPUT...
# =====================================================================

typed_question = st.chat_input(
    "Ask anything about IPL cricket..."
)

selected_question = st.session_state.selected_question

if selected_question:
    current_question = selected_question
    st.session_state.selected_question = None

elif typed_question:
    current_question = typed_question

else:
    current_question = None


# =====================================================================
# ************ EXECUTE AGENTS WORKFLOW ***********************
# =====================================================================

if current_question:
    current_question = clean_question(current_question)

    if current_question:

        #
        # Relevance Check
        #

        if not is_ipl_relevant(current_question):

            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                st.warning(
                    "I couldn't identify any IPL-related concept in the question. "
                    "Please ask about IPL players, teams, seasons, venues, matches, or statistics."
                )

            st.stop()

        entity_result = (
            detect_entity_followup(
                current_question
            )
        )

        metric_result = (
            detect_metric_followup(
                current_question
            )
        )

        time_result = (
            detect_time_followup(
                current_question
            )
        )

        continuation_result = (
            detect_context_continuation(
                current_question
            )
        )
        #st.write("Continuation Result: ", continuation_result)

        if is_acknowledgement(current_question):

            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                st.markdown("Glad that helped. 🏏")

# ------------------------------------------------------------
#      ********** ROUTER STARTING FROM HERE ********
#           TIME FOLLOW-UP WORKFLOW
# ------------------------------------------------------------

        elif (
            time_result["is_time_followup"]
            and st.session_state.last_context is not None
        ):

            rewritten_question = (
                build_time_question(
                    time_result,
                    st.session_state.conversation_state
                )
            )

            with st.chat_message("user"):
                st.markdown(
                    current_question
                )

            with st.chat_message("assistant"):

                if not rewritten_question:

                    st.warning(
                        "I detected a time-aware follow-up, "
                        "but the previous analytical context does not "
                        "support a time-filtered rewrite."
                        
                    )

                else:

                    try:

                        with st.status(
                            "Analyzing the selected period...",
                            expanded=True,
                        ) as status:

                        
                            #st.write(
                            #    "Time-Aware Follow-up Detected"
                            #)

                            st.write(
                                "Time Filter:",
                                time_result
                            )

                            #st.write(
                            #    "Rewritten Question:",
                            #   rewritten_question
                            #)

                            (
                                generated_sql,
                                result,
                                insight,
                                context,
                            ) = run_ipl_analysis(
                                rewritten_question
                            )

                            status.update(
                                label="Time analysis completed",
                                state="complete",
                                expanded=False,
                            )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            insight
                        )

                        # Save the fresh metric result
                        # as the latest conversation context.

                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context
                        )

                        #st.write(st.session_state.conversation_state)

                        with st.expander(
                            "View supporting data",
                            expanded=False,
                        ):

                            st.dataframe(
                                result,
                                width="stretch",
                                hide_index=True,
                            )

                        with st.expander(
                            "View generated SQL",
                            expanded=False,
                        ):

                            st.code(
                                generated_sql,
                                language="sql",
                            )

                        with st.expander(
                            "View Context Builder Output",
                            expanded=False,
                        ):

                            st.json(
                                context
                            )

                    except Exception as error:

                        display_error(
                            error
                        )
  
# -----------------------------------------------------------------
#       METRIC-AWARE FOLLOW-UP WORKFLOW
# -----------------------------------------------------------------

        elif (
            metric_result["is_metric_followup"]
            and st.session_state.last_context is not None
        ):
            
            rewritten_question = (
                build_metric_question(
                    metric_result,
                    st.session_state.conversation_state
                )
            )

            with st.chat_message("user"):
                st.markdown(
                    current_question
                )

            with st.chat_message("assistant"):

                if not rewritten_question:

                    st.warning(
                        "I detected a metric follow-up, "
                        "but the previous context does not "
                        "contain enough information to build "
                        "a new analytical question."
                    )

                else:

                    try:

                        with st.status(
                            "Analyzing the new metric...",
                            expanded=True,
                        ) as status:

                            #st.write(
                            #    "Metric Follow-up Detected"
                            #)

                            #st.write(
                            #    "New metric:",
                            #    metric_result["metric"]
                            #)

                            #st.write(
                            #    "Rewritten Question:",
                            #    rewritten_question
                            #)

                            (
                                generated_sql,
                                result,
                                insight,
                                context,
                            ) = run_ipl_analysis(
                                rewritten_question
                            )

                            status.update(
                                label="Metric analysis completed",
                                state="complete",
                                expanded=False,
                            )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            insight
                        )

                        # Save the fresh metric result
                        # as the latest conversation context.
                        
                        #st.session_state.last_question = (
                        #    rewritten_question
                        #)

                        #st.session_state.last_sql = (
                        #    generated_sql
                        #)

                        #st.session_state.last_result = (
                        #    result
                        #)

                        #st.session_state.last_answer = (
                        #    insight
                        #)

                        #st.session_state.last_context = (
                        #    context
                        #)
                        
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context
                        )
                        #st.write(st.session_state.conversation_state)

                        with st.expander(
                            "View supporting data",
                            expanded=False,
                        ):

                            st.dataframe(
                                result,
                                width="stretch",
                                hide_index=True,
                            )

                        with st.expander(
                            "View generated SQL",
                            expanded=False,
                        ):

                            st.code(
                                generated_sql,
                                language="sql",
                            )

                        with st.expander(
                            "View Context Builder Output",
                            expanded=False,
                        ):

                            st.json(
                                context
                            )

                    except Exception as error:

                        display_error(
                            error
                        )
# -----------------------------------------------------------------
#               ENTITY FOLLOW-UP WORKFLOW
# -----------------------------------------------------------------

        elif ( 
            entity_result["is_entity_followup"]
            and st.session_state.last_context is not None
        ):                
            rewritten_question = (
                build_contextual_question(
                    entity_result,
                    st.session_state.conversation_state
                )
            )

            with st.chat_message("user"):

                st.markdown(
                    current_question
                )

            with st.chat_message("assistant"):

                if not rewritten_question:

                    st.warning(
                    "I detected an entity follow-up, "
                    "but the previous context does not "
                    "contain enough information to build "
                    "a comparison."
                    )
                else:

                    try:

                        #st.write(
                        #    "Entity Follow-up Detected"
                        #)

                        #st.write(
                        #    "Rewritten Question",
                        #    rewritten_question
                        #)

                        generated_sql, result, insight, context = (
                            run_ipl_analysis(
                                rewritten_question
                            )
                        )
                        #print("Generated Context: ", context)

                        #st.write("Generated SQL")
                        #st.code(
                        #    generated_sql,
                        #    language="sql"
                        #)

                        st.write("Analytical Data")
                        st.dataframe(
                            result,
                            width="stretch",
                            hide_index=True
                        )

                        st.markdown(
                            insight
                        )
                        
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context
                        )
                        #st.write(st.session_state.conversation_state)

                    except Exception as error:

                        display_error(
                            error
                        )
# -------------------------------------------------------------------
# ROUTERS FOR CONTEXTUAL FOLLOW-UP QUESTIONS
# -------------------------------------------------------------------

        elif ( 
            continuation_result["is_context_continuation"]
            and st.session_state.last_context is not None
        ):                
            rewritten_question = (
                build_context_continuation_question(
                    continuation_result,
                    st.session_state.conversation_state
                )
            )

            with st.chat_message("user"):

                st.markdown(
                    current_question
                )

            with st.chat_message("assistant"):

                if not rewritten_question:

                    st.warning(
                    "I detected a contextual follow-up, "
                    "but the previous context is not "
                    "sufficient to build a new question."                    
                    )
                else:

                    try:

                        #st.write(
                        #    "Context Continuation Detected"
                        #)

                        #st.write(
                        #    "Rewritten Question",
                        #    rewritten_question
                        #)

                        generated_sql, result, insight, context = (
                            run_ipl_analysis(
                                rewritten_question
                            )
                        )

                        #st.write("Generated SQL")
                        #st.code(
                        #    generated_sql,
                        #    language="sql"
                        #)

                        st.write("Analytical Data")
                        st.dataframe(
                            result,
                            width="stretch",
                            hide_index=True
                        )

                        st.markdown(
                            insight
                        )
                        
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context
                        )
                        #st.write(st.session_state.conversation_state)

                    except Exception as error:

                        display_error(
                            error
                        )

# -------------------------------------------------------------------
# FOLLOW-UP WITHOUT PREVIOUS CONTEXT
# -------------------------------------------------------------------

        elif (
            time_result["is_time_followup"]
            or metric_result["is_metric_followup"]
            or entity_result["is_entity_followup"]
            or continuation_result["is_context_continuation"]
        ):

            with st.chat_message("user"):
                st.markdown(
                    current_question
                )

            with st.chat_message("assistant"):
                st.warning(
                    "Please ask an IPL statistics question first. "
                    "I need previous analytical context before "
                    "processing this follow-up."
                )
# -------------------------------------------------------------------
#           SIMPLE FOLLOW-UP QUESTION WORKFLOW
# -------------------------------------------------------------------
   
        elif is_followup_question(current_question):

            if (
                st.session_state.last_question
                and st.session_state.last_answer
                and st.session_state.last_result is not None
                and st.session_state.last_context is not None
            ):
                with st.chat_message("user"):
                    st.markdown(current_question)

                with st.chat_message("assistant"):
                    try:
                        with st.status(
                            "Reviewing the previous analysis...",
                            expanded=True,
                        ) as status:

                            st.write(
                                "Using the previous question, answer and results"
                            )

                            followup_answer = generate_followup_insight(
                                current_question,
                                st.session_state.last_question,
                                st.session_state.last_answer,
                                st.session_state.last_result,
                                st.session_state.last_context,
                            )

                            validate_answer(followup_answer)

                            status.update(
                                label="Follow-up analysis completed",
                                state="complete",
                                expanded=False,
                            )

                        st.markdown("### 🏏 Answer")
                        st.markdown(followup_answer)

                        st.session_state.last_answer = followup_answer

                        if st.session_state.last_result is not None:
                            with st.expander(
                                "View supporting data",
                                expanded=False,
                            ):
                                st.dataframe(
                                    st.session_state.last_result,
                                    width="stretch",
                                    hide_index=True,
                                )

                        if st.session_state.last_sql:
                            with st.expander(
                                "View generated SQL",
                                expanded=False,
                            ):
                                st.code(
                                    st.session_state.last_sql,
                                    language="sql",
                                )

                    except Exception as error:
                        display_error(error)

            else:
                st.warning(
                    "Please ask an IPL statistics question first. "
                    "I need a previous result before I can explain why."
                )

# ------------------------------------------------------------------
#                   NEW QUESTION WORKFLOW
# ------------------------------------------------------------------

        else:
            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                try:
                    with st.status(
                    "Analyzing IPL data...",
                    expanded=True,
                    ) as status:

                        st.write(
                            "Understanding the cricket question"
                        )

                        st.write(
                            "Generating DuckDB SQL with Gemini"
                        )

                        st.write(
                            "Validating and executing the SQL"
                        )

                        st.write(
                            "Building analytical context"
                        )

                        generated_sql, result, insight, context = run_ipl_analysis(
                            current_question
                        )

                        if context["needs_insight"]:
                            st.write(
                                "Generating the cricket insight"
                            )
                        else:
                            st.write(
                                "Preparing the retrieved records"
                            )

                        status.update(
                            label="IPL analysis completed",
                            state="complete",
                            expanded=False,
                        )

                    answer = insight

                    # Save context for follow-up questions
                    
                    #st.session_state.last_question = current_question
                    #st.session_state.last_sql = generated_sql
                    #st.session_state.last_result = result
                    #st.session_state.last_answer = answer
                    #st.session_state.last_context = context
                    
                    save_analysis_state(
                        current_question,
                        generated_sql,
                        result,
                        insight,
                        context
                    )
                    #st.write(st.session_state.conversation_state)

                    answer_tab, chart_tab,data_tab, sql_tab = st.tabs(
                        [
                            "Answer",
                            "Chart",
                            "Data",
                            "Generated SQL",
                        ]
                    )
#******************* answer_tab is always shown. ******************

                    with answer_tab:
                        st.markdown(answer)

                        if result is not None and not result.empty:
                            if len(result) == 1:
                                st.success(
                                    "One leading result identified."
                                )
                            else:
                                st.success(
                                    f"{len(result):,} ranked results identified."
                                )

#********** chart_tab is only shown when a result is returned. **********

                    with chart_tab:

                        st.subheader("📊 Visual Analysis")

                        if should_generate_chart(result):

                            chart_config = get_chart_config(result)

                            st.write("chart config", chart_config)
                            st.write("columns",result.columns.tolist())
                            st.write(result.head())

                            chart_df = prepare_chart_dataframe(
                                result,
                                chart_config
                            )

                            if chart_config["type"] == "line":

                                fig = render_line_chart(chart_df)

                                st.plotly_chart(
                                    fig,
                                    use_container_width= True
                                )
                                #st.line_chart(
                                #    chart_df,
                                #    width="stretch"
                                #)

                            elif chart_config["type"] == "bar":

                                fig = render_bar_chart(chart_df)

                                st.plotly_chart(
                                    fig,
                                    use_container_width= True
                                )

                                #st.bar_chart(
                                #    chart_df,
                                #    width="stretch"
                                #)

                            else:

                                st.dataframe(
                                    chart_df,
                                    width="stretch"
                                )

                        else:

                            st.info(
                                "Not enough data available to generate a chart."
                            )

# ********** Data and SQL tabs are only shown when a result is returned. **********

                    with data_tab:
                        if result is None or result.empty:
                            st.warning(
                                "No matching IPL records were found."
                            )

                        else:
                            st.dataframe(
                                result,
                                width="stretch",
                                hide_index=True,
                            )

                            csv_data = result.to_csv(
                                index=False
                            ).encode("utf-8")

                            st.download_button(
                                label="Download results as CSV",
                                data=csv_data,
                                file_name="ipl_intelligence_results.csv",
                                mime="text/csv",
                                width="stretch",
                            )

                    with sql_tab:
                        st.code(
                            generated_sql,
                            language="sql",
                        )

                        st.caption(
                            "Generated by Gemini and executed through "
                            "the read-only DuckDB query tool."
                        )

                        with st.expander(
                            "View Context Builder Output",
                            expanded=False,
                        ):
                            st.json(context)

                except Exception as error:
                    display_error(error)

# ============================================================
#                      PAGE FOOTER
# ============================================================

footer_left, footer_right = st.columns(2)

with footer_left:
    st.caption(
        "Powered by Gemini • DuckDB • Streamlit"
    )

with footer_right:
    st.caption(
        " "
    )

# ============================================================
#                      END OF PAGE
# ============================================================