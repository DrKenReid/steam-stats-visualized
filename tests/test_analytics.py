"""Unit tests for analytics module."""

import pytest
from src.analytics import (
    build_games_df, key_stats, top_games, unplayed_games,
    cost_per_hour, account_age_str, backlog_roast, stats_commentary,
    compare_stats, shared_games, comparison_commentary, comparison_personality,
    estimate_account_value, perfect_games, genre_personality_tags,
)


def _make_games(n_played=5, n_unplayed=3):
    games = []
    for i in range(n_played):
        games.append({"appid": i, "name": f"Game {i}", "playtime_forever": (i + 1) * 120})
    for i in range(n_unplayed):
        games.append({"appid": 100 + i, "name": f"Unplayed {i}", "playtime_forever": 0})
    return games


class TestBuildGamesDF:
    def test_hours_calculated(self):
        df = build_games_df(_make_games())
        assert "hours" in df.columns
        assert df["hours"].max() == 10.0  # 600 min / 60

    def test_sorted_desc(self):
        df = build_games_df(_make_games())
        assert df["hours"].is_monotonic_decreasing


class TestKeyStats:
    def test_counts(self):
        df = build_games_df(_make_games(5, 3))
        stats = key_stats(df)
        assert stats["total_games"] == 8
        assert stats["played"] == 5
        assert stats["unplayed"] == 3
        assert stats["pct_played"] == 62.5

    def test_total_hours(self):
        df = build_games_df(_make_games(3, 0))
        stats = key_stats(df)
        # 120+240+360 = 720 min = 12h
        assert stats["total_hours"] == 12.0


class TestTopGames:
    def test_returns_n(self):
        df = build_games_df(_make_games(10, 5))
        assert len(top_games(df, 5)) == 5


class TestUnplayed:
    def test_only_zero(self):
        df = build_games_df(_make_games(3, 7))
        assert len(unplayed_games(df)) == 7


class TestCostPerHour:
    def test_basic(self):
        import pandas as pd
        store = {
            1: {"name": "Game A", "price_overview": {"final": 1999}},
            2: {"name": "Game B", "price_overview": {"final": 999}},
        }
        df = pd.DataFrame([
            {"appid": 1, "hours": 100.0},
            {"appid": 2, "hours": 1.0},
        ])
        result = cost_per_hour(store, df)
        assert len(result) == 2
        assert result.iloc[0]["cost_per_hour"] < result.iloc[1]["cost_per_hour"]


class TestCommentary:
    def test_backlog_roast_high(self):
        assert "graveyard" in backlog_roast(250).lower() or "dust" in backlog_roast(250).lower()

    def test_stats_commentary_contains_numbers(self):
        stats = {"total_games": 100, "played": 30, "unplayed": 70, "pct_played": 30.0, "total_hours": 500, "total_days": 20.8}
        text = stats_commentary(stats)
        assert "100" in text
        assert "30" in text


class TestAccountAge:
    def test_format(self):
        years, since = account_age_str(1199145600)  # Jan 1, 2008
        assert "2008" in since
        assert "year" in years.lower()


# --- Comparison Tests ---

class TestCompareStats:
    def _stats(self, total=100, played=50, hours=500):
        return {
            "total_games": total, "played": played, "unplayed": total - played,
            "pct_played": round(100 * played / total, 1) if total else 0,
            "total_hours": hours, "total_days": round(hours / 24, 1),
        }

    def test_winners_determined(self):
        s1 = self._stats(total=200, played=100, hours=1000)
        s2 = self._stats(total=100, played=80, hours=500)
        results = compare_stats(s1, s2, "Alice", "Bob")
        assert len(results) == 5
        # Alice has more total games
        total_games_row = [r for r in results if r["metric"] == "Total Games"][0]
        assert total_games_row["winner"] == "Alice"

    def test_tie(self):
        s1 = self._stats(total=100, played=50, hours=500)
        s2 = self._stats(total=100, played=50, hours=500)
        results = compare_stats(s1, s2, "Alice", "Bob")
        for r in results:
            assert r["winner"] == "Tie"

    def test_unplayed_fewer_wins(self):
        s1 = self._stats(total=100, played=80, hours=500)  # 20 unplayed
        s2 = self._stats(total=100, played=50, hours=500)  # 50 unplayed
        results = compare_stats(s1, s2, "Alice", "Bob")
        unplayed_row = [r for r in results if r["metric"] == "Unplayed Games"][0]
        assert unplayed_row["winner"] == "Alice"  # fewer unplayed wins


class TestSharedGames:
    def test_finds_shared(self):
        import pandas as pd
        df1 = build_games_df([
            {"appid": 1, "name": "Game A", "playtime_forever": 600},
            {"appid": 2, "name": "Game B", "playtime_forever": 300},
            {"appid": 3, "name": "Game C", "playtime_forever": 120},
        ])
        df2 = build_games_df([
            {"appid": 1, "name": "Game A", "playtime_forever": 1200},
            {"appid": 4, "name": "Game D", "playtime_forever": 60},
            {"appid": 2, "name": "Game B", "playtime_forever": 0},
        ])
        shared = shared_games(df1, df2)
        assert len(shared) == 2
        assert set(shared["name"].tolist()) == {"Game A", "Game B"}
        # Check both hours columns exist
        assert "hours_p1" in shared.columns
        assert "hours_p2" in shared.columns

    def test_no_shared(self):
        df1 = build_games_df([{"appid": 1, "name": "A", "playtime_forever": 60}])
        df2 = build_games_df([{"appid": 2, "name": "B", "playtime_forever": 60}])
        shared = shared_games(df1, df2)
        assert len(shared) == 0


class TestComparisonCommentary:
    def test_returns_string(self):
        s1 = {"total_games": 500, "played": 100, "unplayed": 400, "pct_played": 20.0, "total_hours": 5000, "total_days": 208.3}
        s2 = {"total_games": 50, "played": 40, "unplayed": 10, "pct_played": 80.0, "total_hours": 200, "total_days": 8.3}
        text = comparison_commentary(s1, s2, "Alice", "Bob")
        assert isinstance(text, str)
        assert "Alice" in text
        assert "Bob" in text

    def test_hoarder_detected(self):
        s1 = {"total_games": 500, "played": 100, "unplayed": 400, "pct_played": 20.0, "total_hours": 5000, "total_days": 208.3}
        s2 = {"total_games": 50, "played": 40, "unplayed": 10, "pct_played": 80.0, "total_hours": 200, "total_days": 8.3}
        text = comparison_commentary(s1, s2, "Alice", "Bob")
        assert "hoarder" in text.lower()


class TestComparisonPersonality:
    def test_same_personality(self):
        text = comparison_personality("The Hoarder", "The Hoarder", "A", "B")
        assert "Same energy" in text

    def test_different_personality(self):
        text = comparison_personality("The Completionist", "The Digital Hoarder", "A", "B")
        assert "A" in text and "B" in text


# --- Feature 5: Random Game Picker Tests ---

from src.analytics import pick_random_game, random_game_reasons


class TestRandomGameReasons:
    def test_returns_list(self):
        reasons = random_game_reasons()
        assert isinstance(reasons, list)
        assert len(reasons) > 0

    def test_all_strings(self):
        for r in random_game_reasons():
            assert isinstance(r, str)


class TestPickRandomGame:
    def test_picks_unplayed(self):
        df = build_games_df(_make_games(3, 5))
        result = pick_random_game(df)
        assert result
        assert "name" in result
        assert "appid" in result
        assert "reason" in result
        assert result["name"].startswith("Unplayed")

    def test_no_unplayed_returns_empty(self):
        df = build_games_df(_make_games(5, 0))
        result = pick_random_game(df)
        assert result == {}

    def test_with_genre_weighting(self):
        import pandas as pd
        df = build_games_df(_make_games(2, 3))
        genre_df = pd.DataFrame([
            {"appid": 100, "name": "Unplayed 0", "genre": "RPG"},
            {"appid": 101, "name": "Unplayed 1", "genre": "Action"},
        ])
        # Should not crash; result should be valid
        result = pick_random_game(df, genre_df=genre_df, preferred_genres=["RPG"])
        assert result
        assert "name" in result


# --- Feature 6: Streak & Timeline Tests ---

from src.analytics import calculate_streak, game_timeline


class TestCalculateStreak:
    def test_no_rtime_column(self):
        df = build_games_df(_make_games(3, 0))
        result = calculate_streak(df)
        assert result["current_streak"] == 0

    def test_with_rtime(self):
        import time
        now = int(time.time())
        games = [
            {"appid": 1, "name": "Today Game", "playtime_forever": 120, "rtime_last_played": now},
            {"appid": 2, "name": "Yesterday Game", "playtime_forever": 60, "rtime_last_played": now - 86400},
            {"appid": 3, "name": "Old Game", "playtime_forever": 60, "rtime_last_played": now - 86400 * 10},
        ]
        df = build_games_df(games)
        df["rtime_last_played"] = [now, now - 86400, now - 86400 * 10]
        result = calculate_streak(df)
        assert result["current_streak"] >= 1
        assert result["most_recent_game"] == "Today Game"

    def test_no_played_games(self):
        games = [{"appid": 1, "name": "G", "playtime_forever": 0, "rtime_last_played": 0}]
        df = build_games_df(games)
        df["rtime_last_played"] = [0]
        result = calculate_streak(df)
        assert result["current_streak"] == 0


class TestGameTimeline:
    def test_no_rtime_column(self):
        df = build_games_df(_make_games(3, 0))
        result = game_timeline(df)
        assert result.empty

    def test_returns_correct_columns(self):
        import time
        now = int(time.time())
        games = [
            {"appid": 1, "name": "A", "playtime_forever": 120, "rtime_last_played": now},
            {"appid": 2, "name": "B", "playtime_forever": 60, "rtime_last_played": now - 86400},
        ]
        df = build_games_df(games)
        df["rtime_last_played"] = [now, now - 86400]
        result = game_timeline(df, n=5)
        assert list(result.columns) == ["name", "last_played_date", "hours"]
        assert len(result) == 2
        assert result.iloc[0]["name"] == "A"  # most recent first


class TestEstimateAccountValue:
    def test_basic(self):
        store = {
            1: {"name": "Game A", "price_overview": {"final": 1999}},
            2: {"name": "Game B", "price_overview": {"final": 999}},
            3: {"name": "Free Game", "is_free": True},
        }
        result = estimate_account_value(store)
        assert result["total_value"] == 29.98
        assert result["total_games_priced"] == 2
        assert result["free_games"] == 1
        assert result["most_expensive"] == ("Game A", 19.99)
        assert result["avg_price"] == 14.99

    def test_empty(self):
        result = estimate_account_value({})
        assert result["total_value"] == 0.0
        assert result["total_games_priced"] == 0
        assert result["avg_price"] == 0.0

    def test_free_with_zero_price(self):
        store = {1: {"name": "F2P", "price_overview": {"final": 0}}}
        result = estimate_account_value(store)
        assert result["free_games"] == 1
        assert result["total_games_priced"] == 0


class TestPerfectGames:
    def test_finds_perfect(self):
        ach_stats = [
            {"name": "Game A", "appid": 1, "achieved": 10, "total": 10, "pct": 100.0},
            {"name": "Game B", "appid": 2, "achieved": 5, "total": 10, "pct": 50.0},
            {"name": "Game C", "appid": 3, "achieved": 20, "total": 20, "pct": 100.0},
        ]
        result = perfect_games(ach_stats)
        assert len(result) == 2
        assert result[0]["name"] == "Game A"
        assert result[1]["name"] == "Game C"

    def test_none_perfect(self):
        ach_stats = [
            {"name": "Game A", "appid": 1, "achieved": 9, "total": 10, "pct": 90.0},
        ]
        assert perfect_games(ach_stats) == []

    def test_empty(self):
        assert perfect_games([]) == []


class TestGenrePersonalityTags:
    def test_maps_known_genres(self):
        import pandas as pd
        genre_df = pd.DataFrame([
            {"appid": 1, "name": "G1", "genre": "Action"},
            {"appid": 2, "name": "G2", "genre": "Action"},
            {"appid": 3, "name": "G3", "genre": "RPG"},
            {"appid": 4, "name": "G4", "genre": "Strategy"},
        ])
        tags = genre_personality_tags(genre_df, n=3)
        assert tags == ["Adrenaline Junkie", "RPG Addict", "Armchair General"]

    def test_unknown_genre_fallback(self):
        import pandas as pd
        genre_df = pd.DataFrame([
            {"appid": 1, "name": "G1", "genre": "Weirdcore"},
        ])
        tags = genre_personality_tags(genre_df, n=1)
        assert tags == ["Weirdcore Fan"]

    def test_empty(self):
        import pandas as pd
        assert genre_personality_tags(pd.DataFrame(columns=["appid", "name", "genre"])) == []
