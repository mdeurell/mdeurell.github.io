"""
Critical Earth — site assembly.

Reads:
    content/site.yaml             (top-level: title, hero, nav, section list)
    content/sections/*.yaml       (one file per section, each is a list of typed blocks)
    templates/index.html.j2       (outer skeleton)
    templates/blocks/*.html.j2    (one partial per block type)

Writes:
    website/index.html            (single generated file — never edit by hand)

Run:
    python -m pipeline.build.build_index             # build once
    python -m pipeline.build.build_index --watch     # rebuild on change

Block types are dispatched by the `type` field via dynamic include
(`templates/blocks/<type>.html.j2`). Adding a new block type = drop a new
template and start using it in YAML. No code change needed here.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import mistune
import yaml
from jinja2 import ChainableUndefined, Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content"
SECTIONS_DIR = CONTENT_DIR / "sections"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT = ROOT / "website" / "index.html"


# ── Markdown rendering ─────────────────────────────────────────────────────
# mistune in safe-html mode by default; we explicitly allow raw HTML in
# captions/prose because we sometimes embed <span class="footnote-inline">,
# <code>, <em>, <strong> etc. directly. Source content is trusted (ours),
# never user input.
_md = mistune.create_markdown(escape=False, hard_wrap=False)


def render_md(text: str) -> str:
    """Markdown → HTML. If no markdown features are detected, returned
    HTML still wraps in <p>; downstream templates should NOT add their own
    <p> around md-rendered output."""
    if text is None:
        return ""
    return _md(text.strip())


def render_md_inline(text: str) -> str:
    """Render a single paragraph of markdown but strip the wrapping <p>…</p>
    so the result can drop into an existing <p> or inline span."""
    html = render_md(text).strip()
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return html


# ── Section / site loading ─────────────────────────────────────────────────
def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _prose_can_host_factbox(prose: dict) -> bool:
    """True if a prose block has enough body to comfortably contain a
    right-floated factbox without overflowing into the next section.

    Floated asides take a column of vertical space. If the prose paragraph
    is shorter than the factbox's natural height, the float bleeds past
    the prose's bottom margin and overlaps the following block (figure,
    next prose, etc.). Heuristic threshold: ≥ 2 paragraphs OR ≥ 600 chars
    of body text. Below that, the factbox renders inline instead.
    """
    text = prose.get("text") or ""
    if not isinstance(text, str):
        return False
    body = text.strip()
    if not body:
        return False
    paras = [p for p in body.split("\n\n") if p.strip()]
    return len(paras) >= 2 or len(body) >= 600


def _absorb_margin_factboxes(blocks: list) -> list:
    """Site-wide convention: factbox blocks are absorbed into a neighbouring
    prose block and rendered as right-floated asides — but only when the
    host prose has enough body length to contain the float. Otherwise the
    factbox is left inline at its document-order position, which keeps it
    visually above any following figure rather than spilling past the
    short prose section.

    Attachment preference:
      1) the immediately preceding prose if it can host (≥ 2 paragraphs or
         ≥ 600 chars of body);
      2) otherwise the next prose block in document order, if that can host;
      3) otherwise render inline (no absorption).
    """
    if not blocks:
        return blocks
    n = len(blocks)
    keep = [True] * n
    last_prose_idx: int | None = None
    for i, b in enumerate(blocks):
        if not isinstance(b, dict):
            continue
        btype = b.get("type")
        if btype == "prose":
            last_prose_idx = i
            continue
        if btype != "factbox":
            continue
        target_idx: int | None = None
        if last_prose_idx is not None and _prose_can_host_factbox(blocks[last_prose_idx]):
            target_idx = last_prose_idx
        if target_idx is None:
            for j in range(i + 1, n):
                nb = blocks[j]
                if isinstance(nb, dict) and nb.get("type") == "prose" and _prose_can_host_factbox(nb):
                    target_idx = j
                    break
        if target_idx is not None:
            blocks[target_idx].setdefault("margin_factboxes", []).append(b)
            keep[i] = False
        # else: leave as inline standalone factbox at its original position
    return [b for b, k in zip(blocks, keep) if k]


def load_site() -> dict:
    site = load_yaml(CONTENT_DIR / "site.yaml")
    sections = []
    for rel in site["sections"]:
        sec_path = SECTIONS_DIR / rel
        if not sec_path.exists():
            raise FileNotFoundError(f"Section file missing: {sec_path}")
        section = load_yaml(sec_path)
        section.setdefault("source_file", rel)
        if isinstance(section.get("blocks"), list):
            section["blocks"] = _absorb_margin_factboxes(section["blocks"])
        sections.append(section)
    site["sections"] = sections
    return site


# ── Jinja env ──────────────────────────────────────────────────────────────
def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html",), default_for_string=False),
        trim_blocks=True,
        lstrip_blocks=True,
        # Optional YAML fields are accessed as `block.foo` even when missing —
        # ChainableUndefined returns Undefined (falsy) instead of raising,
        # so `{% if block.foo %}` works whether the field exists or not.
        undefined=ChainableUndefined,
    )
    env.filters["md"] = render_md
    env.filters["md_inline"] = render_md_inline
    return env


# ── Build ──────────────────────────────────────────────────────────────────
def build() -> None:
    site = load_site()
    env = make_env()
    template = env.get_template("index.html.j2")
    asset_version = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    html = template.render(site=site, asset_version=asset_version)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"[build] wrote {OUTPUT.relative_to(ROOT)}  ({len(html):,} chars, v={asset_version})")


# ── Watch mode ─────────────────────────────────────────────────────────────
def watch() -> None:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class Rebuild(FileSystemEventHandler):
        def __init__(self):
            self._last = 0.0

        def on_any_event(self, event):
            if event.is_directory:
                return
            p = Path(event.src_path)
            if p.suffix not in {".yaml", ".j2", ".md"}:
                return
            now = time.time()
            if now - self._last < 0.25:  # debounce
                return
            self._last = now
            try:
                build()
            except Exception as exc:  # noqa: BLE001
                print(f"[build] ERROR: {exc!r}", file=sys.stderr)

    build()
    handler = Rebuild()
    observer = Observer()
    observer.schedule(handler, str(CONTENT_DIR), recursive=True)
    observer.schedule(handler, str(TEMPLATES_DIR), recursive=True)
    observer.start()
    print(f"[watch] watching {CONTENT_DIR.relative_to(ROOT)} and {TEMPLATES_DIR.relative_to(ROOT)} (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main() -> None:
    ap = argparse.ArgumentParser(description="Assemble website/index.html from content/ + templates/.")
    ap.add_argument("--watch", action="store_true", help="rebuild on file change")
    args = ap.parse_args()
    if args.watch:
        watch()
    else:
        build()


if __name__ == "__main__":
    main()
