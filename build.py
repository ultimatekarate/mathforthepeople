"""
Build script for Math for the People.

Walks `posts/`, parses each Markdown file, resolves [[wikilinks]] and
[[?glossary-terms]] against registries (failing the build on broken
references), preserves LaTeX math through the pipeline, computes
equation-source data so cross-references can show inline previews, and
emits a static site to `dist/`.

Run: python build.py
"""

import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape as html_escape
from pathlib import Path

# Force stdout/stderr to UTF-8 so build messages with arrows, ellipses,
# etc. don't crash on Windows (which defaults to cp1252). No-op on
# Linux/macOS, harmless on any wrapped stream that lacks reconfigure().
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from latex2mathml.converter import convert as latex_to_mathml

# --- Config ----------------------------------------------------------------

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
AUTHORS_DIR = ROOT / "authors"
GLOSSARY_DIR = ROOT / "glossary"
DIST_DIR = ROOT / "dist"

SITE_CONFIG_PATH = ROOT / "site.yaml"

# Defaults used when site.yaml is missing or omits a key. The defaults
# match the existing site so deleting site.yaml doesn't change output.
DEFAULT_CONFIG = {
    "title": "Math for the People",
    "tagline": "Honest mathematics, in plain English.",
    "url": "https://example.com",
    "description": "A stripped-down blog about mathematics by Dr. Joe.",
    "max_rabbit_hole_depth": 3,
    "markdown_extensions": [
        "fenced_code", "tables", "smarty", "footnotes", "toc", "attr_list",
    ],
}


def load_site_config():
    """Read site.yaml (if present) on top of DEFAULT_CONFIG."""
    config = dict(DEFAULT_CONFIG)
    if SITE_CONFIG_PATH.exists():
        with SITE_CONFIG_PATH.open(encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
        config.update(user)
    return config


SITE = load_site_config()


class BuildError(Exception):
    """Raised when something is wrong with the source content."""


@dataclass(frozen=True)
class BuildStats:
    """What was written to dist/ during one call to build()."""
    posts: int
    authors: int
    drafts: int


# --- Page metadata helpers ------------------------------------------------
# Every rendered page gets a `page` dict that drives the <title> tag and
# Open Graph / Twitter Card meta tags. Centralizing this here means the
# templates stay simple — they just read `page.title`, `page.description`,
# `page.url`, `page.og_type`.

def make_page(title, description=None, path="/", og_type="website"):
    """Build the metadata dict that gets passed to every template.

    `title` is the page-specific bit; we suffix the site title onto it
    unless they're already equal (which is the case for the homepage).
    """
    full_title = title if title == SITE["title"] else f"{title} · {SITE['title']}"
    return {
        "title": full_title,
        "description": description or SITE["description"],
        "url": SITE["url"].rstrip("/") + path,
        "og_type": og_type,
    }


def extract_description(post, fallback=None):
    """Pull a short description for og:description / RSS / etc.

    Order of preference:
      1. `description:` field in the post's frontmatter (author wrote one).
      2. First paragraph of the rendered HTML, stripped of tags and
         truncated to ~200 characters at a word boundary.
      3. The provided fallback (usually the site description).
    """
    if post.get("description"):
        return post["description"]
    match = re.search(r"<p>(.+?)</p>", post.get("html", ""), re.DOTALL)
    if not match:
        return fallback or SITE["description"]
    text = re.sub(r"<[^>]+>", "", match.group(1))
    # The markdown step has already converted things like apostrophes to
    # entities (&rsquo;, &mdash;). Decode them so the final meta tag holds
    # the actual character — otherwise Jinja's autoescape would emit
    # &amp;rsquo; and break previews everywhere.
    from html import unescape
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 200:
        text = text[:197].rsplit(" ", 1)[0] + "…"
    return text or fallback or SITE["description"]


# --- Math preservation -----------------------------------------------------
# Markdown will mangle $...$ if we let it. We swap math out for placeholders
# before running the parser. After markdown is done, render_math() puts
# rendered MathML back where the placeholders are; restore_math() (kept for
# tests) puts the original LaTeX source back instead.

MATH_PLACEHOLDER = "\x00MATHBLOCK{i}\x00"
ESCAPED_DOLLAR = "\x01"

# <script type="text/tikz">...</script> blocks contain raw TeX that the
# browser's TikZJax interprets at runtime. Their $...$ is for TikZ, not
# for our LaTeX→MathML pass — extract_math must leave them alone.
TIKZ_BLOCK_RE = re.compile(
    r'<script\s+type="text/tikz">[\s\S]*?</script>',
    re.IGNORECASE,
)


def extract_math(text: str):
    """Replace $$...$$ and $...$ with placeholders. Return (text, mapping).

    TikZ script blocks are passed through untouched — their math is for
    the browser's TikZJax, not for our build-time MathML rendering.
    """
    # Honor escaped dollars: \$ becomes a sentinel we restore at the end.
    text = text.replace(r"\$", ESCAPED_DOLLAR)

    placeholders = {}
    counter = [0]

    def stash(match, display: bool):
        i = counter[0]
        counter[0] += 1
        key = MATH_PLACEHOLDER.format(i=i)
        delim = "$$" if display else "$"
        placeholders[key] = f"{delim}{match.group(1)}{delim}"
        return key

    def process(chunk: str) -> str:
        # Display math first so $$...$$ isn't shredded by the inline pattern.
        chunk = re.sub(r"\$\$([\s\S]+?)\$\$", lambda m: stash(m, True), chunk)
        # Inline math: require non-space adjacent to delimiters so "$10 vs $20"
        # in prose is left alone. Newlines also break inline math.
        chunk = re.sub(
            r"\$(?!\s)([^$\n]+?)(?<!\s)\$",
            lambda m: stash(m, False),
            chunk,
        )
        return chunk

    # Walk the text, preserving TikZ blocks verbatim and processing the
    # rest through the math regex.
    out = []
    last = 0
    for m in TIKZ_BLOCK_RE.finditer(text):
        out.append(process(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(process(text[last:]))
    return "".join(out), placeholders


def restore_math(html: str, placeholders: dict) -> str:
    """Put the original $...$ / $$...$$ source back. Used by tests."""
    for key, original in placeholders.items():
        html = html.replace(key, original)
    return html.replace(ESCAPED_DOLLAR, "$")


def render_math(html: str, placeholders: dict, source_name: str = "") -> str:
    """Replace placeholders with MathML rendered server-side via latex2mathml.

    Inline math becomes display="inline"; $$...$$ becomes display="block".
    A bad LaTeX expression fails the build with a message that names the
    source file so the author can find it.
    """
    for key, original in placeholders.items():
        if original.startswith("$$") and original.endswith("$$"):
            tex = original[2:-2].strip()
            display = "block"
        else:
            tex = original[1:-1].strip()
            display = "inline"
        try:
            mathml = latex_to_mathml(tex, display=display)
        except Exception as exc:
            where = f" in '{source_name}'" if source_name else ""
            raise BuildError(
                f"Could not render LaTeX{where}: '{tex}' — {exc}"
            ) from exc
        html = html.replace(key, mathml)
    return html.replace(ESCAPED_DOLLAR, "$")


# --- Wikilinks -------------------------------------------------------------
# Syntax we support inside posts:
#   [[slug]]                  -> link with the target post's title as text
#   [[slug|custom text]]      -> link with custom text
#   [[slug#anchor]]           -> link to an anchor inside the target
#   [[slug#anchor|text]]      -> both
#   [[?term-id]]              -> glossary term lookup, popover on hover
#   [[?term-id|custom text]]  -> glossary term with custom display text
#
# When the anchor matches an equation label (eq:foo) AND the target post
# has a labeled equation by that name, the link gets a data-equation
# attribute so the reader sees the rendered equation on hover.
#
# Broken references (unknown slug, unknown term, missing equation label)
# fail the build, so dead references can't ship.

WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")

# Pattern for equation blocks in post bodies. Matches:
#   <div id="eq:LABEL" ...> ... $$ MATH $$ ... </div>
# Captures the label and the math source.
EQUATION_BLOCK_RE = re.compile(
    r'<div\s+id="(eq:[^"]+)"[^>]*>\s*\n+\s*\$\$([\s\S]+?)\$\$',
)


def extract_equations(body: str) -> dict:
    """Return {label: math_source} for every <div id="eq:..."> block in body."""
    return {m.group(1): m.group(2).strip() for m in EQUATION_BLOCK_RE.finditer(body)}


def resolve_wikilinks(
    text: str,
    registry: dict,
    glossary: dict,
    alias_map: dict,
    current_slug: str,
    link_graph: dict,
    glossary_uses: dict,
    forward_refs: dict,
) -> str:
    def replace(match):
        body = match.group(1).strip()

        # ---- Glossary reference: [[?term]] or [[?term|custom text]] ----
        if body.startswith("?"):
            inner = body[1:]
            term_part, _, custom = inner.partition("|")
            requested = term_part.strip()
            custom = custom.strip()
            canonical = alias_map.get(requested)
            if canonical is None:
                raise BuildError(
                    f"Broken glossary reference in '{current_slug}.md': "
                    f"[[?{requested}]] — no glossary term with id '{requested}'. "
                    f"Add glossary/{requested}.yaml or fix the spelling."
                )
            entry = glossary[canonical]
            display = html_escape(custom or entry["name"])
            glossary_uses.setdefault(canonical, set()).add(current_slug)
            # If the term has a defining post, that post is an implicit
            # dependency of this one. Record it for the rabbit hole graph.
            defined_in = entry.get("defined_in")
            if defined_in and defined_in != current_slug:
                forward_refs.setdefault(current_slug, set()).add(defined_in)
            return (
                f'<a href="/glossary/#{canonical}" class="glossary-ref" '
                f'data-term="{canonical}">{display}</a>'
            )

        # ---- Post reference: [[slug]] / [[slug#anchor]] / with |text ----
        target, _, link_text = body.partition("|")
        slug, _, anchor = target.partition("#")
        slug = slug.strip()
        anchor = anchor.strip()
        link_text = link_text.strip()

        if slug not in registry:
            raise BuildError(
                f"Broken wikilink in '{current_slug}.md': [[{body}]] "
                f"— no post with slug '{slug}'"
            )

        target_post = registry[slug]
        url = f"/{slug}/"
        if anchor:
            url += f"#{anchor}"
        text_out = link_text or target_post["title"]

        # Track the link so the target can show "Referenced by" later.
        link_graph.setdefault(slug, set()).add(current_slug)
        # Track the forward reference for the rabbit hole graph (skip
        # self-references).
        if slug != current_slug:
            forward_refs.setdefault(current_slug, set()).add(slug)

        # ---- Equation reference: emit HTML so popover JS can find it ----
        if anchor.startswith("eq:"):
            equations = target_post.get("equations", {})
            if anchor not in equations:
                raise BuildError(
                    f"Broken equation reference in '{current_slug}.md': "
                    f"[[{body}]] — post '{slug}' has no equation labeled "
                    f"'{anchor}'. Wrap the equation in "
                    f"<div id=\"{anchor}\" class=\"equation\">...$$...$$...</div>"
                )
            math = equations[anchor]
            try:
                math_html = latex_to_mathml(math, display="block")
            except Exception as exc:
                raise BuildError(
                    f"Could not render equation '{anchor}' in '{slug}.md' "
                    f"(referenced from '{current_slug}.md'): '{math}' — {exc}"
                ) from exc
            # MathML goes into data-equation as escaped attribute text;
            # popovers.js reads it back via dataset and assigns it to
            # innerHTML, where it parses as live MathML again.
            return (
                f'<a href="{url}" class="equation-ref" '
                f'data-equation="{html_escape(math_html)}" '
                f'data-source-title="{html_escape(target_post["title"])}">'
                f'{html_escape(text_out)}</a>'
            )

        # ---- Plain post link: emit a markdown link ----
        return f"[{text_out}]({url})"

    return WIKILINK_RE.sub(replace, text)


# --- Loading ---------------------------------------------------------------

def load_authors() -> dict:
    authors = {}
    for path in sorted(AUTHORS_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        key = path.stem
        # Render the bio's markdown so author pages can use it as HTML.
        data["bio_html"] = markdown.markdown(data.get("bio", ""))
        authors[key] = data
    if not authors:
        raise BuildError("No author files found in authors/")
    return authors


def load_glossary():
    """Load glossary entries. Returns (entries, alias_map).

    entries: {
        canonical_id: {name, 
            short_definition, 
            definition_html,
            defined_in?, 
            aliases?, 
            id}
        }
    alias_map: {any_id_or_alias: canonical_id}
    """
    entries = {}
    alias_map = {}
    if not GLOSSARY_DIR.exists():
        return entries, alias_map

    for path in sorted(GLOSSARY_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        term_id = path.stem
        for field in ("name", "short_definition"):
            if field not in data:
                raise BuildError(
                    f"glossary/{path.name}: missing required field '{field}'"
                )
        # Render the definition as inline-ish markdown. Allows links,
        # italics, code, plus LaTeX math via the same extract → markdown →
        # render_math pipeline used for post bodies. Strip the wrapping
        # <p> for cleaner display in popovers.
        text, math_map = extract_math(data["short_definition"])
        rendered = markdown.markdown(text).strip()
        rendered = render_math(rendered, math_map,
                               source_name=f"glossary/{path.name}")
        if rendered.startswith("<p>") and rendered.endswith("</p>") and \
                rendered.count("<p>") == 1:
            rendered = rendered[3:-4]
        data["definition_html"] = rendered
        data["id"] = term_id
        entries[term_id] = data
        alias_map[term_id] = term_id
        for alias in data.get("aliases", []) or []:
            if alias in alias_map and alias_map[alias] != term_id:
                raise BuildError(
                    f"glossary/{path.name}: alias '{alias}' already used by "
                    f"glossary/{alias_map[alias]}.yaml"
                )
            alias_map[alias] = term_id
    return entries, alias_map


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_post(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise BuildError(f"{path.name}: missing YAML frontmatter")
    meta = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)

    # Required fields
    for field in ("title", "author", "date"):
        if field not in meta:
            raise BuildError(f"{path.name}: missing required frontmatter field '{field}'")

    # Slug defaults to the filename without .md
    meta.setdefault("slug", path.stem)
    # Coerce date to a datetime (PyYAML gives a date, not a datetime, for plain YYYY-MM-DD)
    if isinstance(meta["date"], datetime):
        meta["date_dt"] = meta["date"]
    else:
        meta["date_dt"] = datetime.combine(meta["date"], datetime.min.time())
    meta["date_dt"] = meta["date_dt"].replace(tzinfo=timezone.utc)
    meta["date"] = meta["date_dt"].strftime("%Y-%m-%d")
    meta["date_human"] = meta["date_dt"].strftime("%B %d, %Y")
    meta["body"] = body
    meta["source"] = path.name
    # Coerce the optional `draft` field to a bool. Drafts are excluded from
    # production builds but included by the dev server (see serve.py).
    meta["is_draft"] = bool(meta.get("draft", False))
    # Pre-scan for labeled equations so other posts can reference them
    # with [[slug#eq:label]] and get inline previews on hover.
    meta["equations"] = extract_equations(body)
    return meta


def load_posts() -> list:
    posts = [parse_post(p) for p in sorted(POSTS_DIR.glob("*.md"))]
    posts.sort(key=lambda p: p["date_dt"], reverse=True)
    return posts


# --- Rendering -------------------------------------------------------------

def make_markdown_parser():
    # Standard library Markdown with extensions for fenced code, tables,
    # smart typography, footnotes, and heading IDs (so anchors work).
    # Extension list is configurable via site.yaml.
    return markdown.Markdown(
        extensions=SITE["markdown_extensions"],
        extension_configs={"toc": {"permalink": False}},
    )


def render_post_body(post, registry, glossary, alias_map,
                     link_graph, glossary_uses, forward_refs):
    body = post["body"]
    # 1. Pull out math so markdown can't touch it.
    body, math_map = extract_math(body)
    # 2. Resolve [[wikilinks]] and [[?glossary]] and [[slug#eq:foo]].
    body = resolve_wikilinks(
        body, registry, glossary, alias_map,
        post["slug"], link_graph, glossary_uses, forward_refs,
    )
    # 3. Run markdown.
    md = make_markdown_parser()
    html = md.convert(body)
    # 4. Render the math to MathML at build time. Browsers handle MathML
    #    natively — no KaTeX, no CDN, no flash of unstyled math.
    html = render_math(html, math_map, source_name=post.get("source", post["slug"]))
    return html


# --- Reference graph ------------------------------------------------------
# After all posts are rendered, `forward_refs[slug]` holds the set of post
# slugs that the post at `slug` references (directly via [[wikilink]] OR
# implicitly via [[?glossary-term]] when the term has a defining post).
#
# The expectation is that this graph is a DAG — the structure of pre-
# requisites between posts. We:
#   1. Detect cycles and warn (without failing the build), so the author
#      can decide whether the cycle is intentional or a mistake.
#   2. Build, per post, a rabbit-hole tree: the transitive closure of its
#      references shown as a nested structure, with depth capped and
#      already-seen nodes marked rather than re-expanded.

def detect_cycles(forward_refs):
    """Return a deduped, canonicalized list of cycles in the reference graph.

    Each cycle is a list of slugs in traversal order, e.g. ['a', 'b', 'c']
    means a -> b -> c -> a. The list is rotated so its smallest slug
    appears first, which makes equivalent cycles compare equal.
    """
    cycles = set()
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {}

    all_nodes = set(forward_refs)
    for refs in forward_refs.values():
        all_nodes.update(refs)

    def dfs(node, path):
        color[node] = GRAY
        for nxt in sorted(forward_refs.get(node, set())):
            state = color.get(nxt, WHITE)
            if state == GRAY:
                # Found a back-edge: nxt is somewhere in `path`.
                idx = path.index(nxt)
                cycle = path[idx:]
                pivot = cycle.index(min(cycle))
                cycles.add(tuple(cycle[pivot:] + cycle[:pivot]))
            elif state == WHITE:
                dfs(nxt, path + [nxt])
        color[node] = BLACK

    for node in sorted(all_nodes):
        if color.get(node, WHITE) == WHITE:
            dfs(node, [node])

    return [list(c) for c in sorted(cycles)]


def build_rabbit_hole(post_slug, forward_refs, registry, max_depth=3):
    """Compute the per-post reference tree.

    The tree is rendered top-down: direct references at the root level,
    each followed by its own references, recursively. Already-seen nodes
    (anywhere in the tree) are flagged but not re-expanded — keeps deep
    graphs readable without losing the "this also leads here" signal.
    Self-loops and cycles are broken implicitly: a node is never expanded
    if it appears among its own ancestors in the current path.
    """
    seen_globally = set()

    def expand(slug, depth, ancestors):
        children = []
        refs = sorted(
            forward_refs.get(slug, set()),
            key=lambda s: registry[s]["title"].lower() if s in registry else s,
        )
        for ref in refs:
            if ref not in registry:
                continue  # safety net; shouldn't happen for validated graphs
            if ref in ancestors:
                continue  # cycle — drop silently; warning printed elsewhere
            already = ref in seen_globally
            seen_globally.add(ref)
            sub = []
            if not already and depth + 1 < max_depth:
                sub = expand(ref, depth + 1, ancestors | {ref})
            children.append({
                "slug": ref,
                "title": registry[ref]["title"],
                "already_seen": already,
                "children": sub,
            })
        return children

    return expand(post_slug, 0, {post_slug})


def count_unique_in_tree(tree):
    """Total distinct posts in a rabbit-hole tree (for the section header)."""
    seen = set()
    def walk(nodes):
        for n in nodes:
            seen.add(n["slug"])
            walk(n["children"])
    walk(tree)
    return len(seen)


# --- Output ----------------------------------------------------------------

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_rss(env, channel: dict, items: list, out: Path):
    template = env.get_template("rss.xml")
    write(out, template.render(channel=channel, items=items, build_date=format_datetime(datetime.now(timezone.utc))))


def build(include_drafts=False):
    # Build into a staging directory and only swap it into place on
    # success. This way a failed build (e.g. a broken wikilink during
    # `python serve.py`) doesn't leave dist/ empty — the browser keeps
    # showing the last good version until you fix the error.
    staging = ROOT / "dist.new"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    try:
        stats = _build_into_staging(staging, include_drafts=include_drafts)
    except Exception:
        # Leave the previous dist/ untouched and propagate the error.
        shutil.rmtree(staging, ignore_errors=True)
        raise

    # Atomic-ish swap. There's a very brief window where dist/ doesn't
    # exist; livereload doesn't care.
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    staging.rename(DIST_DIR)
    summary = f"Built {stats.posts} post(s) by {stats.authors} author(s)"
    if stats.drafts:
        summary += f" (including {stats.drafts} draft{'s' if stats.drafts != 1 else ''})"
    print(f"{summary} → {DIST_DIR}/")


def _build_into_staging(dist_dir: Path, include_drafts=False) -> BuildStats:

    authors = load_authors()
    glossary, alias_map = load_glossary()
    posts = load_posts()

    # Drafts: hidden in production, surfaced in dev (serve.py passes
    # include_drafts=True). Filtering happens before any other validation
    # or rendering, so a half-broken draft never blocks a production build.
    drafts = [p for p in posts if p["is_draft"]]
    if not include_drafts:
        posts = [p for p in posts if not p["is_draft"]]
    drafts_count = len([p for p in posts if p["is_draft"]])

    # Validate authors referenced by posts.
    for post in posts:
        if post["author"] not in authors:
            raise BuildError(
                f"{post['source']}: unknown author '{post['author']}'. "
                f"Known authors: {sorted(authors)}"
            )

    # Validate glossary 'defined_in' fields point to real posts.
    post_slugs = {p["slug"] for p in posts}
    for term_id, entry in glossary.items():
        defined_in = entry.get("defined_in")
        if defined_in and defined_in not in post_slugs:
            raise BuildError(
                f"glossary/{term_id}.yaml: defined_in '{defined_in}' "
                f"is not a real post slug"
            )

    # Registry for wikilink resolution: slug -> info needed by the resolver,
    # including the equation table extracted at parse time.
    registry = {
        p["slug"]: {
            "title": p["title"],
            "slug": p["slug"],
            "equations": p["equations"],
        }
        for p in posts
    }

    # Two-pass build: render bodies first (collecting the link graph and
    # glossary usage), then render templates (so we can include backlinks,
    # per-post "background concepts", and rabbit-hole reference trees).
    link_graph = {}        # slug -> set of slugs that link to it
    glossary_uses = {}     # term_id -> set of post slugs using it
    forward_refs = {}      # slug -> set of slugs it references (for rabbit hole)
    for post in posts:
        post["html"] = render_post_body(
            post, registry, glossary, alias_map,
            link_graph, glossary_uses, forward_refs,
        )

    # Cycle detection on the reference graph. We don't fail the build on
    # cycles — sometimes two posts genuinely refer to each other — but we
    # warn loudly so the author can decide.
    cycles = detect_cycles(forward_refs)
    if cycles:
        print("\n  Reference cycles detected (the graph is not a DAG):",
              file=sys.stderr)
        for cycle in cycles:
            arrows = " → ".join(cycle + [cycle[0]])
            print(f"    {arrows}", file=sys.stderr)
        print(
            "  These cycles will still build, but rabbit-hole trees skip "
            "the back-edge so readers don't loop forever.\n",
            file=sys.stderr,
        )

    # Compute "background concepts" for each post: every glossary term it
    # uses whose definition lives in another post. This shows the reader,
    # at a glance, what prior posts they might want to read first.
    def background_for(post_slug):
        out = []
        for term_id, used_in in glossary_uses.items():
            if post_slug not in used_in:
                continue
            entry = glossary[term_id]
            defined_in = entry.get("defined_in")
            if defined_in == post_slug:
                continue  # this post defines the term; not background
            if defined_in:
                out.append({
                    "id": term_id,
                    "name": entry["name"],
                    "defined_in": defined_in,
                    "defined_in_title": registry[defined_in]["title"],
                })
            else:
                out.append({
                    "id": term_id,
                    "name": entry["name"],
                    "defined_in": None,
                    "defined_in_title": None,
                })
        out.sort(key=lambda e: e["name"].lower())
        return out

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = SITE
    env.globals["year"] = datetime.now(timezone.utc).year

    # Glossary data exposed to the popover JS as a single JSON blob in
    # every page's <head>. Keeps the popover machinery simple: it just
    # looks up window.GLOSSARY[term_id].
    glossary_json = {
        tid: {
            "name": e["name"],
            "definition_html": e["definition_html"],
            "defined_in": e.get("defined_in"),
            "defined_in_url": f"/{e['defined_in']}/" if e.get("defined_in") else None,
        }
        for tid, e in glossary.items()
    }
    env.globals["glossary_json"] = json.dumps(glossary_json, ensure_ascii=False)

    # Render each post.
    post_template = env.get_template("post.html")
    for post in posts:
        backlinks = [
            {"slug": s, "title": registry[s]["title"]}
            for s in sorted(link_graph.get(post["slug"], set()))
        ]
        rabbit_hole = build_rabbit_hole(
            post["slug"], forward_refs, registry,
            max_depth=SITE["max_rabbit_hole_depth"],
        )
        post_description = extract_description(post)
        html = post_template.render(
            page=make_page(
                post["title"],
                description=post_description,
                path=f"/{post['slug']}/",
                og_type="article",
            ),
            post=post,
            author=authors[post["author"]],
            backlinks=backlinks,
            background=background_for(post["slug"]),
            rabbit_hole=rabbit_hole,
            rabbit_hole_size=count_unique_in_tree(rabbit_hole),
        )
        write(dist_dir / post["slug"] / "index.html", html)

    # Index page (all posts, with author filter).
    index_template = env.get_template("index.html")
    write(
        dist_dir / "index.html",
        index_template.render(
            page=make_page(SITE["title"], description=SITE["tagline"], path="/"),
            posts=posts, authors=authors,
        ),
    )

    # Glossary index page.
    if glossary:
        # For each entry, list all posts that use the term (reverse index).
        glossary_entries = []
        for term_id in sorted(glossary, key=lambda t: glossary[t]["name"].lower()):
            entry = glossary[term_id]
            uses = sorted(glossary_uses.get(term_id, set()))
            glossary_entries.append({
                **entry,
                "defined_in_title": (
                    registry[entry["defined_in"]]["title"]
                    if entry.get("defined_in") else None
                ),
                "used_in": [
                    {"slug": s, "title": registry[s]["title"]} for s in uses
                ],
            })
        glossary_template = env.get_template("glossary.html")
        write(
            dist_dir / "glossary" / "index.html",
            glossary_template.render(
                page=make_page(
                    "Glossary",
                    description="Named concepts used across the blog.",
                    path="/glossary/",
                ),
                entries=glossary_entries,
            ),
        )

    # One landing page per author.
    author_template = env.get_template("author.html")
    for key, author in authors.items():
        author_posts = [p for p in posts if p["author"] == key]
        # Use first paragraph of bio (plain text) as the OG description.
        bio_text = re.sub(r"<[^>]+>", "", author.get("bio_html", ""))
        bio_text = re.sub(r"\s+", " ", bio_text).strip()
        write(
            dist_dir / key / "index.html",
            author_template.render(
                page=make_page(
                    author["name"],
                    description=bio_text[:200] or SITE["description"],
                    path=f"/{key}/",
                ),
                author=author, author_key=key, posts=author_posts,
            ),
        )

    # 404 page. GitHub Pages serves /404.html for any unmatched URL.
    not_found_template = env.get_template("404.html")
    write(
        dist_dir / "404.html",
        not_found_template.render(
            page=make_page(
                "Not found",
                description="This page doesn't exist on the blog.",
                path="/404.html",
            ),
        ),
    )

    # RSS feeds: combined and per-author.
    def rss_items(post_list):
        return [
            {
                "title": p["title"],
                "link": f"{SITE['url']}/{p['slug']}/",
                "guid": f"{SITE['url']}/{p['slug']}/",
                "pub_date": format_datetime(p["date_dt"]),
                "description": p["html"],
                "author": authors[p["author"]]["name"],
            }
            for p in post_list
        ]

    render_rss(
        env,
        channel={"title": SITE["title"], "link": SITE["url"], "description": SITE["description"]},
        items=rss_items(posts),
        out=dist_dir / "feed.xml",
    )
    for key, author in authors.items():
        author_posts = [p for p in posts if p["author"] == key]
        render_rss(
            env,
            channel={
                "title": f"{SITE['title']} — {author['name']}",
                "link": f"{SITE['url']}/{key}/",
                "description": f"Posts by {author['name']}.",
            },
            items=rss_items(author_posts),
            out=dist_dir / key / "feed.xml",
        )

    # Static assets.
    if STATIC_DIR.exists():
        for src in STATIC_DIR.rglob("*"):
            if src.is_file():
                dst = dist_dir / src.relative_to(STATIC_DIR)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    # CNAME (for GitHub Pages custom domain) lives at the repo root and
    # gets copied verbatim if present.
    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, dist_dir / "CNAME")

    # .nojekyll tells GitHub Pages to skip its own Jekyll build step.
    (dist_dir / ".nojekyll").touch()

    return BuildStats(posts=len(posts), authors=len(authors), drafts=drafts_count)


if __name__ == "__main__":
    try:
        build()
    except BuildError as e:
        print(f"\nBuild failed: {e}\n", file=sys.stderr)
        sys.exit(1)
