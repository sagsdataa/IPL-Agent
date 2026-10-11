# agent/chart_generator.py

"""
Chart Generator
"""

import pandas as pd

# --------------------------------------------------
# Core Validation
# --------------------------------------------------

def should_generate_chart(df):

    if df is None:
        return False

    if df.empty:
        return False

    if len(df) < 2:
        return False

    return True


# --------------------------------------------------
# Data Cleaning
# --------------------------------------------------

def clean_dataframe(df):

    if df is None:
        return df

    df = df.copy()

    # Remove duplicate columns if any
    df = df.loc[:, ~df.columns.duplicated()]

    return df


# --------------------------------------------------
# Time Detection
# --------------------------------------------------

def detect_time_column(df):

    df = clean_dataframe(df)

    time_keywords = {
        "season",
        "year",
        "date",
        "month",
        "day"
    }

    for col in df.columns:

        col_lower = str(col).lower()

        if any(
            keyword in col_lower
            for keyword in time_keywords
        ):
            return col

    return None


# --------------------------------------------------
# Metric Detection
# --------------------------------------------------

def detect_metric_column(df):

    df = clean_dataframe(df)

    preferred_metrics = {
        "runs",
        "wickets",
        "strike_rate",
        "economy",
        "average",
        "matches",
        "wins",
        "total_runs",
        "total_wickets",
        "batting_average",
        "bowling_average"
    }

    # First preference:
    # explicitly named IPL metrics

    for col in df.columns:

        if (
            str(col).lower()
            in preferred_metrics
        ):
            return col

    # Second preference:
    # last numeric column

    numeric_columns = []

    for col in df.columns:

        try:

            if pd.api.types.is_numeric_dtype(
                df[col]
            ):
                numeric_columns.append(col)

        except Exception:
            pass

    if not numeric_columns:
        return None

    return numeric_columns[-1]


# --------------------------------------------------
# Entity Detection
# --------------------------------------------------

def detect_entity_column(df):

    df = clean_dataframe(df)

    metric_col = detect_metric_column(df)

    for col in df.columns:

        if col != metric_col:
            return col

    return None


# --------------------------------------------------
# Trend Dataset Detection
# --------------------------------------------------

def is_trend_dataset(df):

    time_col = detect_time_column(df)

    metric_col = detect_metric_column(df)

    return (
        time_col is not None
        and metric_col is not None
        and time_col != metric_col
    )


# --------------------------------------------------
# Ranking Dataset Detection
# --------------------------------------------------

def is_ranking_dataset(df):

    metric_col = detect_metric_column(df)

    entity_col = detect_entity_column(df)

    return (
        metric_col is not None
        and entity_col is not None
    )


# --------------------------------------------------
# Determine Chart Type
# --------------------------------------------------

def get_chart_type(df):

    if is_trend_dataset(df):
        return "line"

    if is_ranking_dataset(df):
        return "bar"

    return "table"


# --------------------------------------------------
# Chart Configuration
# --------------------------------------------------

def get_chart_config(df):

    df = clean_dataframe(df)

    chart_type = get_chart_type(df)

    if chart_type == "line":

        return {
            "type": "line",
            "x": detect_time_column(df),
            "y": detect_metric_column(df)
        }

    if chart_type == "bar":

        return {
            "type": "bar",
            "x": detect_entity_column(df),
            "y": detect_metric_column(df)
        }

    return {
        "type": "table"
    }


# --------------------------------------------------
# Prepare Chart Data
# --------------------------------------------------

def prepare_chart_dataframe(df, chart_config):

    df = clean_dataframe(df)

    chart_type = chart_config["type"]

    if chart_type == "line":

        x_col = chart_config["x"]
        y_col = chart_config["y"]

        if x_col == y_col:

            raise ValueError(
                f"Invalid chart config. "
                f"x and y are both '{x_col}'."
            )

        chart_df = (
            df[[x_col, y_col]]
            .sort_values(by=x_col)
            .set_index(x_col)
        )

        return chart_df

    if chart_type == "bar":

        x_col = chart_config["x"]
        y_col = chart_config["y"]

        if x_col == y_col:

            raise ValueError(
                f"Invalid chart config. "
                f"x and y are both '{x_col}'."
            )

        chart_df = (
            df[[x_col, y_col]]
            .head(10)
            .set_index(x_col)
        )

        return chart_df

    return df