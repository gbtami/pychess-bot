"""Check public UCI identity capture and the backwards-compatible BOT handshake."""

import argparse
import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from lib import config, engine_wrapper, lichess, lichess_bot
from lib.lichess import stop
from lib.variants import BOT_CAPABILITIES_MAX_BYTES, bot_capabilities_header


def test_capabilities_advertise_only_public_engine_identity() -> None:
    """Only name and author belong in the public profile handshake."""
    payload = json.loads(bot_capabilities_header(["standard"], {
        "name": " Alice-Stockfish  1.0 ",
        "author": "Belzedar94\nand the Stockfish developers (see AUTHORS file)",
        "path": "/private/engine/path",
    }))

    assert payload["version"] == 1
    assert payload["variants"] == ["standard"]
    assert payload["engine"] == {
        "name": "Alice-Stockfish 1.0",
        "author": "Belzedar94 and the Stockfish developers (see AUTHORS file)",
    }


@pytest.mark.parametrize("identity", [None, {}, {"name": "   ", "author": "Author"}])
def test_missing_engine_identity_preserves_existing_capabilities(identity: dict[str, str] | None) -> None:
    """Existing clients and engines without a name keep the same payload."""
    assert json.loads(bot_capabilities_header(["chess"], identity)) == {
        "version": 1, "variants": ["standard"],
    }


def test_engine_identity_is_bounded_and_header_safe() -> None:
    """Long Unicode names and multiline credits must fit in HTTP headers."""
    header = bot_capabilities_header(["standard"], {"name": "♔" * 300, "author": "♕" * 500})
    engine = json.loads(header)["engine"]

    header.encode("ascii")
    assert len(header.encode()) <= BOT_CAPABILITIES_MAX_BYTES
    assert len(engine["name"]) == 128
    assert len(engine["author"]) == 256


def test_engine_identity_does_not_crowd_out_variant_capabilities() -> None:
    """Drop optional profile details when a large variant list fills the header."""
    variants = [f"variant{index}" for index in range(350)]
    identity = {"name": "♔" * 128, "author": "♕" * 256}
    assert "engine" not in json.loads(bot_capabilities_header(variants, identity))
    assert bot_capabilities_header(variants, identity) == bot_capabilities_header(variants)


@pytest.mark.parametrize("protocol", ["uci", "xboard", "homemade"])
def test_startup_captures_uci_identity_from_the_existing_engine_check(protocol: str) -> None:
    """Reuse the startup handshake without starting a separate metadata engine."""
    with open("config.yml.default") as file:
        raw_config = yaml.safe_load(file)
    raw_config["engine"]["protocol"] = protocol
    config.insert_default_values(raw_config)
    cfg = config.Configuration(raw_config)
    engine = MagicMock()
    engine.__enter__.return_value = engine
    identity = {"name": "Alice-Stockfish 1.0", "author": "Engine authors"}
    engine.engine.id = identity
    li = Mock(spec=lichess.Lichess)
    li.get_profile.return_value = {"id": "bot", "username": "bot", "title": "BOT"}
    args = argparse.Namespace(v=False, config=None, logfile=None, disable_auto_logging=True, u=False)

    with (patch("lib.lichess_bot.argparse.ArgumentParser.parse_args", return_value=args),
          patch.object(lichess_bot, "load_config", return_value=cfg),
          patch.object(lichess_bot, "logging_configurer"),
          patch.object(lichess_bot, "check_python_version"),
          patch.object(lichess_bot, "log_python_and_libraries"),
          patch.object(engine_wrapper, "create_engine", return_value=engine) as create_engine,
          patch.object(lichess, "Lichess", return_value=li),
          patch.object(lichess_bot, "start") as start):
        lichess_bot.start_lichess_bot()

    assert li.engine_info == (identity if protocol == "uci" else {})
    create_engine.assert_called_once_with(cfg)
    start.assert_called_once()


def test_event_stream_reconnects_with_engine_identity() -> None:
    """The control-stream process carries the captured identity in its handshake."""
    li = Mock(spec=lichess.Lichess)
    li.engine_info = {"name": "Alice-Stockfish 1.0", "author": "Engine authors"}
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_lines.return_value = iter([])

    def connect(_capabilities: str) -> MagicMock:
        stop.terminated = True
        return response

    li.get_event_stream.side_effect = connect
    queue = Mock()
    with patch.object(stop, "terminated", False):
        lichess_bot.watch_control_stream(queue, li, ["alice"])

    payload = json.loads(li.get_event_stream.call_args.args[0])
    assert payload["engine"] == li.engine_info
    assert payload["variants"] == ["alice"]
