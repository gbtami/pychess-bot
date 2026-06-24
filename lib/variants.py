# -*- coding: utf-8 -*-

import chess
try:
    import pyffish as sf
    sf.set_option("VariantPath", "variants.ini")
except ImportError:
    print("No pyffish module installed!")


START_FEN = {variant: sf.start_fen(variant) for variant in sf.variants()}


class FairyMove:
    def __init__(self, uci: str):
        self.move = uci

    def uci(self):
        return self.move

    @classmethod
    def from_uci(cls, uci):
        return cls(uci)

    def __str__(self):
        return self.move


chess.Move = FairyMove


def fairy_board(variant):
    is_chess960 = variant.endswith("960")
    variant = variant.lower().removesuffix("960")
    variant = "3check" if variant == "threecheck" else variant

    class FairyBoardClass(FairyBoard):
        uci_variant = "chess" if variant == "standard" else variant
        xboard_variant = "normal" if variant == "standard" else variant
        chess960 = is_chess960
        initial_fen = START_FEN[uci_variant]

    return FairyBoardClass


class FairyBoard:
    def __init__(self, initial_fen=None, count_started=0):
        if initial_fen not in (None, "None", "",  "startpos"):
            self.initial_fen = initial_fen

        self.move_stack = []
        self.turn = True if self.initial_fen.split()[1] == "w" else False

    def push(self, move: FairyMove):
        self.move_stack.append(move)
        self.turn = not self.turn

    @staticmethod
    def _fix_drop_case(uci: str) -> str:
        # python-chess's UCI parser unconditionally lowercases all move tokens
        # before calling push_uci/parse_uci (chess/engine.py lines 1900, 1907).
        # For drop moves pyffish requires an uppercase piece letter (e.g. "B@f5",
        # "+L@a4"), so we restore the character immediately before "@" to uppercase.
        at = uci.find("@")
        if at > 0:
            uci = uci[:at - 1] + uci[at - 1].upper() + uci[at:]
        return uci

    def push_uci(self, uci: str):
        move = FairyMove(self._fix_drop_case(uci))
        self.push(move)
        return move

    def parse_uci(self, uci: str):
        move = FairyMove(self._fix_drop_case(uci))

    def parse_san(self, san: str):
        # TODO
        return san

    def variation_san(self, pv: str):
        # TODO
        return [str(move) for move in pv]

    def san(self, move):
        # TODO: pyffish does not expose SAN; return UCI string as fallback
        return str(move)

    def push_xboard(self, san: str):
        move = self.parse_san(san)
        self.push(move)
        return move

    def pop(self):
        self.move_stack.pop()
        self.turn = not self.turn

    def is_game_over(self):
        # TODO
        return False

    def fen(self, *, shredder=False, en_passant="legal", promoted=None):
        moves = [m.uci() for m in self.move_stack]
        return sf.get_fen(self.uci_variant, self.initial_fen, moves)

    @property
    def occupied(self):
        # Return 0 so engine_wrapper's piece-count guards (syzygy, gaviota,
        # draw-offer) always treat this as "too few pieces / not applicable"
        # for pychess variants, which don't support those features.
        return 0

    def copy(self, stack=False):
        new = type(self)(self.initial_fen)
        if stack:
            new.move_stack = self.move_stack.copy()
        return new

    def root(self):
        return type(self)(self.initial_fen)
