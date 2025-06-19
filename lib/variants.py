# -*- coding: utf-8 -*-

import chess
try:
    import pyffish as sf
    sf.set_option("VariantPath", "variants.ini")
except ImportError:
    print("No pyffish module installed!")


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

    return FairyBoardClass


class FairyBoard:
    uci_variant = "chess"
    xboard_variant = "normal"

    def __init__(self, initial_fen="startpos"):
        self.initial_fen = (
            initial_fen
            if initial_fen and initial_fen != "startpos"
            else sf.start_fen(self.uci_variant)
        )
        self.move_stack = []
        self.turn = True if self.initial_fen.split()[1] == "w" else False

    def push(self, move: FairyMove):
        self.move_stack.append(move)
        self.turn = not self.turn

    def push_uci(self, uci: str):
        move = FairyMove(uci)
        self.push(move)
        return move

    def parse_uci(self, uci: str):
        return FairyMove(uci)

    def parse_san(self, san: str):
        # Match legal moves.
        matched_move = None
        for move in sf.legal_moves(self.uci_variant, self.initial_fen, self.move_stack, self.chess960):
            if matched_move:
                raise
            if move == san:
                matched_move = move

        if not matched_move:
            raise

        return FairyMove(matched_move)

    def push_xboard(self, san: str):
        move = self.parse_san(san)
        self.push(move)
        return move

    def pop(self):
        del self.move_stack[-1]
        self.turn = not self.turn

    def is_game_over(self):
        return False

    def fen(self, shredder=True, en_passant="fen"):
        if self.initial_fen is None:
            return self.starting_fen
        else:
            return self.initial_fen

    @property
    def occupied(self):
        return 64  # TODO

    def copy(self, stack=False):
        return type(self)()

    def root(self):
        return type(self)()
