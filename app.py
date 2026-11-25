from pathlib import Path
import re

import duckdb
import streamlit as st

from agent.entity_resolver import (
    detect_entity_followup,
)

from guardrails.answer_validator import (
    validate_answer,
)

from guardrails.relevance_validator import (
    is_ipl_relevant,
)

from agent.contextual_question_builder import (
    build_contextual_question,
)

from agent.metric_resolver import (
    detect_metric_followup,
)

from agent.metric_question_builder import (
    build_metric_question,
)

from agent.time_resolver import (
    detect_time_followup,
)

from agent.time_question_builder import (
    build_time_question,
)

from agent.context_continuation_resolver import (
    detect_context_continuation,
)

from agent.context_continuation_builder import (
    build_context_continuation_question,
)

from agent.insight_generator import (
    generate_followup_insight,
)

from agent.conversation_state import (
    create_conversation_state,
    update_conversation_state,
)

from agent.chart_generator import (
    should_generate_chart,
    get_chart_config,
    prepare_chart_dataframe,
)

from agent.plotly_chart_renderer import (
    render_bar_chart,
    render_line_chart,
)

from agent.incomplete_query_detector import (
    detect_incomplete_ipl_query,
)

from agent.analytics_service import (
    run_analytics_query,
)

from agent.capability_planner import (
    create_capability_plan,
)

from agent.capability_executor import (
    execute_capability_plan,
)

from agent.capability_response_composer import (
    compose_capability_response,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEBUG_MODE = False


st.set_page_config(
    page_title="IPL Intelligence Agent",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "ipl.db"
)


# ============================================================
# DATABASE STATISTICS
# ============================================================

@st.cache_data
def get_database_statistics():

    if not DATABASE_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: "
            f"{DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:

        row = connection.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM matches
                ) AS match_count,

                (
                    SELECT COUNT(*)
                    FROM deliveries
                ) AS delivery_count,

                (
                    SELECT COUNT(
                        DISTINCT YEAR(date)
                    )
                    FROM matches
                ) AS season_count,

                (
                    SELECT MIN(
                        YEAR(date)
                    )
                    FROM matches
                ) AS first_season,

                (
                    SELECT MAX(
                        YEAR(date)
                    )
                    FROM matches
                ) AS last_season
            """
        ).fetchone()

        return {
            "matches":
                row[0],

            "deliveries":
                row[1],

            "season_count":
                row[2],

            "first_season":
                row[3],

            "last_season":
                row[4],
        }

    finally:

        connection.close()


# ============================================================
# SESSION STATE
# ============================================================

SESSION_DEFAULTS = {
    "selected_question":
        None,

    "last_sql":
        None,

    "last_result":
        None,

    "last_question":
        None,

    "last_answer":
        None,

    "last_context":
        None,
}


for (
    key,
    default_value,
) in SESSION_DEFAULTS.items():

    if key not in st.session_state:

        st.session_state[
            key
        ] = default_value


if (
    "conversation_state"
    not in st.session_state
):

    st.session_state.conversation_state = (
        create_conversation_state()
    )


# ============================================================
# LOAD DATABASE METADATA
# ============================================================

try:

    stats = (
        get_database_statistics()
    )

except Exception as error:

    st.error(
        "The IPL database could not be opened. "
        "Please confirm that the required "
        "database file is available."
    )

    if DEBUG_MODE:

        st.exception(
            error
        )

    st.stop()


coverage = (
    f"{stats['first_season']}"
    f"–"
    f"{stats['last_season']}"
)


# ============================================================
# QUESTION CLEANING
# ============================================================

def clean_question(
    question,
):

    if question is None:
        return ""

    question = (
        question.strip()
    )

    question = re.sub(
        r"\s+",
        " ",
        question,
    )

    question = re.sub(
        r"[^\w\s]+$",
        "",
        question,
    )

    return question.strip()


def _normalize_short_message(
    question,
):

    return (
        question
        .strip()
        .lower()
        .replace("?", "")
        .replace(".", "")
        .replace("!", "")
        .replace(",", "")
        .replace("'", "")
        .replace(">", "")
        .replace("<", "")
    )


# ============================================================
# FOLLOW-UP HELPERS
# ============================================================

def is_followup_question(
    question: str,
):

    if not question:
        return False

    followup_keywords = {
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
        "sure",
    }

    return (
        _normalize_short_message(
            question
        )
        in followup_keywords
    )


def is_acknowledgement(
    question: str,
):

    if not question:
        return False

    acknowledgements = {
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
        "makes sense",
    }

    return (
        _normalize_short_message(
            question
        )
        in acknowledgements
    )


# ============================================================
# ANALYTICS STATE
# ============================================================

def save_analysis_state(
    question,
    generated_sql,
    result,
    insight,
    context,
):

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
            st.session_state
            .conversation_state,
            question,
            context,
        )
    )


METRIC_NORMALIZATION = {

    "strike rate":
        "strike_rate",

    "strike_rate":
        "strike_rate",

    "economy":
        "economy_rate",

    "economy rate":
        "economy_rate",

    "economy_rate":
        "economy_rate",

    "runs":
        "total_runs",

    "total runs":
        "total_runs",

    "total_runs":
        "total_runs",

    "wickets":
        "total_wickets",

    "total wickets":
        "total_wickets",

    "total_wickets":
        "total_wickets",

    "sixes":
        "sixes",

    "fours":
        "fours",
}


# ============================================================
# ANALYTICS SERVICE WRAPPER
# ============================================================

def run_ipl_analysis(
    question,
):

    analytics_result = (
        run_analytics_query(
            question
        )
    )

    return (
        analytics_result["sql"],
        analytics_result["result"],
        analytics_result["answer"],
        analytics_result["context"],
    )


# ============================================================
# ERROR HANDLING
# ============================================================

def display_error(
    error,
):

    error_text = str(
        error
    )

    lowered = (
        error_text.lower()
    )

    if (
        "429" in error_text
        or "resource_exhausted"
        in lowered
        or "quota" in lowered
    ):

        st.error(
            "Gemini's request quota has been "
            "reached. Please retry after the "
            "quota resets."
        )

    elif (
        "503" in error_text
        or "unavailable" in lowered
        or "high demand" in lowered
    ):

        st.error(
            "Gemini is currently unavailable "
            "because of high demand."
        )

    elif "binder error" in lowered:

        st.error(
            "The generated SQL contains a "
            "column, table, or datatype mismatch."
        )

    elif "conversion error" in lowered:

        st.error(
            "The generated SQL could not convert "
            "an IPL value to the expected datatype."
        )

    elif "catalog error" in lowered:

        st.error(
            "The generated SQL referenced a "
            "table or column that does not exist."
        )

    elif "blocked sql command" in lowered:

        st.error(
            "The query was blocked by the "
            "SQL safety validator."
        )

    else:

        st.error(
            "The IPL question could not "
            "be processed."
        )

    if DEBUG_MODE:

        with st.expander(
            "View technical error",
            expanded=False,
        ):

            st.exception(
                error
            )


# ============================================================
# SUPPORTING OUTPUTS
# ============================================================

def render_supporting_outputs(
    result,
    generated_sql,
    context,
):

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

    if DEBUG_MODE:

        with st.expander(
            "View Context Builder Output",
            expanded=False,
        ):

            st.json(
                context
            )


# ============================================================
# FULL ANALYTICS RENDERING
# ============================================================

def render_full_analysis(
    answer,
    result,
    generated_sql,
    context,
):

    (
        answer_tab,
        chart_tab,
        data_tab,
        sql_tab,
    ) = st.tabs(
        [
            "Answer",
            "Chart",
            "Data",
            "Generated SQL",
        ]
    )

    with answer_tab:

        st.markdown(
            answer
        )

        if (
            result is not None
            and not result.empty
        ):

            if len(result) == 1:

                st.success(
                    "One leading result "
                    "identified."
                )

            else:

                st.success(
                    f"{len(result):,} ranked "
                    f"results identified."
                )

    with chart_tab:

        st.subheader(
            "📊 Visual Analysis"
        )

        if should_generate_chart(
            result
        ):

            chart_config = (
                get_chart_config(
                    result
                )
            )

            chart_df = (
                prepare_chart_dataframe(
                    result,
                    chart_config,
                )
            )

            if (
                chart_config["type"]
                == "line"
            ):

                st.plotly_chart(
                    render_line_chart(
                        chart_df
                    ),
                    width="stretch",
                )

            elif (
                chart_config["type"]
                == "bar"
            ):

                st.plotly_chart(
                    render_bar_chart(
                        chart_df
                    ),
                    width="stretch",
                )

            else:

                st.dataframe(
                    chart_df,
                    width="stretch",
                )

        else:

            st.info(
                "Not enough data available "
                "to generate a chart."
            )

    with data_tab:

        if (
            result is None
            or result.empty
        ):

            st.warning(
                "No matching IPL records "
                "were found."
            )

        else:

            st.dataframe(
                result,
                width="stretch",
                hide_index=True,
            )

            csv_data = (
                result
                .to_csv(
                    index=False
                )
                .encode(
                    "utf-8"
                )
            )

            st.download_button(
                label=(
                    "Download results as CSV"
                ),
                data=csv_data,
                file_name=(
                    "ipl_intelligence_results.csv"
                ),
                mime="text/csv",
                width="stretch",
            )

    with sql_tab:

        st.code(
            generated_sql,
            language="sql",
        )

        st.caption(
            "Generated by Gemini and executed "
            "through the read-only DuckDB query tool."
        )

        if DEBUG_MODE:

            with st.expander(
                "View Context Builder Output",
                expanded=False,
            ):

                st.json(
                    context
                )


# ============================================================
# INCOMPLETE QUESTION
# ============================================================

def render_incomplete_query(
    current_question,
    incomplete,
):

    detected_type = (
        incomplete.get(
            "type",
            "concept",
        )
    )

    detected_value = (
        incomplete.get(
            "value",
            current_question,
        )
    )

    with st.chat_message(
        "user"
    ):

        st.markdown(
            current_question
        )

    with st.chat_message(
        "assistant"
    ):

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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🏏 IPL Intelligence"
    )

    st.caption(
        "Your AI-powered analyst for "
        "the Indian Premier League."
    )

    st.subheader(
        "Popular Questions"
    )

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


# ============================================================
# HEADER
# ============================================================

st.markdown(
    (
        "<h1 style='text-align:center;'>"
        "🏏 IPL Intelligence Agent"
        "</h1>"
    ),
    unsafe_allow_html=True,
)

st.markdown(
    (
        "<h3 style='text-align:center;'>"
        "AI-Powered Cricket Analytics for "
        "the Indian Premier League"
        "</h3>"
    ),
    unsafe_allow_html=True,
)

st.markdown(
    (
        "<p style='text-align:center;"
        "font-size:20px;color:#666;'>"
        "Ask. Analyze. Discover."
        "</p>"
    ),
    unsafe_allow_html=True,
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
        <div style="flex:1;text-align:left;">
            📅 Coverage: {coverage}
        </div>
        <div style="flex:1;text-align:center;">
            🏏 Matches: {stats['matches']:,}
        </div>
        <div style="flex:1;text-align:right;">
            📊 Deliveries: {stats['deliveries']:,}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# QUESTION ENTRY
# ============================================================

typed_question = st.chat_input(
    "Ask anything about IPL cricket..."
)

selected_question = (
    st.session_state
    .selected_question
)


if selected_question:

    current_question = (
        selected_question
    )

    st.session_state.selected_question = (
        None
    )

elif typed_question:

    current_question = (
        typed_question
    )

else:

    current_question = None


# ============================================================
# PROCESS QUESTION
# ============================================================

if current_question:

    current_question = (
        clean_question(
            current_question
        )
    )

    if current_question:

        # ----------------------------------------------------
        # ACKNOWLEDGEMENT
        # ----------------------------------------------------

        if is_acknowledgement(
            current_question
        ):

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                st.markdown(
                    "Glad that helped. 🏏"
                )

            st.stop()


        # ====================================================
        # FOLLOW-UP DETECTION
        # ====================================================

        question_is_relevant = (
            is_ipl_relevant(
                current_question
            )
        )

        incomplete = (
            detect_incomplete_ipl_query(
                current_question
            )
        )

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

        has_previous_context = (
            st.session_state
            .last_context
            is not None
        )


        if DEBUG_MODE:

            print("=" * 60)

            print(
                "QUESTION:",
                current_question,
            )

            print(
                "RELEVANT:",
                question_is_relevant,
            )

            print(
                "INCOMPLETE:",
                incomplete,
            )

            print(
                "ENTITY:",
                entity_result,
            )

            print(
                "METRIC:",
                metric_result,
            )

            print(
                "TIME:",
                time_result,
            )

            print(
                "CONTINUATION:",
                continuation_result,
            )

            print(
                "STATE:",
                st.session_state
                .conversation_state,
            )

            print("=" * 60)


        # ====================================================
        # 1. TIME FOLLOW-UP
        # ====================================================

        if (
            time_result.get(
                "is_time_followup"
            )
            and has_previous_context
        ):

            rewritten_question = (
                build_time_question(
                    time_result,
                    st.session_state
                    .conversation_state,
                )
            )

            if DEBUG_MODE:

                print(
                    "TIME REWRITE:",
                    rewritten_question,
                )

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                if not rewritten_question:

                    st.warning(
                        "I detected a time-aware "
                        "follow-up, but the previous "
                        "analytical context does not "
                        "support a time-filtered rewrite."
                    )

                else:

                    try:

                        (
                            generated_sql,
                            result,
                            insight,
                            context,
                        ) = run_ipl_analysis(
                            rewritten_question
                        )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            insight
                        )

                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )

                        render_supporting_outputs(
                            result,
                            generated_sql,
                            context,
                        )

                    except Exception as error:

                        display_error(
                            error
                        )


        # ====================================================
        # 2. METRIC FOLLOW-UP
        # ====================================================

        elif (
            metric_result.get(
                "is_metric_followup"
            )
            and has_previous_context
        ):

            rewritten_question = (
                build_metric_question(
                    metric_result,
                    st.session_state
                    .conversation_state,
                )
            )

            if DEBUG_MODE:

                print("=" * 60)
                print("METRIC FOLLOW-UP")
                print(
                    "METRIC RESULT:",
                    metric_result,
                )
                print(
                    "REWRITTEN QUESTION:",
                    rewritten_question,
                )
                print("=" * 60)

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                if not rewritten_question:

                    st.warning(
                        "I detected a metric follow-up, "
                        "but the previous context does not "
                        "contain enough information."
                    )

                else:

                    try:

                        (
                            generated_sql,
                            result,
                            insight,
                            context,
                        ) = run_ipl_analysis(
                            rewritten_question
                        )

                        previous_state = (
                            st.session_state
                            .conversation_state
                        )

                        detected_metric = (
                            metric_result.get(
                                "metric"
                            )
                        )

                        normalized_metric = None

                        if detected_metric:

                            normalized_metric = (
                                METRIC_NORMALIZATION.get(
                                    detected_metric,
                                    detected_metric,
                                )
                            )

                        if not context.get(
                            "player"
                        ):

                            context["player"] = (
                                previous_state.get(
                                    "player"
                                )
                            )

                        if normalized_metric:

                            context["metric"] = (
                                normalized_metric
                            )

                        if not context.get(
                            "primary_entity"
                        ):

                            context[
                                "primary_entity"
                            ] = (
                                context.get(
                                    "player"
                                )
                                or previous_state.get(
                                    "primary_entity"
                                )
                            )

                        context["intent"] = (
                            "metric_lookup"
                        )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            insight
                        )

                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )

                        render_supporting_outputs(
                            result,
                            generated_sql,
                            context,
                        )

                    except Exception as error:

                        display_error(
                            error
                        )


        # ====================================================
        # 3. ENTITY FOLLOW-UP
        # ====================================================

        elif (
            entity_result.get(
                "is_entity_followup"
            )
            and has_previous_context
        ):

            rewritten_question = (
                build_contextual_question(
                    entity_result,
                    st.session_state
                    .conversation_state,
                )
            )

            if DEBUG_MODE:

                print("=" * 60)
                print("ENTITY FOLLOW-UP")
                print(
                    "ENTITY:",
                    entity_result,
                )
                print(
                    "REWRITTEN:",
                    rewritten_question,
                )
                print("=" * 60)

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                if not rewritten_question:

                    st.warning(
                        "I detected an entity follow-up, "
                        "but the previous context does not "
                        "contain enough information."
                    )

                else:

                    try:

                        (
                            generated_sql,
                            result,
                            insight,
                            context,
                        ) = run_ipl_analysis(
                            rewritten_question
                        )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            insight
                        )

                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )

                        render_supporting_outputs(
                            result,
                            generated_sql,
                            context,
                        )

                    except Exception as error:

                        display_error(
                            error
                        )


        # ====================================================
        # 4. CONTEXT CONTINUATION
        # ====================================================

        elif (
            continuation_result.get(
                "is_context_continuation"
            )
            and has_previous_context
            and question_is_relevant
        ):

            rewritten_question = (
                build_context_continuation_question(
                    continuation_result,
                    st.session_state
                    .conversation_state,
                )
            )

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                if not rewritten_question:

                    st.warning(
                        "I detected a contextual "
                        "follow-up, but the previous "
                        "context is not sufficient."
                    )

                else:

                    try:

                        (
                            generated_sql,
                            result,
                            insight,
                            context,
                        ) = run_ipl_analysis(
                            rewritten_question
                        )

                        previous_state = (
                            st.session_state
                            .conversation_state
                        )

                        if not context.get(
                            "player"
                        ):

                            context["player"] = (
                                previous_state.get(
                                    "player"
                                )
                            )

                        if not context.get(
                            "metric"
                        ):

                            context["metric"] = (
                                previous_state.get(
                                    "metric"
                                )
                            )

                        if not context.get(
                            "intent"
                        ):

                            context["intent"] = (
                                previous_state.get(
                                    "intent"
                                )
                            )

                        if not context.get(
                            "primary_entity"
                        ):

                            context[
                                "primary_entity"
                            ] = (
                                context.get(
                                    "player"
                                )
                                or previous_state.get(
                                    "player"
                                )
                                or previous_state.get(
                                    "primary_entity"
                                )
                            )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            insight
                        )

                        save_analysis_state(
                            rewritten_question,
                            generated_sql,
                            result,
                            insight,
                            context,
                        )

                        render_supporting_outputs(
                            result,
                            generated_sql,
                            context,
                        )

                    except Exception as error:

                        display_error(
                            error
                        )


        # ====================================================
        # 5. FOLLOW-UP WITHOUT PREVIOUS CONTEXT
        # ====================================================

        elif (
            question_is_relevant
            and (
                time_result.get(
                    "is_time_followup"
                )
                or metric_result.get(
                    "is_metric_followup"
                )
                or entity_result.get(
                    "is_entity_followup"
                )
                or continuation_result.get(
                    "is_context_continuation"
                )
            )
        ):

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                st.warning(
                    "Please ask an IPL statistics "
                    "question first. I need previous "
                    "analytical context before "
                    "processing this follow-up."
                )


        # ====================================================
        # 6. WHY / HOW / EXPLAIN FOLLOW-UP
        # ====================================================

        elif is_followup_question(
            current_question
        ):

            if (
                st.session_state.last_question
                and st.session_state.last_answer
                and (
                    st.session_state.last_result
                    is not None
                )
                and (
                    st.session_state.last_context
                    is not None
                )
            ):

                with st.chat_message(
                    "user"
                ):

                    st.markdown(
                        current_question
                    )

                with st.chat_message(
                    "assistant"
                ):

                    try:

                        followup_answer = (
                            generate_followup_insight(
                                current_question,
                                st.session_state
                                .last_question,
                                st.session_state
                                .last_answer,
                                st.session_state
                                .last_result,
                                st.session_state
                                .last_context,
                            )
                        )

                        validate_answer(
                            followup_answer
                        )

                        st.markdown(
                            "### 🏏 Answer"
                        )

                        st.markdown(
                            followup_answer
                        )

                        st.session_state.last_answer = (
                            followup_answer
                        )

                    except Exception as error:

                        display_error(
                            error
                        )

            else:

                with st.chat_message(
                    "user"
                ):

                    st.markdown(
                        current_question
                    )

                with st.chat_message(
                    "assistant"
                ):

                    st.warning(
                        "Please ask an IPL statistics "
                        "question first. I need a "
                        "previous result before I can "
                        "explain why."
                    )


        # ====================================================
        # 7. INCOMPLETE QUESTION
        # ====================================================

        elif incomplete.get(
            "is_incomplete",
            False,
        ):

            render_incomplete_query(
                current_question,
                incomplete,
            )


        # ====================================================
        # 8. FRESH REQUEST
        #
        # Planner -> Executor -> Composer
        # ====================================================

        else:

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    current_question
                )

            with st.chat_message(
                "assistant"
            ):

                try:

                    with st.status(
                        (
                            "Processing your "
                            "IPL request..."
                        ),
                        expanded=True,
                    ) as status:

                        # -------------------------------
                        # PLAN
                        # -------------------------------

                        st.write(
                            "Identifying the "
                            "required capabilities"
                        )

                        plan = (
                            create_capability_plan(
                                question=(
                                    current_question
                                ),
                                conversation_context=(
                                    st.session_state
                                    .conversation_state
                                ),
                            )
                        )

                        if DEBUG_MODE:

                            print("=" * 80)
                            print(
                                "CAPABILITY PLAN"
                            )
                            print(
                                plan.model_dump()
                            )
                            print("=" * 80)

                        # -------------------------------
                        # EXECUTE
                        # -------------------------------

                        st.write(
                            "Executing the "
                            "capability plan"
                        )

                        execution = (
                            execute_capability_plan(
                                plan
                            )
                        )

                        if DEBUG_MODE:

                            print("=" * 80)
                            print(
                                "EXECUTION"
                            )
                            print(
                                execution.get(
                                    "status"
                                )
                            )
                            print("=" * 80)

                        # -------------------------------
                        # COMPOSE
                        # -------------------------------

                        st.write(
                            "Preparing the "
                            "grounded response"
                        )

                        response = (
                            compose_capability_response(
                                plan,
                                execution,
                            )
                        )

                        status.update(
                            label=(
                                "Request completed"
                            ),
                            state="complete",
                            expanded=False,
                        )


                    # ====================================
                    # RESPONSE STATUS
                    # ====================================

                    response_status = (
                        response.get(
                            "status"
                        )
                    )

                    if (
                        response_status
                        == "unsupported"
                    ):

                        st.warning(
                            response["answer"]
                        )

                    elif (
                        response_status
                        == "partial_success"
                    ):

                        st.warning(
                            "Part of the request "
                            "was completed, but one "
                            "or more capability tasks "
                            "were unsuccessful."
                        )

                        st.markdown(
                            response["answer"]
                        )

                    elif response_status in {
                        "failed",
                        "no_match",
                    }:

                        st.warning(
                            response["answer"]
                        )

                    else:

                        st.markdown(
                            response["answer"]
                        )


                    # ====================================
                    # ANALYTICS ARTIFACTS
                    # ====================================

                    analytics_artifacts = (
                        response.get(
                            "analytics_artifacts",
                            [],
                        )
                    )


                    # ------------------------------------
                    # SAVE ACTIVE ANALYTICS CONTEXT
                    # ------------------------------------

                    if analytics_artifacts:

                        primary_artifact = (
                            analytics_artifacts[
                                -1
                            ]
                        )

                        result = (
                            primary_artifact.get(
                                "result"
                            )
                        )

                        generated_sql = (
                            primary_artifact.get(
                                "sql"
                            )
                        )

                        context = (
                            primary_artifact.get(
                                "context"
                            )
                        )

                        artifact_question = (
                            primary_artifact.get(
                                "question"
                            )
                            or current_question
                        )

                        if (
                            result is not None
                            and generated_sql
                            and context
                        ):

                            save_analysis_state(
                                artifact_question,
                                generated_sql,
                                result,
                                response["answer"],
                                context,
                            )


                    # ------------------------------------
                    # RENDER ANALYTICS ARTIFACTS
                    # ------------------------------------

                    for (
                        index,
                        artifact,
                    ) in enumerate(
                        analytics_artifacts,
                        start=1,
                    ):

                        result = (
                            artifact.get(
                                "result"
                            )
                        )

                        generated_sql = (
                            artifact.get(
                                "sql"
                            )
                        )

                        context = (
                            artifact.get(
                                "context"
                            )
                        )

                        artifact_question = (
                            artifact.get(
                                "question"
                            )
                            or current_question
                        )

                        title_suffix = (
                            f" {index}"
                            if len(
                                analytics_artifacts
                            ) > 1
                            else ""
                        )

                        if result is not None:

                            with st.expander(
                                (
                                    "View supporting "
                                    f"data{title_suffix}"
                                ),
                                expanded=False,
                            ):

                                st.caption(
                                    artifact_question
                                )

                                st.dataframe(
                                    result,
                                    width="stretch",
                                    hide_index=True,
                                )

                                if not result.empty:

                                    csv_data = (
                                        result
                                        .to_csv(
                                            index=False
                                        )
                                        .encode(
                                            "utf-8"
                                        )
                                    )

                                    st.download_button(
                                        label=(
                                            "Download results "
                                            "as CSV"
                                            f"{title_suffix}"
                                        ),
                                        data=csv_data,
                                        file_name=(
                                            "ipl_hybrid_"
                                            f"result_{index}"
                                            ".csv"
                                        ),
                                        mime="text/csv",
                                        key=(
                                            "hybrid_csv_"
                                            f"{index}"
                                        ),
                                        width="stretch",
                                    )

                        if generated_sql:

                            with st.expander(
                                (
                                    "View generated "
                                    f"SQL{title_suffix}"
                                ),
                                expanded=False,
                            ):

                                st.code(
                                    generated_sql,
                                    language="sql",
                                )

                        if (
                            context
                            and DEBUG_MODE
                        ):

                            with st.expander(
                                (
                                    "View analytical "
                                    f"context"
                                    f"{title_suffix}"
                                ),
                                expanded=False,
                            ):

                                st.json(
                                    context
                                )

                except Exception as error:

                    display_error(
                        error
                    )


# ============================================================
# FOOTER
# ============================================================

footer_left, footer_right = (
    st.columns(2)
)

with footer_left:

    st.caption(
        "Powered by Agentic AI • RAG • "
        "Gemini • Python • DuckDB • Streamlit"
    )

with footer_right:

    st.caption(
        " "
    )