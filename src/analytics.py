"""Data processing, metrics, and commentary generation."""

from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd


def apply_time_filter(df: pd.DataFrame, filter_type: str = "all_time") -> pd.DataFrame:
    """Return a DataFrame filtered for the chosen time period.

    - "all_time": returns df unchanged.
    - "last_2_weeks": replaces ``hours`` with ``hours_2weeks``, keeps only
      games with ``hours_2weeks > 0``, and re-sorts.
    """
    if filter_type == "all_time":
        return df
    out = df.copy()
    out["hours_alltime"] = out["hours"]          # preserve original
    out["hours"] = out["hours_2weeks"]
    out = out[out["hours"] > 0].sort_values("hours", ascending=False).reset_index(drop=True)
    return out


def build_games_df(games: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(games)
    df["hours"] = (df["playtime_forever"] / 60).round(1)
    df["hours_2weeks"] = (df.get("playtime_2weeks", pd.Series(dtype=float)).fillna(0) / 60).round(1) if "playtime_2weeks" in df.columns else 0.0
    df = df.sort_values("hours", ascending=False).reset_index(drop=True)
    return df


def key_stats(df: pd.DataFrame) -> dict:
    total = len(df)
    played = int((df["hours"] > 0).sum())
    unplayed = total - played
    total_hours = df["hours"].sum()
    return {
        "total_games": total,
        "played": played,
        "unplayed": unplayed,
        "pct_played": round(100 * played / total, 1) if total else 0,
        "total_hours": round(total_hours, 1),
        "total_days": round(total_hours / 24, 1),
    }


def top_games(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return df.head(n)[["name", "hours", "appid"]].copy()


def unplayed_games(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["hours"] == 0][["name", "appid"]].copy()


def playtime_bins(df: pd.DataFrame) -> pd.DataFrame:
    played = df[df["hours"] > 0].copy()
    return played


def extract_genres(store_details: dict[int, dict]) -> pd.DataFrame:
    rows = []
    for appid, data in store_details.items():
        name = data.get("name", "Unknown")
        for g in data.get("genres", []):
            rows.append({"appid": appid, "name": name, "genre": g["description"]})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["appid", "name", "genre"])


def cost_per_hour(store_details: dict[int, dict], df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for appid, data in store_details.items():
        price_data = data.get("price_overview")
        if not price_data:
            continue
        price = price_data.get("final", 0) / 100  # cents to dollars
        game_row = df[df["appid"] == appid]
        if game_row.empty:
            continue
        hours = float(game_row["hours"].iloc[0])
        if hours < 0.5:
            continue
        rows.append({
            "name": data.get("name", "Unknown"),
            "price": price,
            "hours": hours,
            "cost_per_hour": round(price / hours, 2),
        })
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("cost_per_hour").reset_index(drop=True)
    return result


def account_age_str(timecreated: int) -> tuple[str, str]:
    created = datetime.fromtimestamp(timecreated, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    years = now.year - created.year
    member_since = created.strftime("%B %d, %Y")
    return f"{years} years", member_since


# --- Commentary generators ---

def stats_commentary(stats: dict) -> str:
    unplayed = stats["unplayed"]
    total = stats["total_games"]
    pct = stats["pct_played"]
    lines = []
    lines.append(f"You own **{total}** games. You've played **{stats['played']}**. "
                 f"The other **{unplayed}** are just... vibes.")
    if pct < 30:
        lines.append(f"That's only **{pct}%** played. Your library is basically a museum. 🏛️")
    elif pct < 50:
        lines.append(f"**{pct}%** played — roughly half your library is decorative.")
    else:
        lines.append(f"**{pct}%** played — okay, you actually play your games. Rare breed. 🦄")

    days = stats["total_days"]
    lines.append(f"Total playtime: **{stats['total_hours']:,.0f}** hours. "
                 f"That's **{days:,.0f} days** of your life. No refunds.")
    return "\n\n".join(lines)


GAME_MEMES: dict[str, str] = {
    "Factorio": "The factory must grow. 🏭",
    "Rimworld": "War crimes simulator, according to the community. Geneva Convention? Never heard of it. 🔥",
    "RimWorld": "War crimes simulator, according to the community. Geneva Convention? Never heard of it. 🔥",
    "Terraria": "It's not a 2D Minecraft. They will fight you over this. ⛏️",
    "Stardew Valley": "One more day... *14 hours later* 🌾",
    "Counter-Strike 2": "Rush B. Don't stop. Cyka blyat. 💣",
    "Counter-Strike: Global Offensive": "Rush B. Don't stop. Cyka blyat. 💣",
    "Dota 2": "Abandon all hope, ye who queue here. 🫠",
    "Team Fortress 2": "Hats. It's always been about the hats. 🎩",
    "Skyrim": "Hey, you. You're finally awake. For the 500th time. 🐉",
    "The Elder Scrolls V: Skyrim Special Edition": "Hey, you. You're finally awake. For the 500th time. 🐉",
    "The Elder Scrolls V: Skyrim": "Hey, you. You're finally awake. For the 500th time. 🐉",
    "Baldur's Gate 3": "You can romance a bear. We're not here to judge. Actually, yes we are. 🐻",
    "Stellaris": "Purge the xenos... diplomatically, of course. 🌌",
    "Civilization V": "One more turn. ONE MORE TURN. 🌍",
    "Sid Meier's Civilization V": "One more turn. ONE MORE TURN. 🌍",
    "Sid Meier's Civilization VI": "One more turn. ONE MORE TURN. 🌍",
    "Sid Meier's Civilization IV": "One more turn. ONE MORE TURN. 🌍",
    "Europa Universalis IV": "You've spent more time looking at maps than actual cartographers. 🗺️",
    "Crusader Kings III": "The family tree is more of a family wreath at this point. 👑",
    "Crusader Kings II": "The family tree is more of a family wreath at this point. 👑",
    "Kerbal Space Program": "Jeb is still in orbit from 2015. We should probably do something about that. 🚀",
    "Dark Souls": "YOU DIED (and kept coming back, you absolute masochist). ☠️",
    "DARK SOULS III": "YOU DIED (and kept coming back, you absolute masochist). ☠️",
    "DARK SOULS: REMASTERED": "YOU DIED (and kept coming back, you absolute masochist). ☠️",
    "ELDEN RING": "You don't have the right, O you don't have the right. 🐢",
    "Garry's Mod": "The game is whatever you want it to be. Usually chaos. 🤡",
    "Left 4 Dead 2": "PILLS HERE! 💊",
    "Portal": "The cake is a lie. It's always been a lie. 🎂",
    "Portal 2": "The cake is still a lie. But the companion cube loves you. ❤️",
    "Minecraft": "Just one more block... *builds entire cathedral* ⛏️",
    "Half-Life 2": "We don't go to Ravenholm. 😰",
    "Among Us": "📮 sus",
    "Deep Rock Galactic": "ROCK AND STONE! ⛏️🍺",
    "Clicker Heroes": "You clicked. And clicked. And clicked. The void clicked back. 🖱️",
    "Hunt: Showdown": "Extract camper or big bounty energy? Either way, your heart rate was 180. 💀",
    "Hunt: Showdown 1896": "Extract camper or big bounty energy? Either way, your heart rate was 180. 💀",
    "The Sims 3": "Removed the pool ladder, didn't you? We know what you did. 🏊",
    "The Sims 4": "Removed the pool ladder, didn't you? We know what you did. 🏊",
    "FTL: Faster Than Light": "Your crew died. Again. In a fire. Again. On sector 7. Again. 🚀🔥",
    "Killing Floor": "LOADS OF MONEY! 💷",
    "Killing Floor 2": "LOADS OF MONEY! 💷",
    "Valheim": "You built a Viking mansion before remembering there's a boss fight. 🏰",
    "Subnautica": "Detecting multiple leviathan class lifeforms. Are you sure whatever you're doing is worth it? 🐙",
    "Hades": "Good shade. 💀",
    "Hades II": "Good shade, again. 💀",
    "Witcher 3: Wild Hunt": "How about a round of Gwent? 🃏",
    "The Witcher 3: Wild Hunt": "How about a round of Gwent? 🃏",
    "Cyberpunk 2077": "Wake up, Samurai. We have a city to burn. 🌆",
    "Hollow Knight": "Shaw! Git gud, but make it adorable. 🪲",
    "S.T.A.L.K.E.R.: Shadow of Chernobyl": "Get out of here, Stalker. ☢️",
    "S.T.A.L.K.E.R. 2: Heart of Chornobyl": "Get out of here, Stalker. ☢️",
    "Satisfactory": "Praise be to FICSIT. The factory must grow (in 3D this time). 🏗️",
    "No Man's Sky": "The redemption arc that gives us all hope. 🌌",
    "Cities: Skylines": "Your traffic management skills are... concerning. 🚗",
    "Cities: Skylines II": "Your traffic management skills are still... concerning. 🚗",
    "Fallout 4": "Another settlement needs your help. I've marked it on your map. 📍",
    "Fallout: New Vegas": "The game was rigged from the start. 🎰",
}


def game_meme(name: str) -> str | None:
    """Return a meme/reference for a specific game, or None."""
    return GAME_MEMES.get(name)


def top_game_roast(name: str, hours: float) -> str:
    days = round(hours / 24, 1)
    meme = game_meme(name)
    meme_line = f"\n\n> *{meme}*" if meme else ""
    if hours > 1000:
        return f"**{hours:,.0f}h** on {name}. That's **{days} days**. At this point it's not a hobby, it's a lifestyle. 🏠{meme_line}"
    elif hours > 500:
        return f"**{hours:,.0f}h** on {name} ({days} days). You could've learned a language. But you didn't. 🎮{meme_line}"
    elif hours > 100:
        return f"**{hours:,.0f}h** on {name}. That's {days} full days. Commitment issues? Not here.{meme_line}"
    else:
        return f"**{hours:,.0f}h** on {name}. A respectable amount. We'll allow it.{meme_line}"


def backlog_roast(count: int) -> str:
    if count > 400:
        return f"**{count}** games with zero hours. That's not a backlog, that's a digital hoard. TLC should make a show about this. 📺"
    elif count > 200:
        return f"**{count}** unplayed games gathering digital dust. That's not a backlog, that's a graveyard. ⚰️"
    elif count > 100:
        return f"**{count}** games you've never touched. Steam sales are a hell of a drug. 💊"
    elif count > 50:
        return f"**{count}** unplayed games. You're collecting them like Pokémon. Gotta buy 'em all."
    else:
        return f"Only **{count}** unplayed games? You're practically a minimalist. 🧘"


def account_age_commentary(years_str: str, member_since: str) -> str:
    years = int(years_str.split()[0])
    if years > 15:
        return f"Member since **{member_since}** ({years_str}). You've been on Steam longer than some of your games have existed. OG status. 🏆"
    elif years > 10:
        return f"Member since **{member_since}** ({years_str}). A seasoned veteran. The scars from early Early Access still sting."
    else:
        return f"Member since **{member_since}** ({years_str}). Still relatively fresh. Give it time."


def genre_commentary(top_genre: str) -> str:
    return f'Your most played genre is **{top_genre}**. We\'re not judging. (We\'re totally judging.) 👀'


# --- Gaming Personality ---

def gaming_personality(stats: dict, df: pd.DataFrame, account_years: int) -> tuple[str, str, str]:
    """Return (title, emoji, description) for the user's gaming personality."""
    top = df.head(1)
    top_hours = float(top["hours"].iloc[0]) if not top.empty else 0
    total_hours = stats["total_hours"]
    pct_played = stats["pct_played"]
    total_games = stats["total_games"]
    unplayed = stats["unplayed"]

    # Check if most hours are in one game
    top_pct = (top_hours / total_hours * 100) if total_hours > 0 else 0

    if top_pct > 50:
        return ("The One-Game Andy", "🎯",
                f"{top_pct:.0f}% of your playtime is in one game. Loyalty or obsession? Yes.")
    elif pct_played > 80 and total_games > 50:
        return ("The Completionist", "🏅",
                f"You've played {pct_played}% of your library. You don't just buy games — you play them. Respect.")
    elif unplayed > 400:
        return ("The Digital Hoarder", "🐉",
                f"{unplayed} unplayed games. You collect games like a dragon hoards gold. Steam sales fear your wallet.")
    elif unplayed > 200:
        return ("The Hoarder", "📦",
                f"{unplayed} games you've never launched. Your library is a museum, and you're the only visitor.")
    elif total_hours > 10000:
        return ("The No-Lifer", "💀",
                f"{stats['total_days']:,.0f} days of pure gaming. Touch grass? Never heard of it.")
    elif total_hours > 5000:
        return ("The Veteran", "⚔️",
                f"{stats['total_hours']:,.0f} hours across {total_games} games. You've seen things. Terrible Early Access things.")
    elif account_years > 15:
        return ("The OG", "👴",
                f"{account_years} years on Steam. You remember when it was just a launcher for Half-Life 2.")
    elif total_games > 500 and pct_played < 50:
        return ("The Collector", "🎪",
                f"{total_games} games, only {pct_played}% played. The thrill is in the buying, not the playing.")
    elif total_games < 20:
        return ("The Minimalist", "🧘",
                f"Only {total_games} games. Quality over quantity. Marie Kondo would be proud.")
    else:
        # Check if playtime is spread thin
        top10_hours = df.head(10)["hours"].sum()
        spread = top10_hours / total_hours if total_hours > 0 else 0
        if spread < 0.5:
            return ("The Dabbler", "🦋",
                    "A little bit of everything, a lot of nothing. Jack of all games, master of none.")
        else:
            return ("The Gamer", "🎮",
                    "A balanced gamer. Not too obsessed, not too casual. The Goldilocks of Steam.")


# --- Platform breakdown ---

def platform_breakdown(df: pd.DataFrame) -> dict[str, float]:
    """Return hours by platform from playtime columns."""
    platforms = {}
    for col, label in [
        ("playtime_windows_forever", "Windows"),
        ("playtime_mac_forever", "Mac"),
        ("playtime_linux_forever", "Linux"),
        ("playtime_deck_forever", "Steam Deck"),
    ]:
        if col in df.columns:
            hours = round(df[col].sum() / 60, 1)
            if hours > 0:
                platforms[label] = hours
    return platforms


# --- Most expensive unplayed game(s) ---

def most_expensive_unplayed(unplayed_df: pd.DataFrame, store_details: dict[int, dict], n: int = 10) -> list[tuple[str, float]]:
    """Find the top N priciest games with 0 hours. Returns list of (name, price) tuples."""
    candidates = []
    for _, row in unplayed_df.iterrows():
        appid = row["appid"]
        if appid in store_details:
            price_data = store_details[appid].get("price_overview")
            if price_data:
                price = price_data.get("final", 0) / 100
                if price > 0:
                    name = store_details[appid].get("name", row["name"])
                    candidates.append((name, price))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:n]


# --- Top games per genre ---

def top_games_per_genre(genre_df: pd.DataFrame, n: int = 3) -> dict[str, list[str]]:
    """Return a dict mapping genre -> list of top N game names (by frequency in that genre)."""
    if genre_df.empty:
        return {}
    result = {}
    for genre, group in genre_df.groupby("genre"):
        top_names = group["name"].value_counts().head(n).index.tolist()
        result[genre] = top_names
    return result


# --- Achievement helpers ---

def recent_achievements(steam_id: str, appids: list[int], get_player_achievements_fn, n: int = 10) -> list[dict]:
    """Find the N most recently unlocked achievements across given games."""
    all_achievements = []
    for appid in appids:
        data = get_player_achievements_fn(steam_id, appid)
        if data and "achievements" in data:
            game_name = data.get("gameName", f"App {appid}")
            for ach in data["achievements"]:
                if ach.get("achieved") and ach.get("unlocktime", 0) > 0:
                    all_achievements.append({
                        "game": game_name,
                        "achievement_name": ach.get("name", ach.get("apiname", "Unknown")),
                        "unlock_date": datetime.fromtimestamp(ach["unlocktime"], tz=timezone.utc).strftime("%Y-%m-%d"),
                        "unlocktime": ach["unlocktime"],
                    })
    all_achievements.sort(key=lambda x: x["unlocktime"], reverse=True)
    return all_achievements[:n]


def rarest_achievements(steam_id: str, appids: list[int], get_player_achievements_fn, get_global_achievement_fn, n: int = 10) -> list[dict]:
    """Find user's rarest unlocked achievements by global unlock percentage."""
    candidates = []
    for appid in appids:
        player_data = get_player_achievements_fn(steam_id, appid)
        if not player_data or "achievements" not in player_data:
            continue
        game_name = player_data.get("gameName", f"App {appid}")
        unlocked = {a.get("apiname", a.get("name", "")) for a in player_data["achievements"] if a.get("achieved")}
        if not unlocked:
            continue
        global_data = get_global_achievement_fn(appid)
        if not global_data:
            continue
        for ach in global_data:
            api_name = ach.get("name", "")
            if api_name in unlocked:
                candidates.append({
                    "game": game_name,
                    "achievement_name": api_name,
                    "global_percent": round(float(ach.get("percent", 100)), 2),
                })
    candidates.sort(key=lambda x: x["global_percent"])
    return candidates[:n]


# --- Head-to-Head Comparison ---

def compare_stats(stats1: dict, stats2: dict, name1: str, name2: str) -> list[dict]:
    """Compare two players' stats and determine winners for each metric."""
    comparisons = [
        ("Total Games", stats1["total_games"], stats2["total_games"], "more", "🎮"),
        ("Games Played", stats1["played"], stats2["played"], "more", "✅"),
        ("% Played", stats1["pct_played"], stats2["pct_played"], "higher", "📊"),
        ("Total Hours", stats1["total_hours"], stats2["total_hours"], "more", "⏱️"),
        ("Unplayed Games", stats1["unplayed"], stats2["unplayed"], "fewer", "🕸️"),
    ]
    results = []
    for label, v1, v2, direction, icon in comparisons:
        if direction == "fewer":
            winner = name1 if v1 < v2 else (name2 if v2 < v1 else "Tie")
        else:
            winner = name1 if v1 > v2 else (name2 if v2 > v1 else "Tie")
        results.append({
            "metric": label, "icon": icon,
            "p1_value": v1, "p2_value": v2,
            "winner": winner, "direction": direction,
        })
    return results


def shared_games(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Find games both players own with hours from each."""
    merged = df1[["appid", "name", "hours"]].merge(
        df2[["appid", "hours"]], on="appid", suffixes=("_p1", "_p2"),
    )
    return merged.sort_values("hours_p1", ascending=False).reset_index(drop=True)


def comparison_commentary(stats1: dict, stats2: dict, name1: str, name2: str) -> str:
    """Generate funny comparison text between two players."""
    lines = []

    if stats1["total_games"] > stats2["total_games"] * 1.5:
        lines.append(f"🐉 **{name1}** is the bigger hoarder with **{stats1['total_games']}** games vs {name2}'s measly {stats2['total_games']}. Someone call TLC.")
    elif stats2["total_games"] > stats1["total_games"] * 1.5:
        lines.append(f"🐉 **{name2}** is the bigger hoarder with **{stats2['total_games']}** games vs {name1}'s measly {stats1['total_games']}. Someone call TLC.")
    else:
        lines.append(f"📦 Both are equally unhinged collectors. **{name1}**: {stats1['total_games']} games, **{name2}**: {stats2['total_games']} games.")

    if stats1["pct_played"] > stats2["pct_played"] + 15:
        lines.append(f"🎮 **{name1}** actually plays their games ({stats1['pct_played']}% played). **{name2}** just collects ({stats2['pct_played']}%). One's a gamer, one's a museum curator.")
    elif stats2["pct_played"] > stats1["pct_played"] + 15:
        lines.append(f"🎮 **{name2}** actually plays their games ({stats2['pct_played']}% played). **{name1}** just collects ({stats1['pct_played']}%). One's a gamer, one's a museum curator.")
    else:
        lines.append(f"📊 Both play about the same percentage of their library. Equally guilty (or innocent).")

    h1, h2 = stats1["total_hours"], stats2["total_hours"]
    if h1 > h2 * 2:
        lines.append(f"💀 **{name1}** has **{h1:,.0f}** hours vs {name2}'s {h2:,.0f}. That's not a comparison, that's a cry for help.")
    elif h2 > h1 * 2:
        lines.append(f"💀 **{name2}** has **{h2:,.0f}** hours vs {name1}'s {h1:,.0f}. That's not a comparison, that's a cry for help.")
    else:
        diff = abs(h1 - h2)
        lines.append(f"⏱️ Only **{diff:,.0f}** hours apart. They're both equally committed to not going outside.")

    b1, b2 = stats1["unplayed"], stats2["unplayed"]
    if b1 > b2:
        lines.append(f"💸 **{name1}** wins the Backlog of Shame™ with **{b1}** unplayed games vs {name2}'s {b2}. Gabe Newell sends his thanks.")
    elif b2 > b1:
        lines.append(f"💸 **{name2}** wins the Backlog of Shame™ with **{b2}** unplayed games vs {name1}'s {b1}. Gabe Newell sends his thanks.")

    return "\n\n".join(lines)


def estimate_account_value(store_details: dict[int, dict]) -> dict:
    """Estimate total account value from store price data."""
    total_value = 0.0
    total_priced = 0
    free_games = 0
    most_expensive = ("", 0.0)
    for appid, data in store_details.items():
        price_data = data.get("price_overview")
        if price_data:
            price = price_data.get("final", 0) / 100
            if price > 0:
                total_value += price
                total_priced += 1
                if price > most_expensive[1]:
                    most_expensive = (data.get("name", "Unknown"), price)
            else:
                free_games += 1
        elif data.get("is_free"):
            free_games += 1
    return {
        "total_value": round(total_value, 2),
        "total_games_priced": total_priced,
        "free_games": free_games,
        "most_expensive": most_expensive,
        "avg_price": round(total_value / total_priced, 2) if total_priced else 0.0,
    }


def perfect_games(ach_stats: list[dict]) -> list[dict]:
    """Filter achievement stats to games with 100% completion."""
    return [
        {"name": a["name"], "total": a["total"], "appid": a["appid"]}
        for a in ach_stats
        if a.get("pct") == 100.0 and a.get("total", 0) > 0
    ]


def genre_personality_tags(genre_df: pd.DataFrame, n: int = 5) -> list[str]:
    """Map top N genres to fun personality labels."""
    if genre_df.empty:
        return []
    genre_map = {
        "Action": "Adrenaline Junkie",
        "RPG": "RPG Addict",
        "Strategy": "Armchair General",
        "Simulation": "Virtual Life Enthusiast",
        "Adventure": "Digital Explorer",
        "Indie": "Indie Connoisseur",
        "Casual": "Casual King",
        "Sports": "Virtual Athlete",
        "Racing": "Speed Demon",
        "Puzzle": "Brain Teaser",
        "Horror": "Thrill Seeker",
        "FPS": "FPS Sweat",
        "Shooter": "FPS Sweat",
        "Multiplayer": "Social Gamer",
        "Free to Play": "F2P Warrior",
    }
    top_genres = genre_df["genre"].value_counts().head(n).index.tolist()
    return [genre_map.get(g, f"{g} Fan") for g in top_genres]


def comparison_personality(p1_title: str, p2_title: str, name1: str, name2: str) -> str:
    """Commentary on the personality matchup."""
    if p1_title == p2_title:
        return f"🤝 **Same energy!** Both {name1} and {name2} are **{p1_title}**. Either soulmates or equally concerning."
    combos = {
        ("The Digital Hoarder", "The Completionist"): "One buys everything, the other actually plays everything. Together they'd be unstoppable.",
        ("The Completionist", "The Digital Hoarder"): "One buys everything, the other actually plays everything. Together they'd be unstoppable.",
        ("The One-Game Andy", "The Dabbler"): "One commits too hard, the other can't commit at all. Classic.",
        ("The Dabbler", "The One-Game Andy"): "One commits too hard, the other can't commit at all. Classic.",
        ("The No-Lifer", "The Minimalist"): "The no-lifer and the minimalist walk into a bar. Only one leaves... because the other is still gaming.",
        ("The Minimalist", "The No-Lifer"): "The no-lifer and the minimalist walk into a bar. Only one leaves... because the other is still gaming.",
    }
    specific = combos.get((p1_title, p2_title))
    if specific:
        return f"⚡ **{name1}** ({p1_title}) vs **{name2}** ({p2_title}): {specific}"
    return f"⚡ **{name1}** is **{p1_title}** while **{name2}** is **{p2_title}**. Different vibes, same addiction."


# --- Feature 5: Random Game Picker ---

import random


def random_game_reasons() -> list[str]:
    """Fun reason templates for picking a random game."""
    return [
        "You bought it, might as well try it. 🤷",
        "It's been sitting in your library, lonely and neglected. Give it love. 💔",
        "Your wallet died for this game. Honor its sacrifice. 💀",
        "Steam sale impulse buy? Time to face the consequences. 🛒",
        "This game has been gathering digital dust since purchase day. ☁️",
        "You scrolled past it 400 times. Tonight, it scrolls back. 👁️",
        "Gabe Newell personally requests you play this one. (Not really, but still.) 🧔",
        "It's been in your library longer than some of your friendships. ⏳",
        "Random number generator says this one. Who are you to argue with math? 🎲",
        "Your backlog isn't going to clear itself. Start here. 📋",
    ]


def pick_random_game(df: pd.DataFrame, genre_df: pd.DataFrame = None, preferred_genres: list[str] = None) -> dict:
    """Pick a random unplayed game, optionally weighted toward preferred genres.

    Returns {name, appid, reason} or empty dict if no unplayed games.
    """
    unplayed = df[df["hours"] == 0].copy()
    if unplayed.empty:
        return {}

    reasons = random_game_reasons()

    # If genre info provided, try to weight toward preferred genres
    if genre_df is not None and preferred_genres and not genre_df.empty:
        genre_appids = set(genre_df[genre_df["genre"].isin(preferred_genres)]["appid"].unique())
        matching = unplayed[unplayed["appid"].isin(genre_appids)]
        if not matching.empty and random.random() < 0.6:
            row = matching.sample(1).iloc[0]
            matched_genre = [g for g in preferred_genres if row["appid"] in set(genre_df[genre_df["genre"] == g]["appid"])]
            genre_name = matched_genre[0] if matched_genre else preferred_genres[0]
            return {
                "name": row["name"],
                "appid": int(row["appid"]),
                "reason": f"Matches your favorite genre: **{genre_name}**! 🎯",
            }

    row = unplayed.sample(1).iloc[0]
    return {
        "name": row["name"],
        "appid": int(row["appid"]),
        "reason": random.choice(reasons),
    }


# --- Feature 6: Streak Tracker & Game Timeline ---

def calculate_streak(df: pd.DataFrame) -> dict:
    """Calculate consecutive-day gaming streak from rtime_last_played.

    Returns {current_streak, last_played_date, most_recent_game}.
    """
    if "rtime_last_played" not in df.columns:
        return {"current_streak": 0, "last_played_date": "Unknown", "most_recent_game": "Unknown"}

    played = df[df["rtime_last_played"] > 0].copy()
    if played.empty:
        return {"current_streak": 0, "last_played_date": "Unknown", "most_recent_game": "Unknown"}

    played["last_played_dt"] = pd.to_datetime(played["rtime_last_played"], unit="s", utc=True)
    played["last_played_day"] = played["last_played_dt"].dt.date
    played = played.sort_values("rtime_last_played", ascending=False)

    most_recent_game = played.iloc[0]["name"]
    last_played_date = played.iloc[0]["last_played_dt"].strftime("%B %d, %Y")

    # Get unique days played (sorted descending)
    unique_days = sorted(played["last_played_day"].unique(), reverse=True)

    today = datetime.now(timezone.utc).date()
    # Streak must start from today or yesterday
    if unique_days[0] < today - pd.Timedelta(days=1):
        return {"current_streak": 0, "last_played_date": last_played_date, "most_recent_game": most_recent_game}

    streak = 1
    for i in range(1, len(unique_days)):
        expected = unique_days[i - 1] - pd.Timedelta(days=1)
        if unique_days[i] == expected:
            streak += 1
        else:
            break

    return {"current_streak": streak, "last_played_date": last_played_date, "most_recent_game": most_recent_game}


def game_timeline(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Create a timeline of recently played games using rtime_last_played.

    Returns DataFrame with [name, last_played_date, hours] sorted by most recent.
    """
    if "rtime_last_played" not in df.columns:
        return pd.DataFrame(columns=["name", "last_played_date", "hours"])

    played = df[df["rtime_last_played"] > 0].copy()
    if played.empty:
        return pd.DataFrame(columns=["name", "last_played_date", "hours"])

    played["last_played_date"] = pd.to_datetime(played["rtime_last_played"], unit="s", utc=True).dt.strftime("%Y-%m-%d")
    played = played.sort_values("rtime_last_played", ascending=False).head(n)
    return played[["name", "last_played_date", "hours"]].reset_index(drop=True)
