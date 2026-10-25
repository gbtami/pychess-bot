"""Check recovery after PyChess server restarts without real network calls or delays."""

from http.client import RemoteDisconnected
from unittest.mock import call, patch

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError, ReadTimeout
from requests.models import Response

from lib import lichess_bot
from lib.lichess import stop


def _unavailable_response() -> HTTPError:
    """Represent a temporary deployment response from the server or router."""
    response = Response()
    response.status_code = 503
    return HTTPError(response=response)


@pytest.mark.parametrize("error", [
    ReadTimeout("Server is restarting"),
    RequestsConnectionError("Server is restarting"),
    RemoteDisconnected("Server is restarting"),
    _unavailable_response(),
])
def test_startup_recovers_after_two_minutes_of_server_downtime(error: Exception) -> None:
    """Temporary network failures must not stop the bot after a long deployment."""
    failed_attempts = 12
    with (patch.object(stop, "restart", True),
          patch.object(stop, "terminated", False),
          patch.object(stop, "force_quit", False),
          patch("lib.lichess_bot.multiprocessing.set_start_method"),
          patch.object(lichess_bot, "start_lichess_bot", side_effect=[error] * failed_attempts + [None]) as startup,
          patch("lib.lichess_bot.time.sleep") as sleep,
          patch.object(lichess_bot.logger, "exception")):
        lichess_bot.start_program()

    assert startup.call_count == failed_attempts + 1
    assert sleep.call_args_list == [call(10)] * failed_attempts + [call(0)]


@pytest.mark.parametrize("stop_flag", ["terminated", "force_quit"])
def test_shutdown_during_server_downtime_stops_reconnecting(stop_flag: str) -> None:
    """A requested shutdown must end the restart cycle without another delay."""
    def fail_and_stop() -> None:
        setattr(stop, stop_flag, True)
        raise RemoteDisconnected("Server is restarting")

    with (patch.object(stop, "restart", True),
          patch.object(stop, "terminated", False),
          patch.object(stop, "force_quit", False),
          patch("lib.lichess_bot.multiprocessing.set_start_method"),
          patch.object(lichess_bot, "start_lichess_bot", side_effect=fail_and_stop) as startup,
          patch("lib.lichess_bot.time.sleep") as sleep,
          patch.object(lichess_bot.logger, "exception")):
        lichess_bot.start_program()

    startup.assert_called_once()
    sleep.assert_not_called()


def test_invalid_configuration_is_not_retried_as_server_downtime() -> None:
    """Long server-restart tolerance must not hide configuration errors."""
    with (patch.object(stop, "restart", True),
          patch.object(stop, "terminated", False),
          patch.object(stop, "force_quit", False),
          patch("lib.lichess_bot.multiprocessing.set_start_method"),
          patch.object(lichess_bot, "start_lichess_bot", side_effect=RuntimeError("Invalid configuration")) as startup,
          patch("lib.lichess_bot.time.sleep") as sleep,
          patch.object(lichess_bot.logger, "exception") as log_error):
        lichess_bot.start_program()

    startup.assert_called_once()
    sleep.assert_not_called()
    log_error.assert_called_once_with("Quitting lichess-bot due to an error:")
