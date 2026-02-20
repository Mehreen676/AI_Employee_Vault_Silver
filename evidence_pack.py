"""Evidence Pack Generator (BONUS).

Zips key artefacts from the Silver Agent pipeline into a timestamped archive
so judges (or reviewers) can download a single file containing everything
they need to verify the run.

Contents of the zip:
  run_log.md
  prompt_history.md
  Plans/
  Pending_Approval/
  Approved/
  Done/
  Logs/

Usage:
  python evidence_pack.py
  python evidence_pack.py --out /path/to/output.zip

Output: evidence_<YYYYMMDD_HHMMSS>.zip  (in repo root by default)
"""

from __future__ import annotations

import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"

INCLUDE_FILES = [
    BASE_DIR / "run_log.md",
    BASE_DIR / "prompt_history.md",
    BASE_DIR / "README.md",
]

INCLUDE_DIRS = [
    BASE_DIR / "Plans",
    BASE_DIR / "Pending_Approval",
    BASE_DIR / "Approved",
    BASE_DIR / "Done",
    BASE_DIR / "Logs",
]


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def append_log(text: str) -> None:
    try:
        RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def build_zip(out_path: Path) -> int:
    """Build the evidence zip. Returns number of files added."""
    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Individual files
        for fp in INCLUDE_FILES:
            if fp.exists():
                arcname = fp.relative_to(BASE_DIR)
                zf.write(fp, arcname)
                count += 1

        # Directories (recurse)
        for d in INCLUDE_DIRS:
            if d.is_dir():
                for child in sorted(d.rglob("*")):
                    if child.is_file() and child.name != ".gitkeep":
                        arcname = child.relative_to(BASE_DIR)
                        zf.write(child, arcname)
                        count += 1

    return count


def main() -> None:
    # Determine output path
    if len(sys.argv) >= 3 and sys.argv[1] == "--out":
        out_path = Path(sys.argv[2])
    else:
        out_path = BASE_DIR / f"evidence_{ts_slug()}.zip"

    print(f"=== Evidence Pack Generator ===")
    print(f"Output: {out_path}")

    count = build_zip(out_path)
    size_kb = out_path.stat().st_size / 1024 if out_path.exists() else 0

    append_log(
        f"{utc_ts()} - EvidencePack: created | {out_path.name} | files={count} | size={size_kb:.1f}KB\n"
    )

    print(f"Done! {count} files packed, {size_kb:.1f} KB")
    print(f"Share: {out_path}")


if __name__ == "__main__":
    main()
