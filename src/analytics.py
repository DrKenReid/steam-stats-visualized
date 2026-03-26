"""Data processing, metrics, and commentary generation."""

from datetime import datetime, timezone
import pandas as pd


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


# --- Most expensive unplayed game ---

def most_expensive_unplayed(unplayed_df: pd.DataFrame, store_details: dict[int, dict]) -> tuple[str, float] | None:
    """Find the priciest game with 0 hours."""
    most_expensive = None
    max_price = 0
    for _, row in unplayed_df.iterrows():
        appid = row["appid"]
        if appid in store_details:
            price_data = store_details[appid].get("price_overview")
            if price_data:
                price = price_data.get("final", 0) / 100
                if price > max_price:
                    max_price = price
                    most_expensive = store_details[appid].get("name", row["name"])
    if most_expensive and max_price > 0:
        return (most_expensive, max_price)
    return None
