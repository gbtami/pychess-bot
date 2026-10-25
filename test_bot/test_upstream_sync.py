"""Check upstream fixes at the PyChess variant and matchmaking boundaries."""

import inspect
import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from lib import config, engine_wrapper, lichess_bot, model
from lib.lichess_types import CONFIG_DICT_TYPE, EventType
from lib.matchmaking import Matchmaking


@pytest.fixture
def matchmaker() -> Matchmaking:
    """Enable immediate matchmaking without contacting the server."""
    raw_config = {
        "challenge": {"variants": ["xiangqi"]},
        "matchmaking": {"allow_matchmaking": True, "allow_during_games": True, "challenge_timeout": 0},
    }
    config.insert_default_values(raw_config)
    return Matchmaking(Mock(), config.Configuration(raw_config), {"username": "bot", "perfs": {}})


def test_pending_matchmaking_challenge_reserves_a_bot_slot(matchmaker: Matchmaking) -> None:
    """Even a newly discovered bot must occupy a slot before its events arrive."""
    active_games: dict[str, str] = {}
    with (patch.object(model.Player, "bot_names", set()),
          patch.object(matchmaker, "choose_opponent", return_value=("newbot", 60, 1, 0, "xiangqi", "casual")),
          patch.object(matchmaker, "create_challenge", return_value="pending"),
          patch.object(matchmaker, "should_create_challenge", return_value=True)):
        matchmaker.challenge(active_games, [], max_bot_games=1)

        assert active_games == {"pending": "newbot"}
        assert model.Player.count_bot_games(active_games) == 1

        # The reservation must prevent another challenge even after the wait timer expires.
        matchmaker.last_challenge_created_delay.starting_time -= 1000
        with patch.object(matchmaker, "create_challenge") as create_challenge:
            matchmaker.challenge(active_games, [], max_bot_games=1)
        create_challenge.assert_not_called()


def test_expired_matchmaking_challenge_releases_its_slot(matchmaker: Matchmaking) -> None:
    """Expiring a challenge must leave other games alone."""
    matchmaker.challenge_id = "pending"
    matchmaker.last_challenge_created_delay.starting_time -= 100
    active_games = {"pending": "newbot", "other": "human"}

    assert matchmaker.should_create_challenge(active_games)

    assert active_games == {"other": "human"}
    assert matchmaker.challenge_id == ""
    matchmaker.li.cancel.assert_called_once_with("pending")  # type: ignore[attr-defined]


def test_accepted_matchmaking_challenge_releases_its_reservation(matchmaker: Matchmaking) -> None:
    """Acceptance releases the reservation before the game starts."""
    matchmaker.challenge_id = "pending"
    active_games = {"pending": "newbot", "other": "human"}
    event: EventType = {"type": "gameStart", "game": {"id": "pending"}}

    matchmaker.accepted_challenge(event, active_games)

    assert active_games == {"other": "human"}
    assert matchmaker.challenge_id == ""


@pytest.mark.parametrize("variant", ["Standard", "xiangqi", "alice"])
@pytest.mark.parametrize("active", [True, False])
def test_game_stream_end_only_finalizes_inactive_games(variant: str, active: bool) -> None:
    """Dropped variant streams must reach the retry decorator without freeing the game slot."""
    raw_config: CONFIG_DICT_TYPE = {}
    config.insert_default_values(raw_config)
    cfg = config.Configuration(raw_config)
    initial_state = {
        "id": "game", "variant": {"name": variant}, "createdAt": 0,
        "white": {"name": "opponent"}, "black": {"name": "bot"},
        "initialFen": "startpos", "speed": "blitz",
        "state": {"type": "gameState", "status": "started", "moves": "",
                  "wtime": 60000, "btime": 60000, "winc": 1000, "binc": 1000},
    }
    li = Mock(baseUrl="https://www.pychess.org/")
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_lines.return_value = iter([json.dumps(initial_state).encode()])
    li.get_game_stream.return_value = response
    engine = MagicMock()

    with (patch.object(lichess_bot, "thread_logging_configurer"),
          patch.object(engine_wrapper, "create_engine", return_value=engine),
          patch.object(lichess_bot, "game_is_active", return_value=active),
          patch.object(lichess_bot, "try_get_pgn_game_record") as get_pgn,
          patch.object(lichess_bot, "final_queue_entries") as finalize,
          patch.object(lichess_bot, "delete_takeback_record"),
          patch("lib.lichess_bot.stop.terminated", False),
          patch("lib.lichess_bot.stop.force_quit", False)):
        # Exercise one attempt directly, without waiting for backoff between retries.
        play_once = inspect.unwrap(lichess_bot.play_game)
        args: tuple[object, ...] = (li, "game", Mock(), {"username": "bot"}, cfg, [], Mock(), Mock(), Mock())
        if active:
            with pytest.raises(StopIteration):
                play_once(*args)
            get_pgn.assert_not_called()
            finalize.assert_not_called()
        else:
            play_once(*args)
            get_pgn.assert_called_once()
            finalize.assert_called_once()

    engine.__exit__.assert_called_once()
