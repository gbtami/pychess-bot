# -*- coding: utf-8 -*-
import chess


class PychessMove:
    def __init__(self, uci: str):
        self.move = uci

    def uci(self):
        return self.move

    @classmethod
    def from_uci(cls, uci):
        return cls(uci)

    def __str__(self):
        return self.move


chess.Move = PychessMove


class SimpleBoard:
    def __init__(self, initial_fen=None, chess960=False):
        self.initial_fen = self.starting_fen if not initial_fen else initial_fen
        self.move_stack = []
        self.turn = True if self.initial_fen.split()[1] == "w" else False
        self.chess960 = chess960

    def push(self, move: PychessMove):
        self.move_stack.append(move)
        self.turn = not self.turn

    def push_uci(self, uci: str):
        move = PychessMove(uci)
        self.push(move)
        return move

    def parse_uci(self, uci: str):
        return PychessMove(uci)

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


class StandardBoard(SimpleBoard):
    uci_variant = "chess"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class CrazyhouseBoard(SimpleBoard):
    uci_variant = "crazyhouse"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1"


class MakrukBoard(SimpleBoard):
    uci_variant = "makruk"
    starting_fen = "rnsmksnr/8/pppppppp/8/8/PPPPPPPP/8/RNSKMSNR w - - 0 1"


class CambodianBoard(SimpleBoard):
    uci_variant = "cambodian"
    starting_fen = "rnsmksnr/8/pppppppp/8/8/PPPPPPPP/8/RNSKMSNR w DEde - 0 1"


class SittuyinBoard(SimpleBoard):
    uci_variant = "sittuyin"
    starting_fen = "8/8/4pppp/pppp4/4PPPP/PPPP4/8/8[rrnnssfkRRNNSSFK] w - - 0 1"


class ShogiBoard(SimpleBoard):
    uci_variant = "shogi"
    starting_fen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL[] b - 1"


class XiangqiBoard(SimpleBoard):
    uci_variant = "xiangqi"
    starting_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"


class PlacementBoard(SimpleBoard):
    uci_variant = "placement"
    starting_fen = "8/pppppppp/8/8/8/8/PPPPPPPP/8[nnbbrrqkNNBBRRQK] w - - 0 1"


class CapablancaBoard(SimpleBoard):
    uci_variant = "capablanca"
    starting_fen = "rnabqkbcnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNABQKBCNR w - - 0 1"


class CapahouseBoard(SimpleBoard):
    uci_variant = "capahouse"
    starting_fen = "rnabqkbcnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNABQKBCNR[] w - - 0 1"


class SeirawanBoard(SimpleBoard):
    uci_variant = "seirawan"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[HEhe] w KQBCDFGkqbcdfg - 0 1"


class ShouseBoard(SimpleBoard):
    uci_variant = "shouse"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[HEhe] w KQBCDFGkqbcdfg - 0 1"


class GrandBoard(SimpleBoard):
    uci_variant = "grand"
    starting_fen = "r8r/1nbqkcabn1/pppppppppp/10/10/10/10/PPPPPPPPPP/1NBQKCABN1/R8R w - - 0 1"


class GrandhouseBoard(SimpleBoard):
    uci_variant = "grandhouse"
    starting_fen = "r8r/1nbqkcabn1/pppppppppp/10/10/10/10/PPPPPPPPPP/1NBQKCABN1/R8R[] w - - 0 1"


class GothicBoard(SimpleBoard):
    uci_variant = "gothic"
    starting_fen = "rnbqckabnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNBQCKABNR w KQkq - 0 1"


class GothhouseBoard(SimpleBoard):
    uci_variant = "gothhouse"
    starting_fen = "rnbqckabnr/pppppppppp/10/10/10/10/PPPPPPPPPP/RNBQCKABNR[] w KQkq - 0 1"


class MiniShogiBoard(SimpleBoard):
    uci_variant = "minishogi"
    starting_fen = "rbsgk/4p/5/P4/KGSBR[-] b - 1"


class MiniXiangqiBoard(SimpleBoard):
    uci_variant = "minixiangqi"
    starting_fen = "rcnkncr/p1ppp1p/7/7/7/P1PPP1P/RCNKNCR w - - 0 1"


class ShakoBoard(SimpleBoard):
    uci_variant = "shako"
    starting_fen = "c8c/ernbqkbnre/pppppppppp/10/10/10/10/PPPPPPPPPP/ERNBQKBNRE/C8C w KQkq - 0 1"


VARIANT2BOARD = {
    "chess": StandardBoard,
    "crazyhouse": CrazyhouseBoard,
    "makruk": MakrukBoard,
    "sittuyin": SittuyinBoard,
    "shogi": ShogiBoard,
    "xiangqi": XiangqiBoard,
    "placement": PlacementBoard,
    "capablanca": CapablancaBoard,
    "capahouse": CapahouseBoard,
    "seirawan": SeirawanBoard,
    "shouse": ShouseBoard,
    "grand": GrandBoard,
    "grandhouse": GrandhouseBoard,
    "gothic": GothicBoard,
    "gothhouse": GothhouseBoard,
    "minishogi": MiniShogiBoard,
    "cambodian": CambodianBoard,
    "minixiangqi": MiniXiangqiBoard,
    "shako": ShakoBoard,
}
