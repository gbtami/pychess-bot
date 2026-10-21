"""Ensure PyChess-local uv metadata mirrors upstream-style requirements files.

Keep this check out of inherited source files to minimize merge conflicts.
"""

from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parent.parent


def requirements(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def main() -> int:
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
            print(f"{name} dependency mismatch:", file=sys.stderr)
            for item in sorted(source - target):
                print(f"  missing from pyproject.toml: {item}", file=sys.stderr)
            for item in sorted(target - source):
                print(f"  missing from {path.relative_to(ROOT)}: {item}", file=sys.stderr)
    if not failed:
        print("Runtime and dev dependency manifests match.")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
