import plotly.express as px


def render_bar_chart(chart_df):

    x_col = chart_df.index.name
    y_col = chart_df.columns[0]

    fig = px.bar(
        chart_df.reset_index(),
        x=x_col,
        y=y_col,
        text=y_col,
        title=y_col.replace("_", " ").title()
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        template="plotly_dark"
    )

    return fig


def render_line_chart(chart_df):

    x_col = chart_df.index.name
    y_col = chart_df.columns[0]

    fig = px.line(
        chart_df.reset_index(),
        x=x_col,
        y=y_col,
        markers=True,
        title=y_col.replace("_", " ").title()
    )

    fig.update_layout(
        height=500,
        template="plotly_dark"
    )

    return fig
