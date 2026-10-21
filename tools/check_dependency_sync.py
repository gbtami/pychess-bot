"""
Ensure PyChess-local uv metadata mirrors upstream-style requirements files.

Keep this check out of inherited source files to minimize merge conflicts.
"""

import logging
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parent.parent
LOGGER = logging.getLogger(__name__)


def requirements(path: Path) -> set[str]:
    """Read dependency pins from a requirements file."""
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def main() -> int:
    """Compare uv runtime and development dependencies with requirements files."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pairs = [
        ("runtime", ROOT / "requirements.txt", project["project"]["dependencies"]),
        ("dev", ROOT / "test_bot" / "test-requirements.txt", project["dependency-groups"]["dev"]),
    ]
    failed = False
    for name, path, declared in pairs:
        source = requirements(path)
        target = set(declared)
        if len(target) != len(declared) or source != target:
            failed = True
            LOGGER.error("%s dependency mismatch:", name)
            for item in sorted(source - target):
                LOGGER.error("  missing from pyproject.toml: %s", item)
            for item in sorted(target - source):
                LOGGER.error("  missing from %s: %s", path.relative_to(ROOT), item)
    if not failed:
        LOGGER.info("Runtime and dev dependency manifests match.")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
