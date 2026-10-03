
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
from agent.insight_generator import (
    generate_insight,
    generate_followup_insight
)


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

#if "messages" not in st.session_state:
#    st.session_state.messages = []

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
# HELPER FUNCTIONS
# ============================================================

def clean_question(question):
    """
    Clean and validate a user's question.
    """

    if question is None:
        return ""

    return question.strip()

# the following function is used to detect simple follow-up questions that ask for reasoning behind a previous answer. It checks if the question matches common follow-up phrases like "why", "how", or "explain".
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
        "why?",
        "how?",
        "explain?",
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

# The following function to generate insights.
def run_ipl_analysis(question):
    """
    Send the question to Gemini, generate SQL,
    execute it through the DuckDB tool and return
    the SQL and generate an insight when required.
    """

    generated_sql = generate_sql(question)

    validate_sql(generated_sql)

    query_result = run_query(generated_sql)

    validate_result(query_result)

    context = build_context(
        question,
        query_result
    )

    print("############################")
    print(context)
    print("############################\n")

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

            print(
                "Hallucination check result: ",
                hallucination_result
            )

        except Exception:
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

  #  st.divider()

  #  st.subheader("Explore")

    st.subheader("Popular Questions")

    st.markdown("""
🏏 Who scored the most runs?

🎯 Who took the most wickets?

⚡ Best death-over batter?

🔥 Top powerplay wicket takers?

🏆 Most Player of the Match awards?

🏟 Which venue hosted the most matches?
    """)
    
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

# ============================================================
# QUESTION INPUT
# ============================================================

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


# ============================================================
# EXECUTE AGENT WORKFLOW
# ============================================================

if current_question:
    current_question = clean_question(current_question)

    if current_question:

        entity_result = (
            detect_entity_followup(
                current_question
            )
        )

        if is_acknowledgement(current_question):

            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                st.markdown("Glad that helped. 🏏")

        elif ( 
            #st.session_state.last_context 
            entity_result["is_entity_followup"]
            and st.session_state.last_context is not None
        ):

            #entity_result = (
            #    detect_entity_followup(
            #        current_question
            #    )
            #)

            #if entity_result[
            #    "is_entity_followup"
            #]:

                rewritten_question = (
                    build_contextual_question(
                        entity_result,
                        st.session_state.last_context
                    )
                )

                with st.chat_message("user"):

                    st.markdown(
                        current_question
                    )

                with st.chat_message("assistant"):

                    try:

                        st.write(
                            "Entity Follow-up Detected"
                        )

                        st.write(
                            f"Rewritten Question: "
                            f"{rewritten_question}"
                        )

                        generated_sql, result, insight, context = (
                            run_ipl_analysis(
                                rewritten_question
                            )
                        )

                        st.write("Rewritten Question")
                        st.write(rewritten_question)
                        st.write("Generated SQL")
                        st.code(
                            generated_sql,
                            language="sql"
                        )
                        st.write("Returned Data")
                        st.dataframe(result)

                        st.markdown(
                            insight
                        )

                    except Exception as error:

                        display_error(
                            error
                        )

        # --------------------------------------------
        # FOLLOW-UP QUESTION WORKFLOW
        # --------------------------------------------
   
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
                                    use_container_width=True,
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

        # --------------------------------------------
        # NEW QUESTION WORKFLOW
        # --------------------------------------------

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
                    st.session_state.last_question = current_question
                    st.session_state.last_sql = generated_sql
                    st.session_state.last_result = result
                    st.session_state.last_answer = answer
                    st.session_state.last_context = context

                    answer_tab, data_tab, sql_tab = st.tabs(
                        [
                            "Answer",
                            "Data",
                            "Generated SQL",
                        ]
                    )

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

                    with data_tab:
                        if result is None or result.empty:
                            st.warning(
                                "No matching IPL records were found."
                            )

                        else:
                            st.dataframe(
                                result,
                                use_container_width=True,
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
                                use_container_width=True,
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
# FOOTER
# ============================================================

#st.divider()

footer_left, footer_right = st.columns(2)

with footer_left:
    st.caption(
        "Powered by Gemini • DuckDB • Streamlit"
    )

with footer_right:
    st.caption(
        " "
    )
