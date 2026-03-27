"""Steam API client with caching."""

from __future__ import annotations

import re
import time
import requests
import streamlit as st


BASE = "https://api.steampowered.com"
STORE = "https://store.steampowered.com/api/appdetails"


def _key() -> str:
    return st.secrets["STEAM_API_KEY"]


def parse_steam_input(raw: str) -> str:
    """Parse a Steam profile URL, vanity name, or Steam ID into a Steam ID (64-bit)."""
    raw = raw.strip().rstrip("/")
    # Direct 64-bit ID
    if re.fullmatch(r"\d{17}", raw):
        return raw
    # URL patterns
    m = re.search(r"steamcommunity\.com/profiles/(\d{17})", raw)
    if m:
        return m.group(1)
    m = re.search(r"steamcommunity\.com/id/([^/]+)", raw)
    if m:
        return resolve_vanity(m.group(1))
    # Assume vanity name
    return resolve_vanity(raw)


@st.cache_data(ttl=3600)
def resolve_vanity(vanity: str) -> str:
    r = requests.get(f"{BASE}/ISteamUser/ResolveVanityURL/v0001/",
                     params={"key": _key(), "vanityurl": vanity}, timeout=10)
    data = r.json().get("response", {})
    if data.get("success") != 1:
        raise ValueError(f"Could not resolve vanity name '{vanity}'. Check the profile URL.")
    return str(data["steamid"])


@st.cache_data(ttl=3600)
def get_player_summary(steam_id: str) -> dict:
    r = requests.get(f"{BASE}/ISteamUser/GetPlayerSummaries/v0002/",
                     params={"key": _key(), "steamids": steam_id}, timeout=10)
    players = r.json().get("response", {}).get("players", [])
    if not players:
        raise ValueError("Profile not found or is private.")
    return players[0]


@st.cache_data(ttl=3600)
def get_owned_games(steam_id: str) -> list[dict]:
    r = requests.get(f"{BASE}/IPlayerService/GetOwnedGames/v0001/",
                     params={"key": _key(), "steamid": steam_id,
                             "include_appinfo": "true",
                             "include_played_free_games": "true",
                             "format": "json"}, timeout=15)
    data = r.json().get("response", {})
    if "games" not in data:
        raise ValueError("Game library is private or empty.")
    return data["games"]


@st.cache_data(ttl=3600)
def get_recent_games(steam_id: str) -> list[dict]:
    r = requests.get(f"{BASE}/IPlayerService/GetRecentlyPlayedGames/v0001/",
                     params={"key": _key(), "steamid": steam_id, "format": "json"}, timeout=10)
    return r.json().get("response", {}).get("games", [])


@st.cache_data(ttl=3600)
def get_app_details(appid: int) -> dict | None:
    """Fetch store details for a single app. Returns None on failure."""
    try:
        r = requests.get(STORE, params={"appids": appid, "cc": "us"}, timeout=10)
        data = r.json()
        entry = data.get(str(appid), {})
        if entry.get("success"):
            return entry["data"]
    except Exception:
        pass
    return None


def get_app_details_batch(appids: list[int], delay: float = 0.25) -> dict[int, dict]:
    """Fetch store details for multiple apps with rate limiting."""
    results = {}
    progress = st.progress(0, text="Fetching game details...")
    for i, appid in enumerate(appids):
        details = get_app_details(appid)
        if details:
            results[appid] = details
        if i < len(appids) - 1:
            time.sleep(delay)
        progress.progress((i + 1) / len(appids), text=f"Fetching game details... {i+1}/{len(appids)}")
    progress.empty()
    return results


@st.cache_data(ttl=3600)
def get_player_achievements(steam_id: str, appid: int) -> dict | None:
    """Fetch achievement stats for a single game. Returns None on failure."""
    try:
        r = requests.get(f"{BASE}/ISteamUserStats/GetPlayerAchievements/v0001/",
                         params={"key": _key(), "steamid": steam_id, "appid": appid, "format": "json"},
                         timeout=10)
        data = r.json().get("playerstats", {})
        if data.get("success"):
            return data
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600)
def get_global_achievement_percentages(appid: int) -> list[dict] | None:
    """Fetch global achievement unlock percentages for a game."""
    try:
        r = requests.get(f"{BASE}/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/",
                         params={"gameid": appid, "format": "json"}, timeout=10)
        data = r.json().get("achievementpercentages", {}).get("achievements", [])
        return data if data else None
    except Exception:
        return None


def get_achievement_stats(steam_id: str, appids: list[int], max_games: int = 20, delay: float = 0.3) -> list[dict]:
    """Fetch achievement completion for top games. Returns list of {name, achieved, total, pct}."""
    results = []
    progress = st.progress(0, text="Fetching achievements...")
    checked = 0
    for i, appid in enumerate(appids):
        if checked >= max_games:
            break
        data = get_player_achievements(steam_id, appid)
        if data and "achievements" in data:
            achievements = data["achievements"]
            total = len(achievements)
            achieved = sum(1 for a in achievements if a.get("achieved"))
            if total > 0:
                results.append({
                    "name": data.get("gameName", f"App {appid}"),
                    "appid": appid,
                    "achieved": achieved,
                    "total": total,
                    "pct": round(100 * achieved / total, 1),
                })
                checked += 1
        if i < len(appids) - 1:
            time.sleep(delay)
        progress.progress(min(1.0, (i + 1) / min(len(appids), max_games * 2)),
                         text=f"Fetching achievements... {checked}/{max_games}")
    progress.empty()
    return results
