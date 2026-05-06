import argparse
import hashlib
import re
import sys
from pathlib import Path


SYNC_MARKER_RE = re.compile(
    r"<!--\s*i18n-sync:\s*source=(?P<source>[^;]+);\s*sha256=(?P<sha256>[0-9A-Fa-f]{64})\s*-->"
)


def sha256_hex(path):
    with open(str(path), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest().upper()


def parse_sync_marker(path):
    with open(str(path), "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    for line in text.splitlines()[:5]:
        match = SYNC_MARKER_RE.search(line)
        if match:
            return match.group("source"), match.group("sha256").upper()
    return None


def zh_doc_paths(docs_dir):
    paths = []
    for path in docs_dir.rglob("*.md"):
        if path.name.endswith(".en.md"):
            continue
        paths.append(path)
    return sorted(paths)


def en_doc_path(zh_path):
    return zh_path.with_name("{0}.en.md".format(zh_path.stem))


def relative_posix(path, root):
    return path.relative_to(root).as_posix()


def main():
    parser = argparse.ArgumentParser(
        description="Check whether English MkDocs pages are present and synced to their Chinese source pages."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing the docs/ directory.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print synchronized pages as well.",
    )
    args = parser.parse_args()

    repo_root = args.root.resolve()
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        print("docs directory not found: {0}".format(docs_dir), file=sys.stderr)
        return 2

    zh_paths = zh_doc_paths(docs_dir)
    issues = 0
    synced = 0

    for zh_path in zh_paths:
        en_path = en_doc_path(zh_path)
        zh_rel = relative_posix(zh_path, repo_root)
        en_rel = relative_posix(en_path, repo_root)
        current_hash = sha256_hex(zh_path)

        if not en_path.exists():
            issues += 1
            print("MISSING  {0}  <- source {1}".format(en_rel, zh_rel))
            continue

        marker = parse_sync_marker(en_path)
        if marker is None:
            issues += 1
            print("NO-MARKER  {0}  <- source {1}".format(en_rel, zh_rel))
            continue

        marker_source, marker_hash = marker
        if marker_source != zh_rel:
            issues += 1
            print(
                "SOURCE-MISMATCH  {0}  marker={1} expected={2}".format(
                    en_rel, marker_source, zh_rel
                )
            )
            continue

        if marker_hash != current_hash:
            issues += 1
            print(
                "STALE  {0}  source={1}  marker={2}  current={3}".format(
                    en_rel, zh_rel, marker_hash, current_hash
                )
            )
            continue

        synced += 1
        if args.verbose:
            print("OK  {0}".format(en_rel))

    total = len(zh_paths)
    if issues == 0:
        print(
            "All synchronized: {0}/{1} English pages are up to date.".format(
                synced, total
            )
        )
        return 0

    print(
        "Synchronization issues found: {0}. Up to date: {1}/{2} English pages.".format(
            issues, synced, total
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
