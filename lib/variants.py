# ruff: noqa: D100, D101, D102, D103, D105, D107, PLW1641

import re
from typing import Literal, Self, SupportsInt, cast

import chess
import pyffish as sf

sf.set_option("VariantPath", "variants.ini")

START_FEN: dict[str, str] = {variant: sf.start_fen(variant) for variant in sf.variants()}


def _normalize_variant_name(variant: str) -> tuple[str, str, bool]:
    """Return (pyffish_variant, xboard_variant, chess960)."""
    name = variant.strip().lower()
    name = name.replace("_", "-")
    name = re.sub(r"\s+", "-", name)

    is_chess960 = name.endswith("960")
    if is_chess960:
        name = name[:-3]

    aliases = {
        "standard": ("chess", "normal"),
        "chess": ("chess", "normal"),
        "from-position": ("chess", "normal"),
        "threecheck": ("3check", "3check"),
        "three-check": ("3check", "3check"),
        "3-check": ("3check", "3check"),
        "3check": ("3check", "3check"),
        "king-of-the-hill": ("kingofthehill", "kingofthehill"),
        "kingofthehill": ("kingofthehill", "kingofthehill"),
        "racing-kings": ("racingkings", "racingkings"),
        "racingkings": ("racingkings", "racingkings"),
        "light-brigade": ("lightbrigade", "light-brigade"),
        "lightbrigade": ("lightbrigade", "light-brigade"),
        "seirawan": ("seirawan", "seirawan"),
        "s-chess": ("seirawan", "seirawan"),
        "schess": ("seirawan", "seirawan"),
        "fischer-random": ("chess", "fischerandom"),
        "fischerandom": ("chess", "fischerandom"),
        "chess-960": ("chess", "fischerandom"),
        "chess960": ("chess", "fischerandom"),
    }

    normalized = name.replace("-", "")
    pyffish_variant, xboard_variant = aliases.get(name, aliases.get(normalized, (normalized, normalized)))

    if is_chess960 and pyffish_variant == "chess":
        xboard_variant = "fischerandom"

    return pyffish_variant, xboard_variant, is_chess960


class FairyMove:
    def __init__(self, uci: str) -> None:
        self.move = uci

    def uci(self) -> str:
        return self.move

    def xboard(self) -> str:
        return self.move

    @classmethod
    def from_uci(cls, uci: str) -> Self:
        return cls(uci)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FairyMove):
            return self.move == other.move
        if isinstance(other, str):
            return self.move == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.move)

    def __str__(self) -> str:
        return self.move


chess.Move = FairyMove  # type: ignore[misc, assignment]


def fairy_board(variant: str) -> type[chess.Board]:
    pyffish_variant, cecp_variant, is_chess960 = _normalize_variant_name(variant)

    class FairyBoardClass(FairyBoard):
        uci_variant = pyffish_variant
        xboard_variant = cecp_variant
        chess960 = is_chess960
        initial_fen = START_FEN[pyffish_variant]

    return cast("type[chess.Board]", FairyBoardClass)


class FairyBoard:
    uci_variant: str
    xboard_variant: str
    chess960: bool
    initial_fen: str

    def __init__(self, initial_fen: str | None = None, count_started: int = 0) -> None:
        del count_started
        if initial_fen is not None and initial_fen not in ("None", "", "startpos"):
            self.initial_fen = initial_fen

        self.move_stack: list[FairyMove] = []
        self.turn = self.initial_fen.split()[1] == "w"

    def push(self, move: FairyMove) -> None:
        self.move_stack.append(move)
        self.turn = not self.turn

    @staticmethod
    def _fix_drop_case(uci: str) -> str:
        # python-chess's UCI parser unconditionally lowercases all move tokens
        # before calling push_uci/parse_uci. For drop moves pyffish requires an
        # uppercase piece letter (e.g. "B@f5", "+L@a4"), so restore it.
        at = uci.find("@")
        if at > 0:
            uci = uci[: at - 1] + uci[at - 1].upper() + uci[at:]
        return uci

    @staticmethod
    def _clean_san(san: str) -> str:
        san = san.strip()
        san = san.replace("0", "O")
        # Engines sometimes decorate PV/bestmove SAN. Decorations must not
        # affect matching, but check/mate suffixes are also harmless to ignore.
        return re.sub(r"[+#?!]+$", "", san)

    def _legal_moves(self) -> list[str]:
        return sf.legal_moves(self.uci_variant, self.initial_fen, [move.uci() for move in self.move_stack])

    def _current_fen(self) -> str:
        return sf.get_fen(self.uci_variant, self.initial_fen, [move.uci() for move in self.move_stack])

    def push_uci(self, uci: str) -> FairyMove:
        move = FairyMove(self._fix_drop_case(uci))
        self.push(move)
        return move

    def parse_uci(self, uci: str) -> FairyMove:
        return FairyMove(self._fix_drop_case(uci))

    def parse_xboard(self, xboard: str) -> FairyMove:
        token = self._fix_drop_case(xboard.strip())
        legal_moves = self._legal_moves()

        # Most CECP engines use coordinate notation when san=0/rejected.
        if token in legal_moves:
            return FairyMove(token)

        wanted = self._clean_san(token)
        fen = self._current_fen()
        matches = []
        for move in legal_moves:
            san = self._clean_san(sf.get_san(self.uci_variant, fen, move))
            if san == wanted:
                matches.append(move)

        if len(matches) == 1:
            return FairyMove(matches[0])
        if len(matches) > 1:
            msg = f"Ambiguous XBoard/SAN move {xboard!r} on {fen}"
            raise ValueError(msg)
        msg = f"Illegal XBoard/SAN move {xboard!r} on {fen}"
        raise ValueError(msg)

    def parse_san(self, san: str) -> FairyMove:
        return self.parse_xboard(san)

    def variation_san(self, pv: list[FairyMove]) -> list[str]:
        board = self.copy(stack=True)
        san_moves = []
        for move in pv:
            san_moves.append(board.san(move))
            board.push(move)
        return san_moves

    def san(self, move: FairyMove | chess.Move | str) -> str:
        uci = move.uci() if hasattr(move, "uci") else str(move)
        return sf.get_san(self.uci_variant, self.fen(), uci)

    def xboard(self, move: FairyMove | chess.Move | str) -> str:
        return move.xboard() if hasattr(move, "xboard") else str(move)

    def push_xboard(self, xboard: str) -> FairyMove:
        move = self.parse_xboard(xboard)
        self.push(move)
        return move

    def pop(self) -> None:
        self.move_stack.pop()
        self.turn = not self.turn

    def is_game_over(self, *, claim_draw: bool = False) -> bool:
        del claim_draw
        return False

    def fen(
        self,
        *,
        shredder: bool = False,
        en_passant: Literal["legal", "fen", "xfen"] = "legal",
        promoted: bool | None = None,
    ) -> str:
        del shredder, en_passant, promoted
        return self._current_fen()

    @property
    def occupied(self) -> int:
        # Return 0 so engine_wrapper's piece-count guards (syzygy, gaviota,
        # draw-offer) always treat this as "too few pieces / not applicable"
        # for pychess variants, which don't support those features.
        return 0

    def copy(self, stack: bool | SupportsInt = False) -> Self:
        if stack is False:
            # python-chess copy(stack=False) preserves the current position but
            # discards the move stack. We represent that by using current FEN as
            # the new root. This matters for XBoard PV parsing.
            new = type(self)(self.fen())
        elif stack is True:
            new = type(self)(self.initial_fen)
            new.move_stack = self.move_stack.copy()
        else:
            count = int(stack)
            moves = [move.uci() for move in self.move_stack]
            prefix = moves[:-count] if count else moves
            kept = self.move_stack[-count:].copy() if count else []
            new = type(self)(sf.get_fen(self.uci_variant, self.initial_fen, prefix))
            new.move_stack = kept
        new.turn = self.turn
        return new

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FairyBoard):
            return NotImplemented
        return (
            type(self).uci_variant == type(other).uci_variant
            and type(self).xboard_variant == type(other).xboard_variant
            and self.chess960 == other.chess960
            and self.initial_fen == other.initial_fen
            and self.move_stack == other.move_stack
            and self.turn == other.turn
        )

    def root(self) -> Self:
        return type(self)(self.initial_fen)
