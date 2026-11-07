from pathlib import Path
import re
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
from agent.insight_generator import generate_insight, generate_followup_insight
from agent.conversation_state import create_conversation_state, update_conversation_state
from agent.chart_generator import should_generate_chart, get_chart_config, prepare_chart_dataframe
from agent.plotly_chart_renderer import render_bar_chart, render_line_chart
from guardrails.relevance_validator import is_ipl_relevant
from agent.incomplete_query_detector import detect_incomplete_ipl_query
from knowledge_agent.knowledge_retriever import KnowledgeRetriever
from knowledge_agent.knowledge_router import detect_knowledge_intent
from knowledge_agent.knowledge_agent import generate_knowledge_answer


DEBUG_MODE = False

st.set_page_config(
    page_title="IPL Intelligence Agent",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "ipl.db"


@st.cache_data
def get_database_statistics():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = duckdb.connect(str(DATABASE_PATH), read_only=True)
    try:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM matches) AS match_count,
                (SELECT COUNT(*) FROM deliveries) AS delivery_count,
                (SELECT COUNT(DISTINCT season) FROM matches) AS season_count,
                (
                    SELECT MIN(TRY_CAST(SUBSTRING(season, 1, 4) AS INTEGER))
                    FROM matches
                ) AS first_season,
                (
                    SELECT MAX(TRY_CAST(SUBSTRING(season, 1, 4) AS INTEGER))
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


SESSION_DEFAULTS = {
    "selected_question": None,
    "last_sql": None,
    "last_result": None,
    "last_question": None,
    "last_answer": None,
    "last_context": None,
}

for key, default_value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = create_conversation_state()

retriever = KnowledgeRetriever()

try:
    stats = get_database_statistics()
except Exception as error:
    st.error(
        "The IPL database could not be opened. "
        "Confirm that `ipl.db` is in the same folder as `app.py`."
    )
    st.exception(error)
    st.stop()

coverage = f"{stats['first_season']}–{stats['last_season']}"


def clean_question(question):
    if question is None:
        return""
    
    question = question.strip()

    # collapse multiple spaces
    question = re.sub(
        r"\+$",
        "",
        question
    )
    #Remove trailing punctuation
    question = re.sub(
        r"[^\w\s]+$",
        "",
        question
    )
    return question.strip()

def _normalize_short_message(question):
    return (
        question.strip()
        .lower()
        .replace("?", "")
        .replace(".", "")
        .replace("!", "")
        .replace(",", "")
        .replace("'", "")
        .replace(">", "")
        .replace("<", "")
    )

############################### FOLLOW UP QUESTION #####################################
def is_followup_question(question: str):
    if not question:
        return False

    followup_keywords = {
        "why", "how", "explain", "more", "reason", "agree",
        "justify", "prove", "disagree", "really", "evidence",
        "are you sure", "sure",
    }
    return _normalize_short_message(question) in followup_keywords

############################### ACKNOWLEDGEMENT #####################################
def is_acknowledgement(question: str):
    if not question:
        return False

    acknowledgements = {
        "ok", "okay", "thanks", "thank you", "got it", "understood",
        "cool", "nice", "great", "perfect", "makes sense",
    }
    return _normalize_short_message(question) in acknowledgements


def enrich_context_with_result(context, result):
    enriched = dict(context or {})

    if result is None or result.empty:
        return enriched

    first_row = result.iloc[0]
    entity_columns = (
        "batter", "bowler", "player", "team", "winner", "fielder", "venue"
    )

    for column in entity_columns:
        if column not in result.columns:
            continue

        value = first_row[column]
        if value is None:
            continue

        enriched["primary_entity"] = value

        if column in {"batter", "bowler", "player"}:
            enriched["player"] = value
        elif column in {"team", "winner"}:
            enriched["team"] = value

        break

    return enriched


def save_analysis_state(question, generated_sql, result, insight, context):
    st.session_state.last_question = question
    st.session_state.last_sql = generated_sql
    st.session_state.last_result = result
    st.session_state.last_answer = insight
    st.session_state.last_context = context
    st.session_state.conversation_state = update_conversation_state(
        st.session_state.conversation_state,
        question,
        context,
    )


def create_direct_answer(question, result):
    if result is None or result.empty:
        return "The analysis completed successfully, but no matching IPL records were found."

    if len(result) == 1:
        first_row = result.iloc[0]
        values = [
            f"**{column.replace('_', ' ').title()}:** {first_row[column]}"
            for column in result.columns
        ]
        return (
            f"Based on the IPL dataset, the answer to “{question}” is:\n\n"
            + "  \n".join(values)
        )

    return (
        f"The analysis returned **{len(result):,} results** for the question:\n\n"
        f"**{question}**\n\n"
        "The leading results are shown in the Data tab."
    )


def run_ipl_analysis(question):
    generated_sql = generate_sql(question)
    validate_sql(generated_sql)

    query_result = run_query(generated_sql)
    validate_result(query_result)

    context = build_context(question, query_result)
    context = enrich_context_with_result(context, query_result)
    validate_context(context)

    if context.get("needs_insight"):
        try:
            insight = generate_insight(question, query_result, context)
            validate_answer(insight)
            check_hallucination(insight, context)
        except Exception as error:
            print("Insight generation fallback:", error)
            insight = create_direct_answer(question, query_result)
    else:
        insight = create_direct_answer(question, query_result)

    return generated_sql, query_result, insight, context


def display_error(error):
    error_text = str(error)
    lowered = error_text.lower()

    if "429" in error_text or "resource_exhausted" in lowered or "quota" in lowered:
        st.error(
            "Gemini's request quota has been reached. "
            "Use another available model in `config.py` or retry after the quota resets."
        )
    elif "binder error" in lowered:
        st.error("The generated SQL contains a column, table, or datatype mismatch.")
    elif "conversion error" in lowered:
        st.error("The generated SQL could not convert an IPL value to the expected datatype.")
    elif "catalog error" in lowered:
        st.error("The generated SQL referenced a table or column that does not exist.")
    elif "blocked sql command" in lowered:
        st.error("The query was blocked by the SQL safety validator.")
    elif "503" in error_text or "unavailable" in lowered or "high demand" in lowered:
        st.error("Gemini is currently unavailable because of high demand.")
    else:
        st.error("The IPL question could not be processed.")

    with st.expander("View technical error", expanded=False):
        st.exception(error)


def render_supporting_outputs(result, generated_sql, context):
    with st.expander("View supporting data", expanded=False):
        st.dataframe(result, width="stretch", hide_index=True)

    with st.expander("View generated SQL", expanded=False):
        st.code(generated_sql, language="sql")

    with st.expander("View Context Builder Output", expanded=False):
        st.json(context)


def render_full_analysis(answer, result, generated_sql, context):
    answer_tab, chart_tab, data_tab, sql_tab = st.tabs(
        ["Answer", "Chart", "Data", "Generated SQL"]
    )

    with answer_tab:
        st.markdown(answer)
        if result is not None and not result.empty:
            if len(result) == 1:
                st.success("One leading result identified.")
            else:
                st.success(f"{len(result):,} ranked results identified.")

    with chart_tab:
        st.subheader("📊 Visual Analysis")

        if should_generate_chart(result):
            chart_config = get_chart_config(result)
            chart_df = prepare_chart_dataframe(result, chart_config)

            #if DEBUG_MODE:
            #    st.write("Chart config", chart_config)
            #    st.write("Columns", result.columns.tolist())
            #    st.write(result.head())

            if chart_config["type"] == "line":
                st.plotly_chart(
                    render_line_chart(chart_df),
                    use_container_width="stretch",
                )
            elif chart_config["type"] == "bar":
                st.plotly_chart(
                    render_bar_chart(chart_df),
                    use_container_width="stretch",
                )
            else:
                st.dataframe(chart_df, width="stretch")
        else:
            st.info("Not enough data available to generate a chart.")

    with data_tab:
        if result is None or result.empty:
            st.warning("No matching IPL records were found.")
        else:
            st.dataframe(result, width="stretch", hide_index=True)
            csv_data = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download results as CSV",
                data=csv_data,
                file_name="ipl_intelligence_results.csv",
                mime="text/csv",
                width="stretch",
            )

    with sql_tab:
        st.code(generated_sql, language = "sql")
        st.caption(
            "Generated by Gemini and executed through the read-only DuckDB query tool."
        )
        with st.expander("View Context Builder Output", expanded=False):
            st.json(context)


def render_incomplete_query(current_question, incomplete):
    detected_type = incomplete.get("type", "concept")
    detected_value = incomplete.get("value", current_question)

    with st.chat_message("user"):
        st.markdown(current_question)

    with st.chat_message("assistant"):
        if detected_type == "season":
            st.markdown(
                f"""
I identified **IPL season {detected_value}**, but I need to know what you want to analyze.

Try one of these:

- Who won IPL {detected_value}?
- Top run scorer in IPL {detected_value}
- Top wicket taker in IPL {detected_value}
- Team wins in IPL {detected_value}
"""
            )
        elif detected_type == "entity":
            st.markdown(
                f"""
I identified **{detected_value}**, but I need to know what you want to analyze.

Try one of these:

- {detected_value} performance by season
- {detected_value} total runs or wickets
- {detected_value} strike rate or economy
- Best season for {detected_value}
"""
            )
        else:
            st.markdown(
                f"""
I identified the IPL concept **{detected_value}**, but I need a complete analytical question.

Try one of these:

- Best players in {detected_value}
- Team performance in {detected_value}
- Batting statistics for {detected_value}
- Bowling statistics for {detected_value}
"""
            )


with st.sidebar:
    st.title("🏏 IPL Intelligence")
    st.caption("Your AI-powered analyst for the Indian Premier League.")
    st.subheader("Popular Questions")
    st.markdown(
        """
👑 Who is the greatest IPL run scorer?

🎯 Which bowler dominates the wicket charts?

⚔️ Most one-sided batter vs bowler matchups?

🔥 Who dominates the death overs?

🌍 Best overseas performers in IPL history?

🌀 Which leg spinner has taken the most wickets?

🏟️ Which venue favors chasing teams the most?

🧠 What is the Impact Player rule?

📖 Tell me about MS Dhoni

"""
)


st.markdown("<h1 style='text-align:center;'>🏏 IPL Intelligence Agent</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3 style='text-align:center;'>AI-Powered Cricket Analytics for the Indian Premier League</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;font-size:20px;color:#666;'>Ask. Analyze. Discover.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    """
<p style='text-align:center;color:#666;font-size:16px;'>
Explore IPL players, teams, venues, powerplays, death overs, chasing performance,
and match-winning trends using natural language.
</p>
""",
    unsafe_allow_html=True,
)
st.markdown(
    f"""
<div style="background-color:#e8f0fe;padding:14px;border-radius:8px;
            display:flex;justify-content:space-around;align-items:center;
            font-size:16px;font-weight:450;">
    <div style="flex:1;text-align:left;">📅 Coverage: {coverage}</div>
    <div style="flex:1;text-align:center;">🏏 Matches: {stats['matches']:,}</div>
    <div style="flex:1;text-align:right;">📊 Deliveries: {stats['deliveries']:,}</div>
</div>
""",
    unsafe_allow_html=True,
)

#####################################################################################################
################ This is the ENTRY POINT for "Ask questions" from users ##############################
#####################################################################################################

typed_question = st.chat_input("Ask anything about IPL cricket...")
selected_question = st.session_state.selected_question

#### The below if else block set the question and this question will pass to all relevant check...

if selected_question:
    current_question = selected_question
    st.session_state.selected_question = None
elif typed_question:
    current_question = typed_question
else:
    current_question = None

######### The below if else block check for....############### 
#  1. Call clean_question function for quality checks..############### 

if current_question:
    current_question = clean_question(current_question)

    if current_question:
        if is_acknowledgement(current_question):    # This function will check the words as a followup? like..Ok
            with st.chat_message("user"):
                st.markdown(current_question)
            with st.chat_message("assistant"):
                st.markdown("Glad that helped. 🏏")
            st.stop()

######################## QUESTIONS RELEVANCE CHECK ###############################
##################################################################################
        
        question_is_relevant = is_ipl_relevant(current_question)

        knowledge_document = retriever.find_document(current_question)

        knowledge_intent = detect_knowledge_intent(current_question)

        knowledge_content = None
        print("KNOWLEDGE_DOC: ", knowledge_document)

        if knowledge_document:
            knowledge_content = retriever.load_document(current_question)
        
        incomplete = detect_incomplete_ipl_query(current_question)
        entity_result = detect_entity_followup(current_question)
        metric_result = detect_metric_followup(current_question)
        time_result = detect_time_followup(current_question)
        continuation_result = detect_context_continuation(current_question)
        
#### This if block will decide the final routing to execute the analytics agent Or RAG call? #######

        if (
            knowledge_document
            and knowledge_intent
        ):
            capability_route = "knowledge"
        else:
            capability_route = "analytics"

        has_previous_context = (
            st.session_state.last_context is not None
        )

        if DEBUG_MODE:
            print("=" * 60)
            print("QUESTION:", current_question)
            print("RELEVANT:", question_is_relevant)
            print("INCOMPLETE:", incomplete)
            print("ENTITY:", entity_result)

            print("METRIC:", metric_result)
            print("TIME:", time_result)
            print("CONTINUATION:", continuation_result)
            print("STATE:", st.session_state.conversation_state)
            print("=" * 60)

        #   1. TIME FOLLOW-UP WITH PRIOR CONTEXT
        ########################################################################

        if time_result.get("is_time_followup") and has_previous_context:
            rewritten_question = build_time_question(
                time_result,
                st.session_state.conversation_state,
            )

            print("=" * 20)
            print("TIME FollowUp")
            print("TIME result", time_result)
            print("conversation state:", st.session_state.conversation_state)            
            print("REWRITTEN QUESTION:", rewritten_question)
            print("=" * 20)


            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                if not rewritten_question:
                    st.warning(
                        "I detected a time-aware follow-up, but the previous "
                        "analytical context does not support a time-filtered rewrite."
                    )
                else:
                    try:
                        if DEBUG_MODE:
                            st.write("Rewritten question:", rewritten_question)

                        generated_sql, result, insight, context = run_ipl_analysis(
                            rewritten_question
                        )
                        st.markdown("### 🏏 Answer")
                        st.markdown(insight)
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )
                        render_supporting_outputs(result, generated_sql, context)
                    except Exception as error:
                        display_error(error)

        #   2. Metric follow-up with prior context.
        ########################################################################

        elif metric_result.get("is_metric_followup") and has_previous_context:
            rewritten_question = build_metric_question(
                metric_result,
                st.session_state.conversation_state,
            )

            print("=" * 60)
            print("METRIC FOLLOW-UP")
            print("METRIC RESULT:", metric_result)
            print(
                "CONVERSATION STATE:",
                st.session_state.conversation_state,
            )
            print(
                "REWRITTEN QUESTION:",
                rewritten_question,
            )
            print("=" * 60)

            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                if not rewritten_question:
                    st.warning(
                        "I detected a metric follow-up, but the previous context "
                        "does not contain enough information to build a new question."
                    )
                else:
                    try:
                        if DEBUG_MODE:
                            st.write("Rewritten question:", rewritten_question)

                        generated_sql, result, insight, context = run_ipl_analysis(
                            rewritten_question
                        )
                        st.markdown("### 🏏 Answer")
                        st.markdown(insight)
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )
                        render_supporting_outputs(result, generated_sql, context)
                    except Exception as error:
                        display_error(error)

        #   3. Entity follow-up with prior context.
        ########################################################################

        elif entity_result.get("is_entity_followup") and has_previous_context:
            rewritten_question = build_contextual_question(
                entity_result,
                st.session_state.conversation_state,
            )

            print("=" * 20)
            print("Entity FollowUp")
            print("Entity result", entity_result)
            print(
                "conversation state:", st.session_state.conversation_state
            )
            print(
                "REWRITTEN QUESTION:", rewritten_question

            )

            print("=" * 20)

            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                if not rewritten_question:
                    st.warning(
                        "I detected an entity follow-up, but the previous context "
                        "does not contain enough information to build a comparison."
                    )
                else:
                    try:
                        if DEBUG_MODE:
                            st.write("Rewritten question:", rewritten_question)

                        generated_sql, result, insight, context = run_ipl_analysis(
                            rewritten_question
                        )
                        st.markdown("### 🏏 Answer")
                        st.markdown(insight)
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )
                        render_supporting_outputs(result, generated_sql, context)
                    except Exception as error:
                        display_error(error)

        #   4. KNOWLEDGE QUESTIONS RELATED TO IPL.
        ########################################################################

        elif (  
            capability_route == "knowledge"
            and knowledge_content

        ):
            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                try:

                    knowledge_answer = (
                        generate_knowledge_answer(
                            current_question,
                            knowledge_content
                        )
                    )

                    st.markdown(
                        knowledge_answer
                        #knowledge_content
                    )

                    if DEBUG_MODE:
                        st.caption(
                            f"Knowledge Source: "
                            f"{knowledge_document}"
                        )
                except Exception as error:
                    display_error(error)

        #   5. INCOMPLETE follow-up with prior context.
        ########################################################################

        elif incomplete.get("is_incomplete", False):
            render_incomplete_query(current_question, incomplete)

        #   6. Contextual analytics continuation.
        elif (
            continuation_result.get("is_context_continuation") 
            and has_previous_context
            and question_is_relevant
        ):
            #   Existing continuation workflow
            rewritten_question = build_context_continuation_question(
                continuation_result,
                st.session_state.conversation_state,
            )

            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                if not rewritten_question:
                    st.warning(
                        "I detected a contextual follow-up, but the previous context "
                        "is not sufficient to build a new question."
                    )
                else:
                    try:
                        if DEBUG_MODE:
                            st.write("Rewritten question:", rewritten_question)

                        generated_sql, result, insight, context = run_ipl_analysis(
                            rewritten_question
                        )
                        st.markdown("### 🏏 Answer")
                        st.markdown(insight)
                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )
                        render_supporting_outputs(result, generated_sql, context)
                    except Exception as error:
                        display_error(error)

        #   6. Follow-up requiring missing previous context.
        ########################################################################

        elif (
            question_is_relevant
            and (
            time_result.get("is_time_followup")
            or metric_result.get("is_metric_followup")
            or entity_result.get("is_entity_followup")
            or continuation_result.get("is_context_continuation")
            )
        ):
            with st.chat_message("user"):
                st.markdown(current_question)
            with st.chat_message("assistant"):
                st.warning(
                    "Please ask an IPL statistics question first. "
                    "I need previous analytical context before processing this follow-up."
                )

        #   7. WHY / HOW / EXPLAIN QUESTION
        ########################################################################
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
                        followup_answer = generate_followup_insight(
                            current_question,
                            st.session_state.last_question,
                            st.session_state.last_answer,
                            st.session_state.last_result,
                            st.session_state.last_context,
                        )
                        validate_answer(followup_answer)
                        st.markdown("### 🏏 Answer")
                        st.markdown(followup_answer)
                        st.session_state.last_answer = followup_answer

                        if st.session_state.last_result is not None:
                            with st.expander("View supporting data", expanded=False):
                                st.dataframe(
                                    st.session_state.last_result,
                                    width="stretch",
                                    hide_index=True,
                                )

                        if st.session_state.last_sql:
                            with st.expander("View generated SQL", expanded=False):
                                st.code(st.session_state.last_sql, language="sql")
                    except Exception as error:
                        display_error(error)
            else:
                st.warning(
                    "Please ask an IPL statistics question first. "
                    "I need a previous result before I can explain why."
                )

        #elif incomplete.get("is_incomplete", False):
        #    render_incomplete_query(
        #        current_question,
        #        incomplete
        #    )

        #   8. NOT RELEVANT QUESTIONS...
        ########################################################################

        elif not question_is_relevant:

            with st.chat_message("user"):
                st.markdown(current_question)
            with st.chat_message("assistant"):
                st.warning(
                    "I couldn't identify an IPL-related concept, player, team, season, "
                    "venue, match, or statistic in the question."
                )

        #   9. New QUESTIONS...
        ########################################################################

        else:
            with st.chat_message("user"):
                st.markdown(current_question)

            with st.chat_message("assistant"):
                try:
                    with st.status("Analyzing IPL data...", expanded=True) as status:
                        st.write("Understanding the cricket question")
                        st.write("Generating DuckDB SQL with Gemini")
                        st.write("Validating and executing the SQL")
                        st.write("Building analytical context")

                        generated_sql, result, insight, context = run_ipl_analysis(
                            current_question
                        )

                        if context.get("needs_insight"):
                            st.write("Generating the cricket insight")
                        else:
                            st.write("Preparing the retrieved records")

                        status.update(
                            label="IPL analysis completed",
                            state="complete",
                            expanded=False,
                        )

                    #   SAVE THE CONTEXT OR SESSION QUESTIONS...
                    save_analysis_state(
                        current_question,
                        generated_sql,
                        result,
                        insight,
                        context,
                    )

                    if DEBUG_MODE:
                        print(
                            "UPDATED STATE:",
                            st.session_state.conversation_state,
                        )

                    render_full_analysis(
                        insight,
                        result,
                        generated_sql,
                        context,
                    )
                except Exception as error:
                    display_error(error)


footer_left, footer_right = st.columns(2)
with footer_left:
    st.caption("Powered by Agentic AI • RAG • Gemini • Python • DuckDB • Streamlit ")
with footer_right:
    st.caption(" ")