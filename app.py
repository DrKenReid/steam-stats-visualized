"""Steam Stats Visualized — See your Steam library like never before."""

import urllib.parse
import pandas as pd
import streamlit as st
from src.steam_api import (
    parse_steam_input, get_player_summary, get_owned_games,
    get_recent_games, get_app_details_batch, get_achievement_stats,
    get_player_achievements, get_global_achievement_percentages,
    get_game_schema,
)
from src.analytics import (
    apply_time_filter, build_games_df, key_stats, top_games, unplayed_games,
    extract_genres, cost_per_hour, account_age_str,
    stats_commentary, top_game_roast, backlog_roast,
    account_age_commentary, genre_commentary, game_meme,
    gaming_personality, platform_breakdown, most_expensive_unplayed,
    compare_stats, shared_games, comparison_commentary, comparison_personality,
    top_games_per_genre, recent_achievements, rarest_achievements,
    estimate_account_value, perfect_games, genre_personality_tags,
)
from src.charts import (
    top_games_chart, playtime_histogram, genre_treemap,
    cost_per_hour_chart, recent_games_chart, platform_pie_chart,
    shared_games_chart, stats_comparison_chart, top_games_comparison_chart,
    expensive_unplayed_chart,
)

st.set_page_config(page_title="Steam Stats Visualized", page_icon="🎮", layout="wide")

# --- Share button helper ---
SITE_URL = "https://drkenreid-steam-stats-visualized.streamlit.app"

def _build_share_url(player1_id: str = "", player2_id: str = "") -> str:
    """Build a shareable URL with player IDs as query params."""
    if player1_id and player2_id:
        return f"{SITE_URL}/?id={urllib.parse.quote(player1_id)}&vs={urllib.parse.quote(player2_id)}"
    elif player1_id:
        return f"{SITE_URL}/?id={urllib.parse.quote(player1_id)}"
    return SITE_URL

def share_buttons(section_title: str, share_text: str, share_url: str = ""):
    """Render social share buttons for a section."""
    url = share_url or SITE_URL
    encoded_text = urllib.parse.quote(f"{share_text}\n\nCheck yours: {url}")
    encoded_url = urllib.parse.quote(url)

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
default_vs = query_params.get("vs", "")

user_input = st.text_input("Steam Profile", value=default_input,
                           placeholder="e.g. Drkenreid, 76561197996360778, or https://steamcommunity.com/id/Drkenreid")

# --- Head-to-Head Comparison Toggle ---
compare_mode = st.checkbox("⚔️ Compare with another player", value=bool(default_vs))
user_input_2 = ""
if compare_mode:
    user_input_2 = st.text_input("Player 2 Steam Profile", value=default_vs,
                                 placeholder="e.g. vanity name, Steam ID, or profile URL")

if not user_input:
    st.info("👆 Enter a Steam profile to get started.")
    st.stop()

# --- Time Period Toggle ---
default_period = query_params.get("period", "")
period_options = ["All Time", "Last 2 Weeks"]
time_filter = st.radio(
    "⏱️ Time Period",
    period_options,
    index=1 if default_period == "2weeks" else 0,
    horizontal=True,
)
is_2weeks = time_filter == "Last 2 Weeks"

# Set query params so the URL is shareable
st.query_params["id"] = user_input
if is_2weeks:
    st.query_params["period"] = "2weeks"
elif "period" in st.query_params:
    del st.query_params["period"]
if compare_mode and user_input_2:
    st.query_params["vs"] = user_input_2
    my_share_url = _build_share_url(user_input, user_input_2)
elif "vs" in st.query_params:
    del st.query_params["vs"]
    my_share_url = _build_share_url(user_input)
else:
    my_share_url = _build_share_url(user_input)
# Append period to share URL if active
if is_2weeks and "?" in my_share_url:
    my_share_url += "&period=2weeks"

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

df_all = build_games_df(games_raw)

# --- Resolve Player 2 early so errors show at the top ---
p2_error = None
steam_id_2 = None
profile_2 = None
games_raw_2 = None
if compare_mode and user_input_2:
    try:
        with st.spinner("Resolving Player 2..."):
            steam_id_2 = parse_steam_input(user_input_2)
            profile_2 = get_player_summary(steam_id_2)
            games_raw_2 = get_owned_games(steam_id_2)
    except ValueError as e:
        p2_error = str(e)
        st.error(f"⚔️ Player 2 error: {e}")
        st.warning("Showing Player 1 stats only. Fix Player 2's profile to see the comparison.")

df = apply_time_filter(df_all, "last_2_weeks" if is_2weeks else "all_time")
if is_2weeks and df.empty:
    st.warning("No games played in the last 2 weeks. Showing all-time stats instead.")
    df = df_all
    is_2weeks = False
stats = key_stats(df)
persona_name = profile.get("personaname", "Unknown")

# Determine if we're in a valid comparison mode
show_comparison = compare_mode and user_input_2 and not p2_error and games_raw_2

if is_2weeks:
    st.info("📅 Showing stats for the **last 2 weeks** only.")

# Compute personality & account_years early (needed by both single-player and comparison)
account_years = 0
if "timecreated" in profile:
    from datetime import datetime, timezone
    account_years = datetime.now(timezone.utc).year - datetime.fromtimestamp(profile["timecreated"], tz=timezone.utc).year

title, emoji, description = gaming_personality(stats, df, account_years)

# Compute platforms early (needed by both single-player and comparison)
platforms = platform_breakdown(df_all if is_2weeks else df)

# ─── Single-Player View ─────────────────────────────────────────────
if not show_comparison:
    # ─── Gaming Personality ──────────────────────────────────────────
    st.divider()
    personality_label = "This Week's Vibe" if is_2weeks else ""

    st.markdown(
        f'<div style="text-align:center;padding:20px 0;">'
        f'<span style="font-size:64px;">{emoji}</span><br>'
        f'<h2 style="margin:8px 0 4px 0;">{persona_name} is: {title}</h2>'
        f'<p style="font-size:18px;color:#aaa;">{description}</p>'
        f'{"<p style=\"font-size:14px;color:#888;\">(Based on last 2 weeks)</p>" if is_2weeks else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )
    share_buttons("Personality", f"🎮 I'm \"{title}\" {emoji} on Steam Stats Visualized! {description}", my_share_url)

    # ─── Profile Header ─────────────────────────────────────────────
    st.divider()
    col_avatar, col_info = st.columns([1, 4])
    with col_avatar:
        st.image(profile.get("avatarfull", ""), width=120)
    with col_info:
        st.subheader(persona_name)
        if "timecreated" in profile:
            years_str, member_since = account_age_str(profile["timecreated"])
            st.markdown(account_age_commentary(years_str, member_since))

    # ─── Key Stats ───────────────────────────────────────────────────
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎮 Total Games", f"{stats['total_games']:,}")
    c2.metric("✅ Played", f"{stats['played']:,}")
    c3.metric("🕸️ Unplayed", f"{stats['unplayed']:,}")
    c4.metric("⏱️ Total Hours", f"{stats['total_hours']:,.0f}")

    st.markdown(stats_commentary(stats))
    share_buttons("Stats", f"🎮 {stats['total_games']} games, {stats['total_hours']:,.0f} hours ({stats['total_days']:,.0f} days), {stats['pct_played']}% played on Steam!", my_share_url)

    # ─── Account Value ───────────────────────────────────────────────
    st.divider()
    st.subheader("💰 Account Value")
    st.caption("Fetching price data for your top 100 games...")
    value_appids = df_all.head(100)["appid"].tolist()
    value_store = get_app_details_batch(value_appids)
    acct_value = estimate_account_value(value_store)

    if acct_value["total_games_priced"] > 0:
        cv1, cv2, cv3 = st.columns(3)
        cv1.metric("💵 Total Value", f"${acct_value['total_value']:,.2f}")
        cv2.metric("🎮 Games Priced", f"{acct_value['total_games_priced']}")
        cv3.metric("📊 Average Price", f"${acct_value['avg_price']:.2f}")

        # Cost per hour of entertainment
        total_hours = stats["total_hours"]
        if total_hours > 0:
            cpe = acct_value["total_value"] / total_hours
            st.metric("⏱️ Cost Per Hour of Entertainment", f"${cpe:.2f}")

        # Roast based on value
        pct_played = stats["pct_played"]
        wasted = acct_value["total_value"] * (1 - pct_played / 100)
        st.markdown(
            f"**${acct_value['total_value']:,.2f}** worth of games and you've played **{pct_played}%** of them. "
            f"That's **${wasted:,.2f}** of digital shelf ornaments. 🏺"
        )
        if acct_value["most_expensive"][1] > 0:
            st.markdown(f"Most expensive game: **{acct_value['most_expensive'][0]}** at **${acct_value['most_expensive'][1]:.2f}**.")
        st.caption("*Estimated based on current store prices for your top 100 games.*")
        share_buttons("Account Value", f"💰 My Steam library is worth ${acct_value['total_value']:,.2f}! Cost per hour: ${cpe:.2f}", my_share_url)
    else:
        st.info("No price data available for value estimation.")

    # ─── Top 10 Games ───────────────────────────────────────────────
    st.divider()
    st.subheader("🏆 Top 10 Games by Playtime" + (" (Last 2 Weeks)" if is_2weeks else ""))
    top = top_games(df)
    if not top.empty:
        top_name = top.iloc[0]["name"]
        top_hours = top.iloc[0]["hours"]
        st.markdown(top_game_roast(top_name, top_hours))
        st.plotly_chart(top_games_chart(top), use_container_width=True, key="top_games")
        share_buttons("Top 10", f"🏆 My most played Steam game is {top_name} with {top_hours:,.0f} hours!", my_share_url)

    # ─── Platform Breakdown ─────────────────────────────────────────
    st.divider()
    st.subheader("💻 Where You Game")
    if platforms:
        col_plat_chart, col_plat_info = st.columns([2, 3])
        with col_plat_chart:
            st.plotly_chart(platform_pie_chart(platforms), use_container_width=True, key="platform_pie")
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
        share_buttons("Platform", f"💻 My gaming platform breakdown: {', '.join(f'{p} {h:,.0f}h' for p, h in platforms.items())}", my_share_url)
    else:
        st.info("No platform-specific playtime data available (older accounts may not have this).")

    # ─── Backlog of Shame ───────────────────────────────────────────
    if not is_2weeks:
        st.divider()
        st.subheader("💀 The Backlog of Shame")
        unplayed = unplayed_games(df_all)
        st.markdown(backlog_roast(len(unplayed)))
        share_buttons("Backlog", f"💀 I have {len(unplayed)} unplayed games on Steam. Send help.", my_share_url)
        with st.expander(f"See all {len(unplayed)} unplayed games"):
            # Multi-column grid layout for wide-screen friendliness
            n_cols = 4
            cols = st.columns(n_cols)
            unplayed_list = unplayed["name"].tolist()
            for i, name in enumerate(unplayed_list):
                with cols[i % n_cols]:
                    st.write(f"• {name}")

    # ─── Playtime Distribution ──────────────────────────────────────
    st.divider()
    st.subheader("📊 Playtime Distribution")
    st.caption("Spoiler: most of your games have barely been touched.")
    st.plotly_chart(playtime_histogram(df), use_container_width=True, key="playtime_hist")
    share_buttons("Distribution", f"📊 My Steam playtime distribution is... concerning.", my_share_url)

    # ─── Genre Breakdown & Cost Per Hour ────────────────────────────
    st.divider()
    st.subheader("🎯 Genre Breakdown & Value Analysis")
    st.caption("Using details from your top 100 games...")

    top_appids = df[df["hours"] > 0].head(50)["appid"].tolist()
    store_details = get_app_details_batch(top_appids)
    # Merge in any extra data from value fetch
    store_details = {**store_details, **value_store}

    # Also fetch some unplayed game prices for the "most expensive unplayed" feature
    if not is_2weeks:
        unplayed_for_expensive = unplayed_games(df_all)
        unplayed_appids = unplayed_for_expensive.head(30)["appid"].tolist()
        unplayed_store = get_app_details_batch(unplayed_appids)

    if is_2weeks:
        # In 2-week mode, show genre only (no cost per hour)
        st.markdown("#### Genres")
        genre_df = extract_genres(store_details)
        if not genre_df.empty:
            top_genre = genre_df["genre"].value_counts().index[0]
            st.markdown(genre_commentary(top_genre))
            top_genre_map = top_games_per_genre(genre_df)
            st.plotly_chart(genre_treemap(genre_df, top_games_map=top_genre_map), use_container_width=True, key="genre_treemap")
            tags = genre_personality_tags(genre_df)
            if tags:
                pills_html = " ".join(
                    f'<span style="background:#1b9e77;color:white;padding:4px 12px;border-radius:16px;margin:2px;display:inline-block;font-size:14px;">{t}</span>'
                    for t in tags
                )
                st.markdown(f'<div style="margin:8px 0 12px 0;">{pills_html}</div>', unsafe_allow_html=True)
                share_buttons("Genre Tags", f"My gaming DNA: {' • '.join(tags)}", my_share_url)
            share_buttons("Genre", f"🎯 My most played Steam genre (last 2 weeks) is {top_genre}!", my_share_url)
        else:
            st.info("No genre data available.")
    else:
        col_genre, col_cost = st.columns(2)

        with col_genre:
            st.markdown("#### Genres")
            genre_df = extract_genres(store_details)
            if not genre_df.empty:
                top_genre = genre_df["genre"].value_counts().index[0]
                st.markdown(genre_commentary(top_genre))
                top_genre_map = top_games_per_genre(genre_df)
                st.plotly_chart(genre_treemap(genre_df, top_games_map=top_genre_map), use_container_width=True, key="genre_treemap")
                tags = genre_personality_tags(genre_df)
                if tags:
                    pills_html = " ".join(
                        f'<span style="background:#1b9e77;color:white;padding:4px 12px;border-radius:16px;margin:2px;display:inline-block;font-size:14px;">{t}</span>'
                        for t in tags
                    )
                    st.markdown(f'<div style="margin:8px 0 12px 0;">{pills_html}</div>', unsafe_allow_html=True)
                    share_buttons("Genre Tags", f"My gaming DNA: {' • '.join(tags)}", my_share_url)
                share_buttons("Genre", f"🎯 My most played Steam genre is {top_genre}!", my_share_url)
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
                    st.plotly_chart(cost_per_hour_chart(cph, best=True), use_container_width=True, key="cost_best")
                with tab_worst:
                    st.plotly_chart(cost_per_hour_chart(cph, best=False), use_container_width=True, key="cost_worst")
                share_buttons("Cost", f"💰 Best value Steam game: {best_name} at ${best_val:.2f}/hour!", my_share_url)
            else:
                st.info("No price data available.")

    # ─── Most Expensive Unplayed ────────────────────────────────────
    if not is_2weeks:
        expensive = most_expensive_unplayed(unplayed_for_expensive, unplayed_store)
        if expensive:
            st.divider()
            st.subheader("💸 Most Expensive Games You've Never Played")
            total_wasted = sum(price for _, price in expensive)
            st.markdown(f"You've got **${total_wasted:.2f}** worth of games just sitting there collecting digital dust. "
                        f"That's not a library, that's a donation to Gabe Newell. 🎁")
            if len(expensive) >= 3:
                st.markdown(f"Top offender: **{expensive[0][0]}** at **${expensive[0][1]:.2f}**. "
                            f"Runner-up: **{expensive[1][0]}** (${expensive[1][1]:.2f}). "
                            f"The audacity. 💅")
            st.plotly_chart(expensive_unplayed_chart(expensive), use_container_width=True, key="expensive_unplayed")
            share_buttons("Expensive", f"💸 I have ${total_wasted:.2f} worth of unplayed Steam games. I'm basically a charity.", my_share_url)

    # ─── Achievement Stats ──────────────────────────────────────────
    st.divider()
    st.subheader("🏅 Achievement Stats")
    st.caption("Checking your top games for achievements...")

    achievement_appids = df_all[df_all["hours"] > 0].head(40)["appid"].tolist()
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

        share_buttons("Achievements", f"🏅 {total_achieved} achievements unlocked across Steam! {overall_pct}% completion rate.", my_share_url)

        # ─── Perfect Games ──────────────────────────────────────────
        st.markdown("#### 🏆 Perfect Games")
        perfects = perfect_games(ach_stats)
        if perfects:
            st.markdown(f"**{len(perfects)}** games at 100%. You don't just play games, you *conquer* them. 👑")
            for pg in perfects:
                st.markdown(f"🏆 **{pg['name']}** — {pg['total']} achievements unlocked")
            share_buttons("Perfect Games", f"🏆 {len(perfects)} perfect games on Steam! 100% completion gang.", my_share_url)
        else:
            st.markdown("No perfect games yet. Casual. 😏")
            share_buttons("Perfect Games", "🏆 No perfect games yet on Steam... working on it!", my_share_url)

        # ─── Recently Unlocked Achievements ─────────────────────────
        st.markdown("#### 🕐 Recently Unlocked")
        ach_appids_for_detail = [a["appid"] for a in ach_stats]
        recent_achs = recent_achievements(steam_id, ach_appids_for_detail, get_player_achievements, n=10, get_game_schema_fn=get_game_schema)
        if recent_achs:
            recent_ach_df = pd.DataFrame(recent_achs)[["game", "achievement_name", "unlock_date"]]
            recent_ach_df.columns = ["Game", "Achievement", "Unlocked"]
            st.dataframe(recent_ach_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent achievement data available.")

        # ─── Rarest Achievements ────────────────────────────────────
        st.markdown("#### 💎 Rarest Achievements")
        rare_achs = rarest_achievements(steam_id, ach_appids_for_detail, get_player_achievements, get_global_achievement_percentages, n=10, get_game_schema_fn=get_game_schema)
        if rare_achs:
            rare_df = pd.DataFrame(rare_achs)[["achievement_name", "game", "global_percent"]]
            rare_df.columns = ["Achievement", "Game", "Global Unlock %"]
            st.dataframe(rare_df, use_container_width=True, hide_index=True)
            if rare_achs[0]["global_percent"] < 5:
                st.markdown(f"🔥 **{rare_achs[0]['achievement_name']}** in {rare_achs[0]['game']} — only **{rare_achs[0]['global_percent']}%** of players have this. You're built different.")
            rarest_text = f"💎 My rarest Steam achievement: {rare_achs[0]['achievement_name']} ({rare_achs[0]['game']}) — only {rare_achs[0]['global_percent']}% of players have it!"
            share_buttons("Rarest", rarest_text, my_share_url)
        else:
            st.info("No global achievement data available.")
    else:
        st.info("No achievement data available for your top games.")

    # ─── Recently Played ────────────────────────────────────────────
    st.divider()
    st.subheader("🕹️ Recently Played (Last 2 Weeks)")
    if recent:
        st.plotly_chart(recent_games_chart(recent), use_container_width=True, key="recent_games")
        recent_names = ", ".join(g["name"] for g in recent[:3])
        share_buttons("Recent", f"🕹️ Recently playing: {recent_names}", my_share_url)
    else:
        st.info("No recent activity. Touch grass achieved? 🌿")

    # ─── Gaming Streak ───────────────────────────────────────────────
    from src.analytics import calculate_streak, game_timeline
    from src.charts import game_timeline_chart

    st.divider()
    st.subheader("🔥 Gaming Streak")
    streak_data = calculate_streak(df_all)
    if streak_data["current_streak"] > 0:
        st.markdown(f"### 🔥 {streak_data['current_streak']} day streak!")
        st.markdown(f"Most recent game: **{streak_data['most_recent_game']}** (last played {streak_data['last_played_date']})")
    else:
        if streak_data["last_played_date"] != "Unknown":
            st.markdown(f"### 😴 No streak — last played on {streak_data['last_played_date']}")
            st.markdown(f"Most recent game: **{streak_data['most_recent_game']}**")
        else:
            st.markdown("### 😴 No streak data available")

    # ─── Game Timeline ──────────────────────────────────────────────
    st.divider()
    st.subheader("📅 Game Timeline")
    timeline = game_timeline(df_all, n=20)
    if not timeline.empty:
        st.plotly_chart(game_timeline_chart(timeline), use_container_width=True, key="timeline")
        st.caption("Your recent gaming history at a glance")
    else:
        st.info("No timeline data available.")

    # ─── Shareable Summary Card ─────────────────────────────────────
    st.divider()
    st.subheader("📸 Your Steam Summary Card")

    # Gather data for the card
    _card_top3 = top_games(df, 3)
    _card_top3_html = ""
    for _, _row in _card_top3.iterrows():
        _card_top3_html += f'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span>{_row["name"]}</span><span style="color:#1b9e77;">{_row["hours"]:,.0f}h</span></div>'

    _card_genres = ""
    try:
        if not genre_df.empty:
            _top_genres = genre_df["genre"].value_counts().head(3).index.tolist()
            _card_genres = " ".join(f'<span style="background:#1b9e77;color:white;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:4px;">{g}</span>' for g in _top_genres)
    except Exception:
        pass

    _avatar_url = profile.get("avatarfull", "")
    _persona = persona_name
    _personality_title = title
    _personality_emoji = emoji

    st.markdown(f'''
<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:16px;padding:24px;max-width:500px;margin:0 auto;font-family:sans-serif;color:white;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <img src="{_avatar_url}" style="width:56px;height:56px;border-radius:50%;border:2px solid #1b9e77;" />
        <div>
            <div style="font-size:20px;font-weight:bold;">{_persona}</div>
            <div style="color:#aaa;font-size:14px;">{_personality_emoji} {_personality_title}</div>
        </div>
    </div>
    <div style="display:flex;justify-content:space-between;text-align:center;background:rgba(255,255,255,0.05);border-radius:8px;padding:12px;margin-bottom:16px;">
        <div><div style="font-size:18px;font-weight:bold;">{stats["total_games"]:,}</div><div style="font-size:11px;color:#888;">Games</div></div>
        <div><div style="font-size:18px;font-weight:bold;">{stats["total_hours"]:,.0f}</div><div style="font-size:11px;color:#888;">Hours</div></div>
        <div><div style="font-size:18px;font-weight:bold;">{stats["pct_played"]}%</div><div style="font-size:11px;color:#888;">Played</div></div>
        <div><div style="font-size:18px;font-weight:bold;">{account_years}y</div><div style="font-size:11px;color:#888;">Account Age</div></div>
    </div>
    <div style="margin-bottom:12px;">
        <div style="font-size:12px;color:#888;margin-bottom:4px;">🏆 TOP GAMES</div>
        {_card_top3_html}
    </div>
    <div style="margin-bottom:16px;">
        {_card_genres}
    </div>
    <div style="text-align:center;color:#555;font-size:11px;border-top:1px solid #333;padding-top:8px;">
        steamstatsvisualized.streamlit.app
    </div>
</div>
''', unsafe_allow_html=True)

    st.caption("📱 Screenshot this card and share it!")
    share_buttons("Summary Card", f"🎮 Check out my Steam stats! {_personality_emoji} {_personality_title} — {stats['total_games']} games, {stats['total_hours']:,.0f} hours!", my_share_url)

# ─── Head-to-Head Comparison ─────────────────────────────────────────
if show_comparison:
    st.divider()
    st.header("⚔️ Head-to-Head Comparison")

    df_2 = build_games_df(games_raw_2)
    stats_2 = key_stats(df_2)
    persona_name_2 = profile_2.get("personaname", "Unknown")

    account_years_2 = 0
    if "timecreated" in profile_2:
        account_years_2 = datetime.now(timezone.utc).year - datetime.fromtimestamp(profile_2["timecreated"], tz=timezone.utc).year

    title_2, emoji_2, description_2 = gaming_personality(stats_2, df_2, account_years_2)

    # --- Profile Cards ---
    st.subheader("👥 Profile Cards")
    col_p1, col_vs, col_p2 = st.columns([5, 1, 5])
    with col_p1:
        st.image(profile.get("avatarfull", ""), width=100)
        st.markdown(f"**{persona_name}**")
        if "timecreated" in profile:
            y1, s1 = account_age_str(profile["timecreated"])
            st.caption(f"Member since {s1} ({y1})")
    with col_vs:
        st.markdown("<div style='text-align:center;padding-top:30px;font-size:40px;'>⚔️</div>", unsafe_allow_html=True)
    with col_p2:
        st.image(profile_2.get("avatarfull", ""), width=100)
        st.markdown(f"**{persona_name_2}**")
        if "timecreated" in profile_2:
            y2, s2 = account_age_str(profile_2["timecreated"])
            st.caption(f"Member since {s2} ({y2})")

    # --- Gaming Personality Face-off ---
    st.subheader("🧠 Personality Face-off")
    col_pers1, col_pers2 = st.columns(2)
    with col_pers1:
        st.markdown(f"<div style='text-align:center;'><span style='font-size:48px;'>{emoji}</span><br><b>{persona_name}</b><br>{title}</div>", unsafe_allow_html=True)
    with col_pers2:
        st.markdown(f"<div style='text-align:center;'><span style='font-size:48px;'>{emoji_2}</span><br><b>{persona_name_2}</b><br>{title_2}</div>", unsafe_allow_html=True)
    st.markdown(comparison_personality(title, title_2, persona_name, persona_name_2))
    share_buttons("Personality Matchup", f"⚔️ {persona_name} ({title}) vs {persona_name_2} ({title_2}) on Steam Stats Visualized!", my_share_url)

    # --- Stats Showdown ---
    st.subheader("📊 Stats Showdown")
    comparison = compare_stats(stats, stats_2, persona_name, persona_name_2)
    for item in comparison:
        winner_icon = "🏆" if item["winner"] != "Tie" else "🤝"
        winner_text = f"**{item['winner']}** wins" if item["winner"] != "Tie" else "**Tie!**"
        st.markdown(
            f"{item['icon']} **{item['metric']}**: "
            f"{persona_name} **{item['p1_value']:,}** vs {persona_name_2} **{item['p2_value']:,}** "
            f"→ {winner_icon} {winner_text}"
        )
    st.plotly_chart(stats_comparison_chart(stats, stats_2, persona_name, persona_name_2), use_container_width=True, key="stats_compare")
    share_buttons("Stats Showdown", f"⚔️ Steam Stats Showdown: {persona_name} vs {persona_name_2}!", my_share_url)

    # --- Shared Games ---
    st.subheader("🤝 Shared Games")
    shared_df = shared_games(df, df_2)
    st.markdown(f"**{len(shared_df)}** games in common!")
    unique_p1 = len(df[~df["appid"].isin(df_2["appid"])])
    unique_p2 = len(df_2[~df_2["appid"].isin(df["appid"])])
    col_u1, col_u2 = st.columns(2)
    col_u1.metric(f"🎯 Only {persona_name}", unique_p1)
    col_u2.metric(f"🎯 Only {persona_name_2}", unique_p2)
    if not shared_df.empty:
        st.plotly_chart(shared_games_chart(shared_df, persona_name, persona_name_2), use_container_width=True, key="shared_games")

    # --- Top Games Comparison ---
    st.subheader("🏆 Top Games Comparison")
    st.plotly_chart(top_games_comparison_chart(df, df_2, persona_name, persona_name_2), use_container_width=True, key="top_compare")

    # --- Platform Breakdown Side by Side ---
    platforms_2 = platform_breakdown(df_2)
    if platforms or platforms_2:
        st.subheader("💻 Platform Breakdown")
        col_plat1, col_plat2 = st.columns(2)
        with col_plat1:
            st.markdown(f"**{persona_name}**")
            if platforms:
                st.plotly_chart(platform_pie_chart(platforms), use_container_width=True, key="p1_platform_pie")
            else:
                st.info("No platform data")
        with col_plat2:
            st.markdown(f"**{persona_name_2}**")
            if platforms_2:
                st.plotly_chart(platform_pie_chart(platforms_2), use_container_width=True, key="p2_platform_pie")
            else:
                st.info("No platform data")

    # --- Comparison Commentary ---
    st.subheader("🔥 The Verdict")
    st.markdown(comparison_commentary(stats, stats_2, persona_name, persona_name_2))
    share_buttons("Comparison", f"⚔️ {persona_name} vs {persona_name_2} — Steam Stats Head-to-Head!", my_share_url)

# ─── Footer ──────────────────────────────────────────────────────────
st.divider()
st.caption("Built with Streamlit, Plotly, and questionable life choices. | [GitHub](https://github.com/drkenreid/steam-stats-visualized)")
