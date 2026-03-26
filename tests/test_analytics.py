"""Unit tests for analytics module."""

import pytest
from src.analytics import (
    build_games_df, key_stats, top_games, unplayed_games,
    cost_per_hour, account_age_str, backlog_roast, stats_commentary,
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
