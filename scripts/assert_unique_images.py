"""Assert every catalog SKU has a unique image file (path + hash)."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")


def path_for(pid: str, aud: str | None) -> Path:
    folder = "male" if aud == "masculino" else ""
    name = f"{pid}.png"
    if folder:
        return ROOT / "public" / "images" / "products" / folder / name
    return ROOT / "public" / "images" / "products" / name


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    block = text.split("const catalogItems")[1].split("function defaultDescription")[0]
    items = re.findall(
        r'id: "([^"]+)"[\s\S]*?catalogImage\("([^"]+)"(?:, "(masculino)")?\)',
        block,
    )
    missing = []
    by_path: dict[str, list[str]] = defaultdict(list)
    by_hash: dict[str, list[str]] = defaultdict(list)
    for pid, img_id, aud in items:
        p = path_for(img_id, aud)
        key = str(p.relative_to(ROOT / "public")).replace("\\", "/")
        by_path[key].append(pid)
        if not p.exists():
            missing.append(pid)
            continue
        by_hash[file_hash(p)].append(pid)

    dup_paths = {k: v for k, v in by_path.items() if len(set(v)) > 1}
    dup_hashes = {k: v for k, v in by_hash.items() if len(set(v)) > 1}
    print("skus", len(items))
    print("missing", len(missing), missing[:20])
    print("dup paths", dup_paths)
    print("dup hashes", {h[:12]: v for h, v in dup_hashes.items()})
    if missing or dup_paths or dup_hashes:
        raise SystemExit(2)
    print("OK unique")


if __name__ == "__main__":
    main()
