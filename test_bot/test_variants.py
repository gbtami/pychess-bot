"""Tests for the pychess variant board adapter."""

from typing import cast

from lib.variants import FairyBoard, FairyMove, fairy_board


def _board(variant: str) -> FairyBoard:
    """Create a typed fairy board for tests."""
    return cast("FairyBoard", fairy_board(variant)())


def test_variant_name_normalization() -> None:
    """Pychess variant names should map to pyffish and CECP names."""
    three_check = _board("ThreeCheck")
    racing_kings = _board("Racing Kings")
    king_of_the_hill = _board("King of the Hill")
    chess960 = _board("Chess960")

    assert three_check.uci_variant == "3check"
    assert three_check.xboard_variant == "3check"
    assert racing_kings.uci_variant == "racingkings"
    assert racing_kings.xboard_variant == "racingkings"
    assert king_of_the_hill.uci_variant == "kingofthehill"
    assert king_of_the_hill.xboard_variant == "kingofthehill"
    assert chess960.uci_variant == "chess"
    assert chess960.xboard_variant == "fischerandom"
    assert chess960.chess960 is True


def test_xboard_xiangqi_accepts_cecp_zero_based_ranks() -> None:
    """CECP Xiangqi coordinates should use ranks 0..9 at the engine boundary."""
    board = _board("xiangqi")

    assert board.parse_xboard("b2b9").uci() == "b3b10"
    assert board.xboard(FairyMove("b3b10")) == "b2b9"


def test_xboard_xiangqi_still_accepts_pyffish_style_coordinates() -> None:
    """Existing engines that emit pyffish-style Xiangqi coordinates should keep working."""
    board = _board("xiangqi")

    assert board.parse_xboard("b3b10").uci() == "b3b10"
    assert board.parse_xboard("Cxb10").uci() == "b3b10"


def test_xboard_xiangqi_accepts_cecp_zero_based_san_fallback() -> None:
    """SAN fallback should also try CECP rank conversion on 10-rank boards."""
    board = _board("xiangqi")

    assert board.parse_xboard("Cxb9").uci() == "b3b10"


def test_xboard_grand_chess_uses_dynamic_ten_rank_conversion() -> None:
    """The CECP rank rule should be derived from board height, not hardcoded variants."""
    board = _board("grand")

    assert board.parse_xboard("a2a4").uci() == "a3a5"
    assert board.xboard(FairyMove("a3a5")) == "a2a4"


def test_xboard_asean_does_not_shift_ranks() -> None:
    """Eight-rank variants should use pyffish coordinates unchanged for CECP."""
    board = _board("asean")

    assert board.parse_xboard("e3e4").uci() == "e3e4"
    assert board.xboard(FairyMove("e3e4")) == "e3e4"


def test_xboard_san_fallback_for_asean() -> None:
    """SAN fallback should map engine SAN to pychess coordinate moves."""
    board = _board("asean")

    assert board.parse_xboard("e4").uci() == "e3e4"
    assert board.parse_xboard("Nd2").uci() == "b1d2"


def test_drop_move_case_restoration() -> None:
    """Drop moves lowercased by python-chess should be restored for pyffish."""
    board = _board("sittuyin")

    assert board.parse_uci("k@h3").uci() == "K@h3"
    assert board.parse_xboard("n@a1").uci() == "N@a1"


def test_copy_without_stack_preserves_current_position() -> None:
    """copy(stack=False) should keep the current position but discard history."""
    board = _board("asean")
    board.push_xboard("e3e4")

    copied = board.copy(stack=False)

    assert copied.fen() == board.fen()
    assert copied.move_stack == []
    assert copied.turn == board.turn


def test_alice_play_sequence_uses_second_board() -> None:
    """Alice moves should use Alice SAN rules and transfer pieces between boards."""
    board = _board("alice")
    moves = [FairyMove("e2e4"), FairyMove("e7e5"), FairyMove("g1f3")]

    assert board.variation_san(moves) == ["e4", "e5", "Nf3"]

    for san in ("e4", "e5", "Nf3"):
        board.push_xboard(san)

    assert board.move_stack == moves
    assert board.fen() == "rnbqkbnr/pppp1ppp/8/4|p3/4|P3/5|N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
    assert board.turn is False
