"""Plotly chart builders."""

from __future__ import annotations

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
    # Sort by total hours so both players' contributions are visible
    df = shared_df.copy().head(n)
    df["total"] = df["hours_p1"].fillna(0) + df["hours_p2"].fillna(0)
    df = df.sort_values("total", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["name"], x=df["hours_p1"].fillna(0), name=name1,
        orientation="h", marker_color="#1b9e77",
        hovertemplate="%{y}<br>" + name1 + ": %{x:.0f}h<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df["name"], x=df["hours_p2"].fillna(0), name=name2,
        orientation="h", marker_color="#d95f02",
        hovertemplate="%{y}<br>" + name2 + ": %{x:.0f}h<extra></extra>",
    ))
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

def summary_card_figure(
    persona_name: str,
    title: str,
    emoji: str,
    description: str,
    stats: dict,
    account_years: int,
    top3: list[tuple[str, float]],
    genre_tags: list[str] | None = None,
    avatar_url: str = "",
) -> go.Figure:
    """Build the summary card as a Plotly figure for PNG download."""
    fig = go.Figure()
    fig.update_xaxes(visible=False, range=[0, 500])
    fig.update_yaxes(visible=False, range=[0, 600])

    # Background
    fig.add_shape(type="rect", x0=0, y0=0, x1=500, y1=600,
                  fillcolor="#1a1a2e", line=dict(width=0))
    fig.add_shape(type="rect", x0=0, y0=0, x1=500, y1=300,
                  fillcolor="#16213e", line=dict(width=0))

    # Avatar
    if avatar_url:
        fig.add_layout_image(dict(
            source=avatar_url, x=30, y=565, xref="x", yref="y",
            sizex=56, sizey=56, xanchor="left", yanchor="top",
            layer="above",
        ))

    # Player name and personality
    fig.add_annotation(x=100, y=555, text=f"<b>{persona_name}</b>",
                       font=dict(size=20, color="white"), showarrow=False, xanchor="left", yanchor="top")
    fig.add_annotation(x=100, y=530, text=f"{emoji} {title}",
                       font=dict(size=14, color="#aaaaaa"), showarrow=False, xanchor="left", yanchor="top")
    fig.add_annotation(x=250, y=490, text=description,
                       font=dict(size=12, color="#888888"), showarrow=False, xanchor="center", yanchor="top",
                       width=440)

    # Stats row
    stat_items = [
        (f"{stats['total_games']:,}", "Games"),
        (f"{stats['total_hours']:,.0f}", "Hours"),
        (f"{stats['pct_played']}%", "Played"),
        (f"{account_years}y", "Account"),
    ]
    for i, (val, label) in enumerate(stat_items):
        cx = 65 + i * 120
        fig.add_annotation(x=cx, y=440, text=f"<b>{val}</b>",
                           font=dict(size=18, color="white"), showarrow=False, xanchor="center")
        fig.add_annotation(x=cx, y=418, text=label,
                           font=dict(size=11, color="#888888"), showarrow=False, xanchor="center")

    # Top 3 games
    fig.add_annotation(x=30, y=385, text="🏆 TOP GAMES",
                       font=dict(size=12, color="#888888"), showarrow=False, xanchor="left")
    for i, (name, hours) in enumerate(top3[:3]):
        y = 360 - i * 25
        fig.add_annotation(x=30, y=y, text=name,
                           font=dict(size=14, color="white"), showarrow=False, xanchor="left")
        fig.add_annotation(x=470, y=y, text=f"{hours:,.0f}h",
                           font=dict(size=14, color="#1b9e77"), showarrow=False, xanchor="right")

    # Genre tags
    if genre_tags:
        tag_text = " · ".join(genre_tags[:5])
        fig.add_annotation(x=250, y=270, text=tag_text,
                           font=dict(size=12, color="#1b9e77"), showarrow=False, xanchor="center")

    # Watermark
    fig.add_annotation(x=250, y=20, text="steamstatsvisualized.streamlit.app",
                       font=dict(size=11, color="#555555"), showarrow=False, xanchor="center")

    fig.update_layout(
        width=500, height=600,
        plot_bgcolor="#1a1a2e", paper_bgcolor="#1a1a2e",
        margin=dict(l=0, r=0, t=0, b=0),
        template=DARK_TEMPLATE,
    )
    return fig


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
