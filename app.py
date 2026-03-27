"""Steam Stats Visualized — See your Steam library like never before."""

import urllib.parse
import pandas as pd
import streamlit as st
from src.steam_api import (
    parse_steam_input, get_player_summary, get_owned_games,
    get_recent_games, get_app_details_batch, get_achievement_stats,
)
from src.analytics import (
    build_games_df, key_stats, top_games, unplayed_games,
    extract_genres, cost_per_hour, account_age_str,
    stats_commentary, top_game_roast, backlog_roast,
    account_age_commentary, genre_commentary, game_meme,
    gaming_personality, platform_breakdown, most_expensive_unplayed,
)
from src.charts import (
    top_games_chart, playtime_histogram, genre_treemap,
    cost_per_hour_chart, recent_games_chart, platform_pie_chart,
)

st.set_page_config(page_title="Steam Stats Visualized", page_icon="🎮", layout="wide")

# --- Share button helper ---
SITE_URL = "https://github.com/drkenreid/steam-stats-visualized"

def share_buttons(section_title: str, share_text: str):
    """Render social share buttons for a section."""
    encoded_text = urllib.parse.quote(f"{share_text}\n\nCheck yours: {SITE_URL}")
    encoded_url = urllib.parse.quote(SITE_URL)

    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
    reddit_url = f"https://reddit.com/submit?url={encoded_url}&title={urllib.parse.quote(share_text)}"
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}&quote={urllib.parse.quote(share_text)}"
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"

    st.markdown(
        f'<div style="display:flex;gap:8px;margin:4px 0 12px 0;">'
        f'<a href="{twitter_url}" target="_blank" style="background:#1DA1F2;color:white;padding:4px 10px;border-radius:4px;text-decoration:none;font-size:12px;">𝕏 Tweet</a>'
        f'<a href="{reddit_url}" target="_blank" style="background:#FF4500;color:white;padding:4px 10px;border-radius:4px;text-decoration:none;font-size:12px;">Reddit</a>'
        f'<a href="{facebook_url}" target="_blank" style="background:#4267B2;color:white;padding:4px 10px;border-radius:4px;text-decoration:none;font-size:12px;">Facebook</a>'
        f'<a href="{linkedin_url}" target="_blank" style="background:#0077B5;color:white;padding:4px 10px;border-radius:4px;text-decoration:none;font-size:12px;">LinkedIn</a>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.title("🎮 Steam Stats Visualized")
st.caption("Paste your Steam profile URL, vanity name, or Steam ID below and prepare to be roasted.")

# Support URL query params for shareable links
query_params = st.query_params
default_input = query_params.get("id", "")

user_input = st.text_input("Steam Profile", value=default_input,
                           placeholder="e.g. Drkenreid, 76561197996360778, or https://steamcommunity.com/id/Drkenreid")

if not user_input:
    st.info("👆 Enter a Steam profile to get started.")
    st.stop()

# Set query param so the URL is shareable
st.query_params["id"] = user_input

# --- Resolve & fetch ---
try:
    with st.spinner("Resolving Steam ID..."):
        steam_id = parse_steam_input(user_input)
except ValueError as e:
    st.error(str(e))
    st.stop()

try:
    with st.spinner("Loading profile..."):
        profile = get_player_summary(steam_id)
        games_raw = get_owned_games(steam_id)
        recent = get_recent_games(steam_id)
except ValueError as e:
    st.error(str(e))
    st.stop()

df = build_games_df(games_raw)
stats = key_stats(df)
persona_name = profile.get("personaname", "Unknown")

# ─── Gaming Personality ──────────────────────────────────────────────
st.divider()
account_years = 0
if "timecreated" in profile:
    from datetime import datetime, timezone
    account_years = datetime.now(timezone.utc).year - datetime.fromtimestamp(profile["timecreated"], tz=timezone.utc).year

title, emoji, description = gaming_personality(stats, df, account_years)

st.markdown(
    f'<div style="text-align:center;padding:20px 0;">'
    f'<span style="font-size:64px;">{emoji}</span><br>'
    f'<h2 style="margin:8px 0 4px 0;">{persona_name} is: {title}</h2>'
    f'<p style="font-size:18px;color:#aaa;">{description}</p>'
    f'</div>',
    unsafe_allow_html=True,
)
share_buttons("Personality", f"🎮 I'm \"{title}\" {emoji} on Steam Stats Visualized! {description}")

# ─── Profile Header ─────────────────────────────────────────────────
st.divider()
col_avatar, col_info = st.columns([1, 4])
with col_avatar:
    st.image(profile.get("avatarfull", ""), width=120)
with col_info:
    st.subheader(persona_name)
    if "timecreated" in profile:
        years_str, member_since = account_age_str(profile["timecreated"])
        st.markdown(account_age_commentary(years_str, member_since))

# ─── Key Stats ───────────────────────────────────────────────────────
st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("🎮 Total Games", f"{stats['total_games']:,}")
c2.metric("✅ Played", f"{stats['played']:,}")
c3.metric("🕸️ Unplayed", f"{stats['unplayed']:,}")
c4.metric("⏱️ Total Hours", f"{stats['total_hours']:,.0f}")

st.markdown(stats_commentary(stats))
share_buttons("Stats", f"🎮 {stats['total_games']} games, {stats['total_hours']:,.0f} hours ({stats['total_days']:,.0f} days), {stats['pct_played']}% played on Steam!")

# ─── Top 10 Games ───────────────────────────────────────────────────
st.divider()
st.subheader("🏆 Top 10 Games by Playtime")
top = top_games(df)
if not top.empty:
    top_name = top.iloc[0]["name"]
    top_hours = top.iloc[0]["hours"]
    st.markdown(top_game_roast(top_name, top_hours))
    st.plotly_chart(top_games_chart(top), use_container_width=True)
    share_buttons("Top 10", f"🏆 My most played Steam game is {top_name} with {top_hours:,.0f} hours!")
    # Game-specific meme references
    memes = [(row["name"], row["hours"], game_meme(row["name"])) for _, row in top.iterrows() if game_meme(row["name"])]
    if memes:
        with st.expander("🎭 Game memes & references"):
            for name, hours, meme in memes:
                st.markdown(f"**{name}** ({hours:,.0f}h) — *{meme}*")

# ─── Platform Breakdown ─────────────────────────────────────────────
st.divider()
st.subheader("💻 Where You Game")
platforms = platform_breakdown(df)
if platforms:
    col_plat_chart, col_plat_info = st.columns([2, 3])
    with col_plat_chart:
        st.plotly_chart(platform_pie_chart(platforms), use_container_width=True)
    with col_plat_info:
        for platform, hours in sorted(platforms.items(), key=lambda x: -x[1]):
            pct = round(100 * hours / sum(platforms.values()), 1)
            icon = {"Windows": "🪟", "Mac": "🍎", "Linux": "🐧", "Steam Deck": "🎮"}.get(platform, "💻")
            st.markdown(f"{icon} **{platform}**: {hours:,.0f}h ({pct}%)")
        if "Steam Deck" in platforms:
            st.markdown("*Steam Deck gang! 🫡*")
        if len(platforms) == 1:
            only = list(platforms.keys())[0]
            st.markdown(f"*100% {only}. Ride or die. 🏴*")
        elif len(platforms) >= 3:
            st.markdown("*Multi-platform gamer. Respect the versatility. 🌈*")
    share_buttons("Platform", f"💻 My gaming platform breakdown: {', '.join(f'{p} {h:,.0f}h' for p, h in platforms.items())}")
else:
    st.info("No platform-specific playtime data available (older accounts may not have this).")

# ─── Backlog of Shame ───────────────────────────────────────────────
st.divider()
st.subheader("💀 The Backlog of Shame")
unplayed = unplayed_games(df)
st.markdown(backlog_roast(len(unplayed)))
share_buttons("Backlog", f"💀 I have {len(unplayed)} unplayed games on Steam. Send help.")
with st.expander(f"See all {len(unplayed)} unplayed games"):
    for _, row in unplayed.iterrows():
        st.write(f"• {row['name']}")

# ─── Playtime Distribution ──────────────────────────────────────────
st.divider()
st.subheader("📊 Playtime Distribution")
st.caption("Spoiler: most of your games have barely been touched.")
st.plotly_chart(playtime_histogram(df), use_container_width=True)
share_buttons("Distribution", f"📊 My Steam playtime distribution is... concerning.")

# ─── Genre Breakdown & Cost Per Hour ────────────────────────────────
st.divider()
st.subheader("🎯 Genre Breakdown & Value Analysis")
st.caption("Fetching details for your top 50 most-played games...")

top_appids = df[df["hours"] > 0].head(50)["appid"].tolist()
store_details = get_app_details_batch(top_appids)

# Also fetch some unplayed game prices for the "most expensive unplayed" feature
unplayed_appids = unplayed.head(30)["appid"].tolist()
unplayed_store = get_app_details_batch(unplayed_appids)

col_genre, col_cost = st.columns(2)

with col_genre:
    st.markdown("#### Genres")
    genre_df = extract_genres(store_details)
    if not genre_df.empty:
        top_genre = genre_df["genre"].value_counts().index[0]
        st.markdown(genre_commentary(top_genre))
        st.plotly_chart(genre_treemap(genre_df), use_container_width=True)
        share_buttons("Genre", f"🎯 My most played Steam genre is {top_genre}!")
    else:
        st.info("No genre data available.")

with col_cost:
    st.markdown("#### 💰 Cost Per Hour")
    cph = cost_per_hour(store_details, df)
    if not cph.empty:
        best_name = cph.iloc[0]["name"]
        best_val = cph.iloc[0]["cost_per_hour"]
        st.markdown(f"Best bang for your buck: **{best_name}** at **${best_val:.2f}/hour**. Basically free entertainment.")
        tab_best, tab_worst = st.tabs(["Best Value", "Worst Value"])
        with tab_best:
            st.plotly_chart(cost_per_hour_chart(cph, best=True), use_container_width=True)
        with tab_worst:
            st.plotly_chart(cost_per_hour_chart(cph, best=False), use_container_width=True)
        share_buttons("Cost", f"💰 Best value Steam game: {best_name} at ${best_val:.2f}/hour!")
    else:
        st.info("No price data available.")

# ─── Most Expensive Unplayed ────────────────────────────────────────
expensive = most_expensive_unplayed(unplayed, unplayed_store)
if expensive:
    st.divider()
    st.subheader("💸 Most Expensive Game You've Never Played")
    exp_name, exp_price = expensive
    st.markdown(f"**{exp_name}** — ${exp_price:.2f} just sitting there. Collecting digital dust. "
                f"That's not a purchase, that's a donation to Gabe Newell. 🎁")
    share_buttons("Expensive", f"💸 My most expensive unplayed Steam game is {exp_name} (${exp_price:.2f}). I'm basically a charity.")

# ─── Achievement Stats ──────────────────────────────────────────────
st.divider()
st.subheader("🏅 Achievement Stats")
st.caption("Checking your top games for achievements...")

achievement_appids = df[df["hours"] > 0].head(40)["appid"].tolist()
ach_stats = get_achievement_stats(steam_id, achievement_appids, max_games=15)

if ach_stats:
    ach_df = pd.DataFrame(ach_stats).sort_values("pct", ascending=False)

    # Overall stats
    total_achieved = sum(a["achieved"] for a in ach_stats)
    total_possible = sum(a["total"] for a in ach_stats)
    overall_pct = round(100 * total_achieved / total_possible, 1) if total_possible else 0

    col_ach1, col_ach2, col_ach3 = st.columns(3)
    col_ach1.metric("🏆 Achievements Unlocked", f"{total_achieved:,}")
    col_ach2.metric("📋 Total Available", f"{total_possible:,}")
    col_ach3.metric("📊 Completion Rate", f"{overall_pct}%")

    if overall_pct > 70:
        st.markdown("You're a completionist. Achievements aren't optional — they're mandatory. 💪")
    elif overall_pct > 40:
        st.markdown("Decent completion rate. You care about achievements, but you're not losing sleep over them.")
    else:
        st.markdown("Achievements? More like suggestions. You play for vibes, not checkboxes. 🧘")

    # Most completed game
    best_game = ach_df.iloc[0]
    st.markdown(f"**Most completed:** {best_game['name']} — **{best_game['pct']}%** ({best_game['achieved']}/{best_game['total']})")

    # Least completed
    worst_game = ach_df.iloc[-1]
    if worst_game["pct"] < 20:
        st.markdown(f"**Least completed:** {worst_game['name']} — **{worst_game['pct']}%** ({worst_game['achieved']}/{worst_game['total']}). Barely scratched the surface.")

    with st.expander("See all achievement stats"):
        for _, row in ach_df.iterrows():
            bar_filled = int(row["pct"] / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            st.markdown(f"**{row['name']}** — {row['pct']}% ({row['achieved']}/{row['total']})")
            st.caption(f"`{bar}`")

    share_buttons("Achievements", f"🏅 {total_achieved} achievements unlocked across Steam! {overall_pct}% completion rate.")
else:
    st.info("No achievement data available for your top games.")

# ─── Recently Played ────────────────────────────────────────────────
st.divider()
st.subheader("🕹️ Recently Played (Last 2 Weeks)")
if recent:
    st.plotly_chart(recent_games_chart(recent), use_container_width=True)
    recent_names = ", ".join(g["name"] for g in recent[:3])
    share_buttons("Recent", f"🕹️ Recently playing: {recent_names}")
else:
    st.info("No recent activity. Touch grass achieved? 🌿")

# ─── Footer ──────────────────────────────────────────────────────────
st.divider()
st.caption("Built with Streamlit, Plotly, and questionable life choices. | [GitHub](https://github.com/drkenreid/steam-stats-visualized)")
