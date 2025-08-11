#!/usr/bin/env python3
"""
AXL Web: Documentation Site Builder

Generates a static documentation site from Markdown files, keeping the
same theme and style as the main site (`site/index.html`).

Features:
- Reads CSS directly from `site/index.html` to stay in sync with the brand
- Converts all `docs/**/*.md` files to `site/docs/**/*.html`
- Auto-builds a sidebar navigation from the docs tree
- Supports fenced code blocks, tables, and basic Markdown.
- Works with or without `markdown` package (falls back to a small converter)

Usage:
  python build_docs.py            # builds once
  python build_docs.py --watch    # optional: rebuild on changes (polling)

Dependencies (optional, recommended):
  pip install markdown

The output is served by the existing dev server (server.py) at:
  http://localhost:8000/docs/
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parent
SITE_DIR = ROOT_DIR / "site"
DOCS_SRC_DIR = ROOT_DIR / "docs"
DOCS_OUT_DIR = SITE_DIR / "docs"
INDEX_HTML = SITE_DIR / "index.html"


def read_site_css() -> str:
    """Extract the first <style>...</style> block from site/index.html."""
    if not INDEX_HTML.exists():
        raise FileNotFoundError(f"Missing {INDEX_HTML}")
    text = INDEX_HTML.read_text(encoding="utf-8")
    m = re.search(r"<style>([\s\S]*?)</style>", text, re.IGNORECASE)
    if not m:
        return ""  # no inline CSS; that's fine
    return m.group(1).strip()


def import_markdown() -> Optional[object]:
    try:
        import markdown  # type: ignore
        return markdown
    except Exception:
        return None


def minimal_md_to_html(md: str) -> str:
    """A tiny Markdown-to-HTML fallback renderer.

    Supports:
    - #, ##, ### headings
    - ```lang fenced code```
    - paragraphs and inline code `code`
    - unordered lists (- or *)
    This is intentionally small but good enough if the markdown module
    is unavailable.
    """

    # Fenced code blocks
    def fenced_repl(match: re.Match) -> str:
        lang = match.group(1) or ""
        code = match.group(2)
        return (
            f'<pre class="code"><code class="language-{html.escape(lang)}">'
            f"{html.escape(code)}"  # preserve code verbatim
            f"</code></pre>"
        )

    html_out = re.sub(r"```\s*([A-Za-z0-9_+-]*)\n([\s\S]*?)\n```", fenced_repl, md)

    lines = html_out.splitlines()
    out: List[str] = []
    in_list = False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        # headings
        if line.startswith("### "):
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
            continue
        # lists
        if re.match(r"^\s*[-*] ", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^\s*[-*] ", "", line)
            # inline code
            item = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", item)
            out.append(f"<li>{item}</li>")
            continue
        # inline code and paragraphs
        paragraph = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", line)
        out.append(f"<p>{paragraph}</p>")

    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def convert_markdown(md_text: str) -> str:
    md_mod = import_markdown()
    if md_mod is None:
        return minimal_md_to_html(md_text)
    md = md_mod.Markdown(extensions=[
        "fenced_code",
        "tables",
        "toc",
        "md_in_html",
    ])
    return md.convert(md_text)


@dataclass
class DocPage:
    source_path: Path
    output_path: Path
    url_path: str
    title: str


def derive_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    # fallback to filename with spaces
    name = fallback.replace("-", " ").replace("_", " ")
    return name.title()


def discover_docs() -> List[DocPage]:
    pages: List[DocPage] = []
    for path in sorted(DOCS_SRC_DIR.rglob("*.md")):
        rel = path.relative_to(DOCS_SRC_DIR)
        out_rel = rel.with_suffix(".html")
        out_path = DOCS_OUT_DIR / out_rel
        url_path = "/docs/" + str(out_rel).replace(os.sep, "/")
        title = derive_title(path.read_text(encoding="utf-8"), rel.stem)
        pages.append(DocPage(path, out_path, url_path, title))
    return pages


@dataclass
class NavNode:
    name: str
    title: str
    page: Optional[DocPage] = None
    children: Dict[str, "NavNode"] = field(default_factory=dict)


def _display_title_from_segment(segment: str) -> str:
    name = segment.replace("-", " ").replace("_", " ")
    return name.title()


def build_nav_tree(pages: List[DocPage]) -> NavNode:
    root = NavNode(name="", title="Docs")
    for p in pages:
        rel = p.source_path.relative_to(DOCS_SRC_DIR)
        parts = list(rel.parts)
        # detect index.md as container page for a folder
        is_index = parts[-1].lower() == "index.md"
        cursor = root
        for i, seg in enumerate(parts):
            is_leaf = i == len(parts) - 1
            if is_leaf and not is_index:
                # leaf file (non-index)
                if seg not in cursor.children:
                    cursor.children[seg] = NavNode(name=seg, title=p.title)
                node = cursor.children[seg]
                node.title = p.title
                node.page = p
            elif is_leaf and is_index:
                # index file defines the folder's page
                folder_name = parts[-2] if len(parts) > 1 else "index"
                if folder_name not in cursor.children:
                    cursor.children[folder_name] = NavNode(name=folder_name, title=_display_title_from_segment(folder_name))
                node = cursor.children[folder_name]
                node.page = p
                # keep title from page
                node.title = p.title or node.title
            else:
                if seg not in cursor.children:
                    cursor.children[seg] = NavNode(name=seg, title=_display_title_from_segment(seg))
                cursor = cursor.children[seg]
    return root


def _subtree_contains_url(node: NavNode, url: str) -> bool:
    if node.page is not None and node.page.url_path == url:
        return True
    for child in node.children.values():
        if _subtree_contains_url(child, url):
            return True
    return False


def _render_nav(node: NavNode, current_url: str, is_root: bool = False, base_key: str = "") -> str:
    lines: List[str] = []
    if is_root:
        lines.append('<nav class="docs-nav" aria-label="Docs">')
    lines.append("<ul>")
    # sort folders and pages by title
    def sort_key(item: Tuple[str, NavNode]):
        return item[1].title.lower()
    for key, child in sorted(node.children.items(), key=sort_key):
        has_children = len(child.children) > 0
        li_classes: List[str] = []
        if has_children:
            li_classes.append("folder")
        # determine active class
        is_active = child.page is not None and child.page.url_path == current_url
        if is_active:
            li_classes.append("active")
        # expanded if subtree contains current
        is_expanded = has_children and _subtree_contains_url(child, current_url)
        if is_expanded:
            li_classes.append("expanded")
        class_attr = f" class=\"{' '.join(li_classes)}\"" if li_classes else ""
        data_key = (base_key + "/" + child.name).strip("/")
        # label/link row with optional toggle
        if has_children:
            lines.append(f"  <li data-key=\"{html.escape(data_key)}\"{class_attr}>")
            lines.append("    <div class=\"nav-row\">")
            lines.append("      <button class=\"nav-toggle\" aria-label=\"Toggle section\" aria-expanded=\"" + ("true" if is_expanded else "false") + "\"><i class=\"ico fa-solid fa-chevron-right\"></i></button>")
            if child.page is not None:
                lines.append(f"      <a href=\"{child.page.url_path}\">{html.escape(child.title)}</a>")
            else:
                lines.append(f"      <span>{html.escape(child.title)}</span>")
            lines.append("    </div>")
        else:
            # leaf page
            if child.page is not None:
                lines.append(f"  <li data-key=\"{html.escape(data_key)}\"{class_attr}><a href=\"{child.page.url_path}\">{html.escape(child.title)}</a>")
            else:
                lines.append(f"  <li data-key=\"{html.escape(data_key)}\"{class_attr}><span>{html.escape(child.title)}</span>")
        # children
        if has_children:
            lines.append(_render_nav(child, current_url, False, data_key))
        lines.append("  </li>")
    lines.append("</ul>")
    if is_root:
        lines.append("</nav>")
    return "\n".join(lines)


def build_sidebar(pages: List[DocPage], current: DocPage) -> str:
    tree = build_nav_tree(pages)
    return _render_nav(tree, current.url_path, is_root=True)


def render_template(css: str, sidebar_html: str, content_html: str, page_title: str, base_prefix: str) -> str:
    """Return a full HTML page using the main site's CSS and header.

    Uses simple placeholder tokens to avoid brace escaping issues.
    """
    tpl = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>__TITLE__ — AXL DB Docs</title>
  <meta name=\"description\" content=\"AXL DB Documentation\" />
  <style>
__CSS__
    .docs-layout{display:grid; grid-template-columns: 260px 1fr; gap:18px;}
    .docs-nav ul{list-style:none; margin:0; padding:0}
    .docs-nav ul ul{margin:6px 0 6px 12px; padding-left:12px; border-left:1px solid var(--border)}
    .docs-nav li a{display:block; padding:10px 12px; color:var(--muted); text-decoration:none; border-radius:8px}
    .docs-nav li a:hover{background:rgba(255,178,36,.10); color:var(--text)}
    .docs-nav li.active a{background:rgba(255,178,36,.14); color:var(--text)}
    .docs-nav li.folder > a{font-weight:700; color:var(--text)}
    .docs-nav li.folder {position:relative}
    .docs-nav li.folder > ul {display:none}
    .docs-nav li.folder.expanded > ul {display:block}
    .docs-nav .nav-row{display:flex; align-items:center; gap:6px}
    .docs-nav .nav-toggle{appearance:none; background:transparent; border:0; color:var(--muted); padding:6px; border-radius:6px; cursor:pointer}
    .docs-nav .nav-toggle:hover{background:rgba(255,178,36,.10); color:var(--text)}
    .docs-nav .nav-toggle .ico{font-size:12px; transition: transform .15s ease}
    .docs-nav li.folder.expanded > .nav-row .nav-toggle .ico{transform: rotate(90deg)}
    .docs-content{background:var(--panel); border:1px solid var(--border); border-radius:var(--radius); box-shadow: var(--shadow); padding:18px}
    .docs-content h1, .docs-content h2, .docs-content h3{margin-top:1.2em; margin-bottom:.5em}
    .docs-content h1:first-child{margin-top:0}
    .docs-content p{margin:.6em 0; color:#cbd6e6; font-size:1rem}
    .docs-content table{width:100%; border-collapse:collapse; margin:10px 0;}
    .docs-content th, .docs-content td{border:1px solid var(--border); padding:8px; text-align:left}
    .docs-content pre{background: var(--code); border-radius:12px; padding:14px; margin:16px 0; overflow:auto; box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 20px rgba(0,0,0,0.25)}
    .docs-content pre code{background: transparent !important}
    @media (max-width: 960px){ .docs-layout{grid-template-columns:1fr} }
  </style>
  <link rel=\"icon\" type=\"image/svg+xml\" href=\"../axl-logo.svg\"> 
  <link rel=\"stylesheet\" href=\"../vendor/fontawesome/css/all.min.css\" />
  <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark-dimmed.min.css\" />
</head>
<body>
  <header class=\"nav\" role=\"banner\" aria-label=\"Primary\">
    <div class=\"container nav-inner\">
      <a class=\"brand\" href=\"../index.html#top\" aria-label=\"AXL DB home\">
        <img class=\"logo\" src=\"../axl-logo-glyph.svg\" alt=\"AXL logo\" width=\"28\" height=\"28\"/>
        <span>AXL DB</span>
      </a>
      <nav class=\"nav-links\" aria-label=\"Main\">
        <a href=\"../index.html#features\">Features</a>
        <a href=\"../index.html#performance\">Performance</a>
        <a href=\"../index.html#use-cases\">Use cases</a>
        <a href=\"../index.html#get-started\">Get started</a>
        <a class=\"btn ghost\" href=\"https://github.com/hetoku/axl-db\" target=\"_blank\" rel=\"noopener noreferrer\"><i class=\"ico fa-brands fa-github\" aria-hidden=\"true\"></i>GitHub</a>
      </nav>
    </div>
  </header>
  <main class=\"features\" style=\"padding-top:28px\">
    <div class=\"container\">
      <div class=\"section-head\" style=\"align-items:center\"> 
        <h2>__TITLE__</h2>
        <a class=\"btn ghost\" href=\"../index.html\">Back to site</a>
      </div>
      <div class=\"docs-layout\">
        <aside class=\"docs-sidebar\">__SIDEBAR__</aside>
        <article class=\"docs-content\">__CONTENT__</article>
      </div>
    </div>
  </main>
  <footer class=\"footer\" role=\"contentinfo\">
    <div class=\"container row\" style=\"justify-content:space-between\">
      <div class=\"row\" style=\"gap:14px\">
        <a href=\"https://github.com/hetoku/axl-db\" target=\"_blank\" rel=\"noopener noreferrer\"><i class=\"ico fa-brands fa-github\"></i>GitHub</a>
        <a href=\"/docs/\"><i class=\"ico fa-regular fa-file-lines\"></i>Docs</a>
        <a href=\"https://github.com/hetoku/axl-db/blob/main/LICENSE\" target=\"_blank\" rel=\"noopener noreferrer\"><i class=\"ico fa-regular fa-star\"></i>License</a>
        <a href=\"https://github.com/hetoku/axl-db/issues\" target=\"_blank\" rel=\"noopener noreferrer\"><i class=\"ico fa-regular fa-message\"></i>Contact</a>
      </div>
      <div>© <span id=\"y\"></span> AXL DB. All rights reserved.</div>
    </div>
  </footer>
  <script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\"></script>
  <script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/c.min.js\"></script>
  <script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js\"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function(){
      if(window.hljs){ hljs.highlightAll(); }
      var y = document.getElementById('y'); if(y){ y.textContent = new Date().getFullYear(); }
      // Sidebar toggle persistence
      var nav = document.querySelector('.docs-nav');
      if(!nav) return;
      var lsKey = 'axl:docs:open';
      var openSet = new Set(JSON.parse(localStorage.getItem(lsKey) || '[]'));
      // restore expanded from localStorage
      openSet.forEach(function(key){
        var li = nav.querySelector('li[data-key="'+key+'"]');
        if(li){ li.classList.add('expanded'); var btn = li.querySelector('.nav-toggle'); if(btn){ btn.setAttribute('aria-expanded','true'); } }
      });
      nav.addEventListener('click', function(e){
        var btn = e.target.closest('.nav-toggle');
        if(!btn) return;
        e.preventDefault();
        var li = btn.closest('li');
        if(!li) return;
        var key = li.getAttribute('data-key') || '';
        var expanded = li.classList.toggle('expanded');
        btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        if(key){
          if(expanded) openSet.add(key); else openSet.delete(key);
          localStorage.setItem(lsKey, JSON.stringify(Array.from(openSet)));
        }
      });
    });
  </script>
</body>
</html>"""

    result = (
        tpl
        .replace("__CSS__", css)
        .replace("__SIDEBAR__", sidebar_html)
        .replace("__CONTENT__", content_html)
        .replace("__TITLE__", html.escape(page_title))
    )
    # Adjust asset/base links if rendering at site root (e.g., docs.html)
    if base_prefix != "..":
        result = result.replace("../", f"{base_prefix}/")
    return result


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_all() -> List[Path]:
    css = read_site_css()
    pages = discover_docs()
    written: List[Path] = []
    for page in pages:
        md_text = page.source_path.read_text(encoding="utf-8")
        html_content = convert_markdown(md_text)
        sidebar = build_sidebar(pages, page)
        full_html = render_template(css, sidebar, html_content, page.title, "..")
        write_file(page.output_path, full_html)
        written.append(page.output_path)
    # write an index redirect for /docs/ → /docs/index.html
    index_target = DOCS_OUT_DIR / "index.html"
    if not any(p.output_path.name == "index.html" for p in pages):
        redirect = """<!DOCTYPE html><meta http-equiv=refresh content="0; url=./index.html">
<link rel=\"canonical\" href=\"./index.html\">"""
        write_file(index_target, redirect)
        written.append(index_target)

    # Also generate a root-level docs.html using the docs index content
    root_page_src: Optional[DocPage] = None
    for p in pages:
        if p.output_path.name == "index.html":
            root_page_src = p
            break
    if root_page_src is None and pages:
        root_page_src = pages[0]
    if root_page_src is not None:
        md_text = root_page_src.source_path.read_text(encoding="utf-8")
        html_content = convert_markdown(md_text)
        sidebar = build_sidebar(pages, root_page_src)
        root_html = render_template(css, sidebar, html_content, root_page_src.title, base_prefix=".")
        out_page = SITE_DIR / "docs.html"
        write_file(out_page, root_html)
        written.append(out_page)

    return written


def watch_loop(interval: float = 1.0) -> None:
    print("👀 Watching for changes in docs/ ... Press Ctrl+C to stop")
    last_mtime = 0.0
    while True:
        mtimes = [p.stat().st_mtime for p in DOCS_SRC_DIR.rglob("*.md")] + [INDEX_HTML.stat().st_mtime]
        current = max(mtimes) if mtimes else 0.0
        if current > last_mtime:
            written = build_all()
            print(f"✅ Rebuilt {len(written)} files")
            last_mtime = current
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AXL DB docs site from Markdown")
    parser.add_argument("--watch", action="store_true", help="Rebuild on changes")
    args = parser.parse_args()

    if not DOCS_SRC_DIR.exists():
        print("📁 Creating docs/ with a starter index.md ...")
        DOCS_SRC_DIR.mkdir(parents=True, exist_ok=True)
        starter = """# AXL DB Documentation

Welcome to the AXL DB docs. This site is generated from Markdown files in the `docs/` folder.

## Getting started

```bash
git clone https://github.com/hetoku/axl-db
cd axl-db
make
./axl --help
```

## Example (C)

```c
#include "axl.h"
int main(void){ return 0; }
```
"""
        write_file(DOCS_SRC_DIR / "index.md", starter)

    written = build_all()
    print(f"✅ Built {len(written)} file(s) into {DOCS_OUT_DIR}")

    if args.watch:
        try:
            watch_loop()
        except KeyboardInterrupt:
            print("👋 Stopped watching")


if __name__ == "__main__":
    main()


