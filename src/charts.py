"""Plotly chart builders."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


DARK_TEMPLATE = "plotly_dark"
COLORS = px.colors.qualitative.Set2


def top_games_chart(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("hours", ascending=True)
    fig = px.bar(df, x="hours", y="name", orientation="h",
                 text="hours", color_discrete_sequence=["#1b9e77"],
                 template=DARK_TEMPLATE)
    fig.update_traces(textposition="outside", texttemplate="%{text:.0f}h")
    fig.update_layout(
        title="", xaxis_title="Hours", yaxis_title="",
        height=400, margin=dict(l=0, r=40, t=10, b=30),
        yaxis=dict(tickfont=dict(size=13)),
    )
    return fig


def playtime_histogram(df: pd.DataFrame) -> go.Figure:
    played = df[df["hours"] > 0].copy()
    fig = px.histogram(played, x="hours", nbins=50,
                       color_discrete_sequence=["#d95f02"],
                       template=DARK_TEMPLATE)
    fig.update_layout(
        title="", xaxis_title="Hours Played", yaxis_title="Number of Games",
        height=350, margin=dict(l=0, r=20, t=10, b=30),
    )
    return fig


def genre_treemap(genre_df: pd.DataFrame) -> go.Figure:
    if genre_df.empty:
        return go.Figure()
    counts = genre_df.groupby("genre").size().reset_index(name="count")
    counts = counts.sort_values("count", ascending=False).head(15)
    fig = px.treemap(counts, path=["genre"], values="count",
                     color="count", color_continuous_scale="Tealgrn",
                     template=DARK_TEMPLATE)
    fig.update_layout(
        title="", height=450, margin=dict(l=0, r=0, t=10, b=10),
        coloraxis_showscale=False,
    )
    return fig


def cost_per_hour_chart(df: pd.DataFrame, best: bool = True, n: int = 10) -> go.Figure:
    if best:
        subset = df.head(n).sort_values("cost_per_hour", ascending=False)
        color = "#1b9e77"
        title_suffix = "Best Value"
    else:
        subset = df.tail(n).sort_values("cost_per_hour", ascending=True)
        color = "#e7298a"
        title_suffix = "Worst Value"

    fig = px.bar(subset, x="cost_per_hour", y="name", orientation="h",
                 text="cost_per_hour", color_discrete_sequence=[color],
                 template=DARK_TEMPLATE)
    fig.update_traces(textposition="outside", texttemplate="$%{text:.2f}/h")
    fig.update_layout(
        title="", xaxis_title="Cost Per Hour ($)", yaxis_title="",
        height=350, margin=dict(l=0, r=60, t=10, b=30),
    )
    return fig


def recent_games_chart(games: list[dict]) -> go.Figure:
    if not games:
        return go.Figure()
    df = pd.DataFrame(games)
    df["hours"] = (df["playtime_2weeks"] / 60).round(1)
    df = df.sort_values("hours", ascending=True)
    fig = px.bar(df, x="hours", y="name", orientation="h",
                 text="hours", color_discrete_sequence=["#7570b3"],
                 template=DARK_TEMPLATE)
    fig.update_traces(textposition="outside", texttemplate="%{text:.1f}h")
    fig.update_layout(
        title="", xaxis_title="Hours (Last 2 Weeks)", yaxis_title="",
        height=max(200, len(df) * 40), margin=dict(l=0, r=40, t=10, b=30),
    )
    return fig


def platform_pie_chart(platforms: dict[str, float]) -> go.Figure:
    labels = list(platforms.keys())
    values = list(platforms.values())
    colors = {"Windows": "#00a4ef", "Mac": "#a2aaad", "Linux": "#f5a623", "Steam Deck": "#1a9fff"}
    color_list = [colors.get(l, "#888") for l in labels]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values,
        hole=0.4, marker=dict(colors=color_list),
        textinfo="label+percent", textfont_size=13,
    )])
    fig.update_layout(
        title="", template=DARK_TEMPLATE,
        height=350, margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
    )
    return fig
