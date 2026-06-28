"""Fork-specific variant compatibility tests for incoming challenge matching."""

from collections import Counter, defaultdict

import yaml

from lib import config, model
from lib.blocklist import OnlineBlocklist
from lib.lichess_types import ChallengeType, UserProfileType
from lib.timer import Timer
from lib.variants import normalize_challenge_variant_key, normalize_incoming_challenge_variant_key


def _challenge_config(variants: list[str]):
    with open("./config.yml.default") as file:
        cfg = yaml.safe_load(file)
    cfg["token"] = ""
    cfg["challenge"]["allow_list"] = []
    cfg["challenge"]["block_list"] = []
    cfg["challenge"]["min_rating"] = 0
    cfg["challenge"]["max_rating"] = 4000
    cfg["challenge"]["rating_difference"] = None
    cfg["challenge"]["variants"] = variants
    return config.Configuration(cfg).challenge


def _challenge(
    variant_key: str, *, initial_fen: str = "startpos", chess960: bool = False
) -> ChallengeType:
    return {
        "id": "zzzzzzzz",
        "url": "https://lichess.org/zzzzzzzz",
        "status": "created",
        "challenger": {"id": "c", "name": "c", "rating": 2000, "title": None, "online": True},
        "destUser": {"id": "b", "name": "b", "rating": 3000, "title": "BOT", "online": True},
        "variant": {"key": variant_key, "name": variant_key, "short": variant_key},
        "rated": False,
        "speed": "bullet",
        "timeControl": {"type": "clock", "limit": 90, "increment": 1, "show": "1.5+1"},
        "color": "random",
        "finalColor": "white",
        "perf": {"icon": "\ue032", "name": "Bullet"},
        "initialFen": initial_fen,
        "chess960": chess960,
    }


def test_variant_key_normalization_accepts_lichess_and_pychess_spellings() -> None:
    assert normalize_challenge_variant_key("standard") == "standard"
    assert normalize_challenge_variant_key("chess") == "standard"
    assert normalize_challenge_variant_key("kingOfTheHill") == "kingofthehill"
    assert normalize_challenge_variant_key("racingKings") == "racingkings"
    assert normalize_challenge_variant_key("threeCheck") == "3check"
    assert normalize_challenge_variant_key("s-chess") == "seirawan"
    assert normalize_challenge_variant_key("Chess960") == "chess960"
    assert normalize_challenge_variant_key("fischerandom") == "chess960"
    assert normalize_challenge_variant_key("kingOfTheHill", chess960=True) == "kingofthehill960"


def test_incoming_challenge_normalization_handles_server_keys_and_960() -> None:
    assert normalize_incoming_challenge_variant_key("kingofthehill") == "kingofthehill"
    assert (
        normalize_incoming_challenge_variant_key("racingkings", chess960=True)
        == "racingkings960"
    )
    assert (
        normalize_incoming_challenge_variant_key(
            "standard",
            initial_fen="brnkrqnb/pppppppp/8/8/8/8/PPPPPPPP/BRNKRQNB w KQkq - 0 1",
        )
        == "chess960"
    )


def test_challenge_matching_uses_normalized_variant_keys() -> None:
    challenge_cfg = _challenge_config(
        ["kingOfTheHill", "racingKings960", "threeCheck", "chess960", "s-chess"]
    )
    user_profile: UserProfileType = {"id": "b", "username": "b", "perfs": {}, "title": "BOT"}
    recent_challenges: defaultdict[str, list[Timer]] = defaultdict()
    recent_challenges["c"] = []
    online_block_list = OnlineBlocklist([])

    assert model.Challenge(_challenge("kingofthehill"), user_profile).is_supported(
        challenge_cfg, recent_challenges, Counter(), online_block_list, user_profile
    ) == (True, "")
    assert model.Challenge(
        _challenge("racingkings", chess960=True), user_profile
    ).is_supported(
        challenge_cfg, recent_challenges, Counter(), online_block_list, user_profile
    ) == (True, "")
    assert model.Challenge(_challenge("3check"), user_profile).is_supported(
        challenge_cfg, recent_challenges, Counter(), online_block_list, user_profile
    ) == (True, "")
    assert model.Challenge(_challenge("seirawan"), user_profile).is_supported(
        challenge_cfg, recent_challenges, Counter(), online_block_list, user_profile
    ) == (True, "")
    assert model.Challenge(
        _challenge(
            "standard",
            initial_fen="brnkrqnb/pppppppp/8/8/8/8/PPPPPPPP/BRNKRQNB w KQkq - 0 1",
        ),
        user_profile,
    ).is_supported(
        challenge_cfg, recent_challenges, Counter(), online_block_list, user_profile
    ) == (True, "")
