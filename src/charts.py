"""Plotly chart builders."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.analytics import game_meme


DARK_TEMPLATE = "plotly_dark"
COLORS = px.colors.qualitative.Set2


def top_games_chart(df: pd.DataFrame, memes: dict[str, str] | None = None) -> go.Figure:
    df = df.sort_values("hours", ascending=True).copy()
    # Build meme text for hover
    if memes is None:
        from src.analytics import GAME_MEMES
        memes = GAME_MEMES
    df["meme"] = df["name"].map(lambda n: memes.get(n, ""))
    df["hover_text"] = df.apply(
        lambda r: f"Game: {r['name']}<br>Playtime: {r['hours']:,.0f}h" + (f"<br>{r['meme']}" if r['meme'] else ""),
        axis=1,
    )
    fig = px.bar(df, x="hours", y="name", orientation="h",
                 text="hours", color_discrete_sequence=["#1b9e77"],
                 template=DARK_TEMPLATE, custom_data=["hover_text"])
    fig.update_traces(
        textposition="outside", texttemplate="%{text:.0f}h",
        hovertemplate="%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        title="", xaxis_title="Hours", yaxis_title="",
        height=400, margin=dict(l=0, r=40, t=10, b=30),
        yaxis=dict(tickfont=dict(size=13)),
        hovermode="closest",
    )
    return fig


def playtime_histogram(df: pd.DataFrame) -> go.Figure:
    played = df[df["hours"] > 0].copy()
    fig = px.histogram(played, x="hours", nbins=50,
                       color_discrete_sequence=["#d95f02"],
                       template=DARK_TEMPLATE)
    fig.update_traces(
        hovertemplate="Hours played: %{x:.0f}<br>Games: %{y}<extra></extra>",
    )
    fig.update_layout(
        title="", xaxis_title="Hours Played", yaxis_title="Number of Games",
        height=350, margin=dict(l=0, r=20, t=10, b=30),
        hovermode="closest",
    )
    return fig


def genre_treemap(genre_df: pd.DataFrame, top_games_map: dict[str, list[str]] | None = None) -> go.Figure:
    if genre_df.empty:
        return go.Figure()
    counts = genre_df.groupby("genre").size().reset_index(name="count")
    counts = counts.sort_values("count", ascending=False).head(15)

    if top_games_map:
        counts["top_games"] = counts["genre"].map(
            lambda g: ", ".join(top_games_map.get(g, []))
        )
    else:
        counts["top_games"] = ""

    counts["hover_text"] = counts.apply(
        lambda r: f"Genre: {r['genre']}<br>Games: {r['count']}" + (f"<br>Top: {r['top_games']}" if r['top_games'] else ""),
        axis=1,
    )

    fig = px.treemap(counts, path=["genre"], values="count",
                     color="count", color_continuous_scale="Tealgrn",
                     template=DARK_TEMPLATE, custom_data=["hover_text"])
    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        title="", height=450, margin=dict(l=0, r=0, t=10, b=10),
        coloraxis_showscale=False,
    )
    return fig


def cost_per_hour_chart(df: pd.DataFrame, best: bool = True, n: int = 10) -> go.Figure:
    if best:
        subset = df.head(n).sort_values("cost_per_hour", ascending=False).copy()
        color = "#1b9e77"
    else:
        subset = df.tail(n).sort_values("cost_per_hour", ascending=True).copy()
        color = "#e7298a"

    subset["hover_text"] = subset.apply(
        lambda r: f"Game: {r['name']}<br>Price: ${r['price']:.2f}<br>Playtime: {r['hours']:,.1f}h<br>Cost/Hour: ${r['cost_per_hour']:.2f}",
        axis=1,
    )

    fig = px.bar(subset, x="cost_per_hour", y="name", orientation="h",
                 text="cost_per_hour", color_discrete_sequence=[color],
                 template=DARK_TEMPLATE, custom_data=["hover_text"])
    fig.update_traces(
        textposition="outside", texttemplate="$%{text:.2f}/h",
        hovertemplate="%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        title="", xaxis_title="Cost Per Hour ($)", yaxis_title="",
        height=350, margin=dict(l=0, r=60, t=10, b=30),
        hovermode="closest",
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
    fig.update_traces(
        textposition="outside", texttemplate="%{text:.1f}h",
        hovertemplate="Game: %{y}<br>Last 2 weeks: %{x:.1f}h<extra></extra>",
    )
    fig.update_layout(
        title="", xaxis_title="Hours (Last 2 Weeks)", yaxis_title="",
        height=max(200, len(df) * 40), margin=dict(l=0, r=40, t=10, b=30),
        hovermode="closest",
    )
    return fig


# --- Comparison Charts ---

def shared_games_chart(shared_df: pd.DataFrame, name1: str, name2: str, n: int = 20) -> go.Figure:
    """Horizontal bar chart comparing hours for shared games."""
    df = shared_df.head(n).sort_values("hours_p1", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df["name"], x=df["hours_p1"], name=name1,
                         orientation="h", marker_color="#1b9e77", text=df["hours_p1"],
                         textposition="outside", texttemplate="%{text:.0f}h",
                         hovertemplate="%{y}<br>" + name1 + ": %{x:.0f}h<extra></extra>"))
    fig.add_trace(go.Bar(y=df["name"], x=df["hours_p2"], name=name2,
                         orientation="h", marker_color="#d95f02", text=df["hours_p2"],
                         textposition="outside", texttemplate="%{text:.0f}h",
                         hovertemplate="%{y}<br>" + name2 + ": %{x:.0f}h<extra></extra>"))
    fig.update_layout(barmode="group", template=DARK_TEMPLATE,
                      xaxis_title="Hours", yaxis_title="",
                      height=max(400, len(df) * 35), margin=dict(l=0, r=60, t=10, b=30),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      hovermode="closest")
    return fig


def stats_comparison_chart(stats1: dict, stats2: dict, name1: str, name2: str) -> go.Figure:
    """Grouped bar chart comparing key metrics."""
    metrics = ["Total Games", "Played", "Unplayed", "Total Hours"]
    vals1 = [stats1["total_games"], stats1["played"], stats1["unplayed"], stats1["total_hours"]]
    vals2 = [stats2["total_games"], stats2["played"], stats2["unplayed"], stats2["total_hours"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(name=name1, x=metrics, y=vals1, marker_color="#1b9e77",
                         hovertemplate=name1 + "<br>%{x}: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(name=name2, x=metrics, y=vals2, marker_color="#d95f02",
                         hovertemplate=name2 + "<br>%{x}: %{y:,.0f}<extra></extra>"))
    fig.update_layout(barmode="group", template=DARK_TEMPLATE,
                      height=350, margin=dict(l=0, r=20, t=10, b=30),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      hovermode="closest")
    return fig


def top_games_comparison_chart(df1: pd.DataFrame, df2: pd.DataFrame, name1: str, name2: str, n: int = 10) -> go.Figure:
    """Overlapping horizontal bar chart of both players' top games."""
    top1 = df1.head(n)[["name", "hours"]].copy()
    top2 = df2.head(n)[["name", "hours"]].copy()
    all_names = list(dict.fromkeys(list(top1["name"]) + list(top2["name"])))[:15]
    hours1 = {r["name"]: r["hours"] for _, r in top1.iterrows()}
    hours2 = {r["name"]: r["hours"] for _, r in top2.iterrows()}
    names = sorted(all_names, key=lambda n: max(hours1.get(n, 0), hours2.get(n, 0)))
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=[hours1.get(n, 0) for n in names], name=name1,
                         orientation="h", marker_color="#1b9e77",
                         hovertemplate="%{y}<br>" + name1 + ": %{x:,.0f}h<extra></extra>"))
    fig.add_trace(go.Bar(y=names, x=[hours2.get(n, 0) for n in names], name=name2,
                         orientation="h", marker_color="#d95f02",
                         hovertemplate="%{y}<br>" + name2 + ": %{x:,.0f}h<extra></extra>"))
    fig.update_layout(barmode="group", template=DARK_TEMPLATE,
                      xaxis_title="Hours", yaxis_title="",
                      height=max(400, len(names) * 35), margin=dict(l=0, r=40, t=10, b=30),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      hovermode="closest")
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
        hovertemplate="Platform: %{label}<br>Hours: %{value:,.0f}h<br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        title="", template=DARK_TEMPLATE,
        height=350, margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
    )
    return fig


def expensive_unplayed_chart(data: list[tuple[str, float]]) -> go.Figure:
    """Horizontal bar chart of top most expensive unplayed games."""
    if not data:
        return go.Figure()
    df = pd.DataFrame(data, columns=["name", "price"])
    df = df.sort_values("price", ascending=True)
    fig = px.bar(df, x="price", y="name", orientation="h",
                 text="price", color_discrete_sequence=["#e7298a"],
                 template=DARK_TEMPLATE)
    fig.update_traces(
        textposition="outside", texttemplate="$%{text:.2f}",
        hovertemplate="Game: %{y}<br>Price: $%{x:.2f}<br>Status: Unplayed 💀<extra></extra>",
    )
    fig.update_layout(
        title="", xaxis_title="Price ($)", yaxis_title="",
        height=max(300, len(df) * 35), margin=dict(l=0, r=60, t=10, b=30),
        hovermode="closest",
    )
    return fig


# --- Feature 6: Game Timeline Chart ---

def game_timeline_chart(timeline_df: pd.DataFrame) -> go.Figure:
    """Horizontal scatter plot showing when games were last played."""
    if timeline_df.empty:
        return go.Figure()

    df = timeline_df.copy()
    df["last_played_date"] = pd.to_datetime(df["last_played_date"])
    df["date_label"] = df["last_played_date"].dt.strftime("%B %d, %Y")
    df["size"] = df["hours"].clip(lower=1)  # min size for visibility

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["last_played_date"],
        y=df["name"],
        mode="markers",
        marker=dict(
            size=df["size"].apply(lambda h: min(max(h * 0.5, 8), 40)),
            color=df["hours"],
            colorscale="Tealgrn",
            showscale=True,
            colorbar=dict(title="Hours"),
        ),
        customdata=df[["date_label", "hours"]].values,
        hovertemplate="Game: %{y}<br>Last played: %{customdata[0]}<br>Total hours: %{customdata[1]:,.1f}h<extra></extra>",
    ))
    fig.update_layout(
        template=DARK_TEMPLATE,
        xaxis_title="Last Played",
        yaxis_title="",
        height=max(400, len(df) * 30),
        margin=dict(l=0, r=20, t=10, b=30),
        hovermode="closest",
        yaxis=dict(tickfont=dict(size=12)),
    )
    return fig
