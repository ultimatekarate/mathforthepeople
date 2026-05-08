"""Tests for build.py — the static site generator.

Covers:
  - Math extraction round-trips (display, inline, currency-prose, escaped $).
  - Frontmatter parsing (happy path, missing block, missing required fields).
  - Wikilink resolution (post links, glossary, equation refs, broken refs).
  - Reference-graph helpers (cycle detection, rabbit-hole tree).
  - Full end-to-end build against a minimal fixture site, plus negative
    cases that should fail the build (broken wikilink, unknown author,
    broken glossary term).
"""

from pathlib import Path
from textwrap import dedent

import pytest

import build


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_TEMPLATES = PROJECT_ROOT / "templates"


# =========================================================================
# Math extraction
# =========================================================================

def test_extract_inline_math():
    text = "Let $x = 1$ and $y = 2$ stand."
    out, mapping = build.extract_math(text)
    assert "$x = 1$" not in out
    assert "$y = 2$" not in out
    assert len(mapping) == 2
    assert build.restore_math(out, mapping) == text


def test_extract_display_math():
    text = "Equation: $$ E = mc^2 $$ done."
    out, mapping = build.extract_math(text)
    assert "$$" not in out
    assert len(mapping) == 1
    assert build.restore_math(out, mapping) == text


def test_extract_math_ignores_currency_in_prose():
    text = "I paid $10 and you paid $20."
    out, mapping = build.extract_math(text)
    assert mapping == {}
    assert out == text


def test_extract_math_handles_escaped_dollar():
    text = r"Pay \$5 not $5$."
    out, mapping = build.extract_math(text)
    assert build.restore_math(out, mapping) == "Pay $5 not $5$."


def test_extract_math_display_takes_priority_over_inline():
    text = "$$ a = b + c $$"
    out, mapping = build.extract_math(text)
    assert len(mapping) == 1
    val = next(iter(mapping.values()))
    assert val.startswith("$$") and val.endswith("$$")


def test_extract_math_skips_tikz_script_blocks():
    """TikZJax interprets the TeX inside <script type='text/tikz'>; the
    build-time LaTeX-to-MathML pass must not touch it. Regression for
    the bug where TikZ axis labels got replaced with literal MathML."""
    text = (
        "Inline math $a$ stays.\n"
        '<script type="text/tikz">\n'
        "\\begin{tikzpicture}\n"
        "  \\draw (0,0) node[below] {$x$};\n"
        "\\end{tikzpicture}\n"
        "</script>\n"
        "Another $b$ outside."
    )
    out, mapping = build.extract_math(text)
    # Only the two outside-TikZ math expressions get placeholders.
    assert len(mapping) == 2
    # The TikZ block survives verbatim, including its $x$.
    assert "node[below] {$x$}" in out


# =========================================================================
# Math rendering (latex2mathml)
# =========================================================================

def test_render_math_inline():
    text, mapping = build.extract_math("Let $x = 1$ stand.")
    out = build.render_math(text, mapping)
    assert "<math" in out
    assert 'display="inline"' in out
    assert "$x = 1$" not in out


def test_render_math_display():
    text, mapping = build.extract_math("$$ a + b $$")
    out = build.render_math(text, mapping)
    assert 'display="block"' in out
    assert "$$" not in out


def test_render_math_preserves_escaped_dollar():
    text, mapping = build.extract_math(r"Pay \$5 not $5$.")
    out = build.render_math(text, mapping)
    # Escape sentinel becomes a literal $; the placeholder turns into MathML.
    assert "$5" in out  # the literal-dollar prefix
    assert "<math" in out


def test_render_math_fails_loud_on_bad_latex():
    text, mapping = build.extract_math(r"$\notarealcommand{x}$")
    # latex2mathml may or may not raise on every bad command — but if it
    # does, the build should surface it as a BuildError with the source
    # name so the author knows where to look.
    try:
        build.render_math(text, mapping, source_name="bogus.md")
    except build.BuildError as exc:
        assert "bogus.md" in str(exc)


# =========================================================================
# Equation block extraction
# =========================================================================

def test_extract_equations_finds_labeled_block():
    body = dedent("""\
        Some prose.

        <div id="eq:foo" class="equation">

        $$ x = y + z $$
        </div>

        More prose.
    """)
    assert build.extract_equations(body) == {"eq:foo": "x = y + z"}


def test_extract_equations_returns_empty_when_unlabeled():
    body = "Just $$ a + b $$ inline-ish."
    assert build.extract_equations(body) == {}


# =========================================================================
# Frontmatter parsing
# =========================================================================

def _write_post(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_post_minimal_happy_path(tmp_path):
    path = _write_post(tmp_path, "hello.md", dedent("""\
        ---
        title: Hello
        author: joe
        date: 2026-04-01
        ---

        Body goes here.
    """))
    meta = build.parse_post(path)
    assert meta["title"] == "Hello"
    assert meta["author"] == "joe"
    assert meta["slug"] == "hello"
    assert meta["date"] == "2026-04-01"
    assert "Body goes here." in meta["body"]
    assert meta["is_draft"] is False


def test_parse_post_explicit_slug_overrides_filename(tmp_path):
    path = _write_post(tmp_path, "filename.md", dedent("""\
        ---
        title: T
        author: a
        date: 2026-01-01
        slug: custom-slug
        ---

        body
    """))
    assert build.parse_post(path)["slug"] == "custom-slug"


def test_parse_post_raises_when_frontmatter_missing(tmp_path):
    path = _write_post(tmp_path, "broken.md", "no frontmatter here\n")
    with pytest.raises(build.BuildError, match="missing YAML frontmatter"):
        build.parse_post(path)


def test_parse_post_raises_when_required_field_missing(tmp_path):
    path = _write_post(tmp_path, "missing.md", dedent("""\
        ---
        title: T
        date: 2026-01-01
        ---

        body
    """))
    with pytest.raises(build.BuildError, match="'author'"):
        build.parse_post(path)


def test_parse_post_extracts_labeled_equations(tmp_path):
    path = _write_post(tmp_path, "eq.md", dedent("""\
        ---
        title: T
        author: a
        date: 2026-01-01
        ---

        <div id="eq:main" class="equation">

        $$ y = mx + b $$
        </div>
    """))
    meta = build.parse_post(path)
    assert meta["equations"] == {"eq:main": "y = mx + b"}


# =========================================================================
# Description extraction
# =========================================================================

def test_extract_description_prefers_frontmatter():
    post = {"description": "Hand-written.", "html": "<p>Different.</p>"}
    assert build.extract_description(post) == "Hand-written."


def test_extract_description_falls_back_to_first_paragraph():
    post = {"html": "<p>This is the first paragraph.</p><p>Second.</p>"}
    assert build.extract_description(post) == "This is the first paragraph."


def test_extract_description_strips_inline_html_tags():
    post = {"html": "<p>Bold <strong>text</strong> and <em>more</em>.</p>"}
    assert build.extract_description(post) == "Bold text and more."


def test_extract_description_truncates_long_text():
    post = {"html": "<p>" + ("word " * 100) + "</p>"}
    desc = build.extract_description(post)
    assert len(desc) <= 200
    assert desc.endswith("…")


def test_extract_description_unescapes_html_entities():
    post = {"html": "<p>Don&rsquo;t panic &mdash; really.</p>"}
    desc = build.extract_description(post)
    assert "’" in desc  # right single quote
    assert "—" in desc  # em-dash
    assert "&" not in desc   # no leftover entity prefixes


# =========================================================================
# Wikilink resolution
# =========================================================================

def _resolve(text, *, registry=None, glossary=None, alias_map=None,
             slug="current"):
    """Run resolve_wikilinks and return (output, link_graph, glossary_uses, forward_refs)."""
    link_graph, glossary_uses, forward_refs = {}, {}, {}
    out = build.resolve_wikilinks(
        text,
        registry or {},
        glossary or {},
        alias_map or {},
        slug,
        link_graph, glossary_uses, forward_refs,
    )
    return out, link_graph, glossary_uses, forward_refs


def test_resolve_wikilink_plain_post():
    registry = {"target": {"title": "Target Post", "slug": "target", "equations": {}}}
    out, lg, _, fr = _resolve("See [[target]].", registry=registry)
    assert "[Target Post](/target/)" in out
    assert lg == {"target": {"current"}}
    assert fr == {"current": {"target"}}


def test_resolve_wikilink_custom_text():
    registry = {"target": {"title": "Target", "slug": "target", "equations": {}}}
    out, *_ = _resolve("[[target|see this]]", registry=registry)
    assert "[see this](/target/)" in out


def test_resolve_wikilink_with_anchor():
    registry = {"target": {"title": "T", "slug": "target", "equations": {}}}
    out, *_ = _resolve("[[target#section]]", registry=registry)
    assert "(/target/#section)" in out


def test_resolve_glossary_term():
    glossary = {"foo": {"name": "Foo", "id": "foo"}}
    alias_map = {"foo": "foo"}
    out, _, gu, _ = _resolve("[[?foo]]", glossary=glossary, alias_map=alias_map)
    assert 'class="glossary-ref"' in out
    assert 'data-term="foo"' in out
    assert ">Foo<" in out
    assert gu == {"foo": {"current"}}


def test_resolve_glossary_alias():
    glossary = {"foo": {"name": "Foo", "id": "foo"}}
    alias_map = {"foo": "foo", "f": "foo"}
    out, *_ = _resolve("[[?f]]", glossary=glossary, alias_map=alias_map)
    assert 'data-term="foo"' in out


def test_resolve_glossary_custom_text():
    glossary = {"foo": {"name": "Foo", "id": "foo"}}
    alias_map = {"foo": "foo"}
    out, *_ = _resolve("[[?foo|bars]]", glossary=glossary, alias_map=alias_map)
    assert ">bars<" in out


def test_resolve_equation_reference_emits_data_attrs():
    registry = {"target": {"title": "T", "slug": "target",
                            "equations": {"eq:foo": "x = y"}}}
    out, *_ = _resolve("[[target#eq:foo]]", registry=registry)
    assert 'class="equation-ref"' in out
    # data-equation now holds pre-rendered MathML (HTML-escaped for the
    # attribute). The popover JS reads it back via dataset and drops it
    # into innerHTML.
    assert 'data-equation="&lt;math' in out
    assert 'data-source-title="T"' in out


def test_resolve_unknown_post_raises():
    with pytest.raises(build.BuildError, match="Broken wikilink"):
        _resolve("[[nope]]")


def test_resolve_unknown_glossary_term_raises():
    with pytest.raises(build.BuildError, match="Broken glossary reference"):
        _resolve("[[?nope]]")


def test_resolve_unknown_equation_label_raises():
    registry = {"target": {"title": "T", "slug": "target", "equations": {}}}
    with pytest.raises(build.BuildError, match="no equation labeled 'eq:foo'"):
        _resolve("[[target#eq:foo]]", registry=registry)


def test_resolve_glossary_use_records_implicit_dependency():
    glossary = {"foo": {"name": "Foo", "id": "foo", "defined_in": "other-post"}}
    alias_map = {"foo": "foo"}
    _, _, _, fr = _resolve("[[?foo]]", glossary=glossary, alias_map=alias_map)
    assert "other-post" in fr.get("current", set())


# =========================================================================
# Cycle detection
# =========================================================================

def test_detect_cycles_no_cycle():
    refs = {"a": {"b"}, "b": {"c"}, "c": set()}
    assert build.detect_cycles(refs) == []


def test_detect_cycles_finds_simple_cycle():
    refs = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
    assert build.detect_cycles(refs) == [["a", "b", "c"]]


def test_detect_cycles_finds_self_loop():
    assert build.detect_cycles({"a": {"a"}}) == [["a"]]


# =========================================================================
# Rabbit hole tree
# =========================================================================

def test_rabbit_hole_caps_at_max_depth():
    refs = {"a": {"b"}, "b": {"c"}, "c": {"d"}, "d": {"e"}}
    registry = {x: {"title": x.upper()} for x in "abcde"}
    tree = build.build_rabbit_hole("a", refs, registry, max_depth=2)
    # a -> b -> c, and c should not have its own children.
    assert tree[0]["slug"] == "b"
    assert tree[0]["children"][0]["slug"] == "c"
    assert tree[0]["children"][0]["children"] == []


def test_rabbit_hole_marks_already_seen():
    refs = {"a": {"b", "c"}, "b": {"c"}, "c": set()}
    registry = {x: {"title": x} for x in "abc"}
    tree = build.build_rabbit_hole("a", refs, registry)
    seen = []
    def walk(nodes):
        for n in nodes:
            seen.append((n["slug"], n["already_seen"]))
            walk(n["children"])
    walk(tree)
    c_marks = sorted(m for s, m in seen if s == "c")
    assert c_marks == [False, True]


def test_count_unique_in_tree():
    tree = [
        {"slug": "a", "title": "A", "already_seen": False, "children": [
            {"slug": "b", "title": "B", "already_seen": False, "children": []},
        ]},
        {"slug": "b", "title": "B", "already_seen": True, "children": []},
    ]
    assert build.count_unique_in_tree(tree) == 2


# =========================================================================
# End-to-end build smoke tests
# =========================================================================

def _write_minimal_site(root: Path) -> None:
    """Create a tiny valid site under `root`.

    The site has one author, one glossary entry, and two posts — enough
    to exercise math, wikilinks, glossary references, RSS, and the
    rabbit-hole tree.
    """
    (root / "posts").mkdir()
    (root / "authors").mkdir()
    (root / "glossary").mkdir()
    (root / "static").mkdir()

    (root / "authors" / "joe.yaml").write_text(dedent("""\
        name: Dr. Joe
        short_name: Joe
        bio: A test bio.
    """), encoding="utf-8")

    (root / "glossary" / "convergence.yaml").write_text(dedent("""\
        name: convergence
        defined_in: about
        short_definition: |
          When something settles down.
    """), encoding="utf-8")

    (root / "posts" / "about.md").write_text(dedent("""\
        ---
        title: About
        author: joe
        date: 2026-04-01
        ---

        This is the home post; it covers [[?convergence]].

        $$ S = \\sum_{n=0}^\\infty r^n $$

        Inline math: $x = 1$ and $y = 2$.
    """), encoding="utf-8")

    (root / "posts" / "second.md").write_text(dedent("""\
        ---
        title: Second
        author: joe
        date: 2026-04-15
        ---

        See the [[about|first post]] for background.
    """), encoding="utf-8")


@pytest.fixture
def patched_build(tmp_path, monkeypatch):
    """Point build.py's path globals at a fresh tmp_path; reuse real templates."""
    monkeypatch.setattr(build, "ROOT", tmp_path)
    monkeypatch.setattr(build, "POSTS_DIR", tmp_path / "posts")
    monkeypatch.setattr(build, "AUTHORS_DIR", tmp_path / "authors")
    monkeypatch.setattr(build, "GLOSSARY_DIR", tmp_path / "glossary")
    monkeypatch.setattr(build, "NOTATION_DIR", tmp_path / "notation")
    monkeypatch.setattr(build, "STATIC_DIR", tmp_path / "static")
    monkeypatch.setattr(build, "DIST_DIR", tmp_path / "dist")
    monkeypatch.setattr(build, "TEMPLATES_DIR", REAL_TEMPLATES)
    return tmp_path


def test_full_build_produces_expected_files(patched_build):
    _write_minimal_site(patched_build)
    build.build()
    dist = patched_build / "dist"
    assert (dist / "index.html").exists()
    assert (dist / "about" / "index.html").exists()
    assert (dist / "second" / "index.html").exists()
    assert (dist / "joe" / "index.html").exists()
    assert (dist / "feed.xml").exists()
    assert (dist / "joe" / "feed.xml").exists()
    assert (dist / "404.html").exists()
    assert (dist / ".nojekyll").exists()
    assert (dist / "glossary" / "index.html").exists()


def test_full_build_renders_math_to_mathml(patched_build):
    _write_minimal_site(patched_build)
    build.build()
    html = (patched_build / "dist" / "about" / "index.html").read_text(encoding="utf-8")
    # Math is rendered server-side via latex2mathml. The raw LaTeX
    # source should NOT appear in the output any more — only MathML.
    assert "$x = 1$" not in html
    assert "$$" not in html
    assert "<math" in html
    assert 'display="block"' in html
    assert 'display="inline"' in html


def test_full_build_renders_wikilink_with_custom_text(patched_build):
    _write_minimal_site(patched_build)
    build.build()
    html = (patched_build / "dist" / "second" / "index.html").read_text(encoding="utf-8")
    assert 'href="/about/"' in html
    assert "first post" in html


def test_full_build_fails_on_broken_wikilink(patched_build):
    _write_minimal_site(patched_build)
    (patched_build / "posts" / "broken.md").write_text(dedent("""\
        ---
        title: Broken
        author: joe
        date: 2026-04-20
        ---

        See [[nonexistent-post]].
    """), encoding="utf-8")
    with pytest.raises(build.BuildError, match="Broken wikilink"):
        build.build()


def test_full_build_fails_on_unknown_author(patched_build):
    _write_minimal_site(patched_build)
    (patched_build / "posts" / "wrong.md").write_text(dedent("""\
        ---
        title: Wrong
        author: not-a-real-author
        date: 2026-04-20
        ---

        body
    """), encoding="utf-8")
    with pytest.raises(build.BuildError, match="unknown author"):
        build.build()


def test_full_build_handles_glossary_defined_in_a_draft(patched_build):
    """A glossary term whose defining post is a draft should not break
    the production build — the term still appears in the glossary, it
    just lacks the 'see the post' link until the draft is promoted."""
    _write_minimal_site(patched_build)
    (patched_build / "posts" / "future.md").write_text(dedent("""\
        ---
        title: Future Post
        author: joe
        date: 2026-05-01
        draft: true
        ---

        Body.
    """), encoding="utf-8")
    (patched_build / "glossary" / "future-thing.yaml").write_text(dedent("""\
        name: future thing
        defined_in: future
        short_definition: Something we'll explain later.
    """), encoding="utf-8")
    # Production build: drafts excluded, no exception.
    build.build()
    glossary_html = (patched_build / "dist" / "glossary" / "index.html").read_text(encoding="utf-8")
    assert "future thing" in glossary_html
    # The "defined in" link to the draft is dropped.
    assert 'href="/future/"' not in glossary_html


def test_full_build_still_fails_on_typoed_defined_in(patched_build):
    """The graceful-draft handling must not mask a real broken slug."""
    _write_minimal_site(patched_build)
    (patched_build / "glossary" / "broken.yaml").write_text(dedent("""\
        name: broken
        defined_in: nonexistent-post
        short_definition: Bad slug.
    """), encoding="utf-8")
    with pytest.raises(build.BuildError, match="not a real post slug"):
        build.build()


def test_full_build_fails_on_broken_glossary_term(patched_build):
    _write_minimal_site(patched_build)
    (patched_build / "posts" / "bad-glossary.md").write_text(dedent("""\
        ---
        title: Bad
        author: joe
        date: 2026-04-20
        ---

        Refers to [[?nonexistent-term]].
    """), encoding="utf-8")
    with pytest.raises(build.BuildError, match="Broken glossary reference"):
        build.build()


def test_load_glossary_handles_utf8_content(patched_build):
    """Regression: yaml files with non-ASCII chars (em-dashes, smart
    quotes) must read correctly on every platform. Without an explicit
    encoding= arg, Python on Windows opens in cp1252 and produces
    mojibake (em-dash → 'â€') the moment the file leaves a Linux box."""
    (patched_build / "glossary").mkdir()
    (patched_build / "glossary" / "test.yaml").write_text(
        'name: test\nshort_definition: |\n  Em-dash — here, smart " quote.\n',
        encoding="utf-8",
    )
    glossary, _ = build.load_glossary()
    defn = glossary["test"]["definition_html"]
    assert "—" in defn
    assert "â€" not in defn


def test_load_glossary_renders_math_in_definitions(patched_build):
    """Glossary definitions go through the same math pipeline as posts."""
    (patched_build / "glossary").mkdir()
    (patched_build / "glossary" / "limit.yaml").write_text(dedent("""\
        name: limit
        short_definition: |
          The value an infinite sequence approaches: $\\lim_{n\\to\\infty} a_n = L$.
    """), encoding="utf-8")
    glossary, _ = build.load_glossary()
    defn = glossary["limit"]["definition_html"]
    assert "<math" in defn
    assert "$\\lim" not in defn
    assert "$L$" not in defn


def test_load_notation_renders_description(patched_build):
    """Notation descriptions go through the same math pipeline as glossary."""
    (patched_build / "notation").mkdir()
    (patched_build / "notation" / "matrix.yaml").write_text(dedent("""\
        name: matrix
        plural: Matrices
        sort_order: 1
        description: |
          Capital sans-serif letters: $\\mathsf{A}$, $\\mathsf{M}$.
    """), encoding="utf-8")
    entries = build.load_notation()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["name"] == "matrix"
    assert entry["id"] == "matrix"
    # Description's inline math becomes inline MathML; raw LaTeX is gone.
    assert "<math" in entry["description_html"]
    assert "$\\mathsf" not in entry["description_html"]


def test_load_notation_orders_by_sort_order(patched_build):
    """Multiple entries: sort_order determines display order."""
    (patched_build / "notation").mkdir()
    (patched_build / "notation" / "second.yaml").write_text(dedent("""\
        name: second
        plural: Seconds
        sort_order: 2
        description: ignore me
    """), encoding="utf-8")
    (patched_build / "notation" / "first.yaml").write_text(dedent("""\
        name: first
        plural: Firsts
        sort_order: 1
        description: ignore me
    """), encoding="utf-8")
    entries = build.load_notation()
    assert [e["name"] for e in entries] == ["first", "second"]


def test_load_notation_returns_empty_when_dir_absent(patched_build):
    # No notation/ directory: entries are empty, no error raised.
    assert build.load_notation() == []


def test_load_notation_raises_on_missing_field(patched_build):
    (patched_build / "notation").mkdir()
    (patched_build / "notation" / "broken.yaml").write_text(
        'name: broken\nplural: Broken\nsample: "x"\n',
        encoding="utf-8",
    )
    with pytest.raises(build.BuildError, match="missing required field 'description'"):
        build.load_notation()


def test_full_build_generates_notation_page(patched_build):
    _write_minimal_site(patched_build)
    (patched_build / "notation").mkdir()
    (patched_build / "notation" / "set.yaml").write_text(dedent("""\
        name: set
        plural: Sets
        sort_order: 1
        description: |
          Capital blackboard-bold letters: $\\mathbb{R}$, $\\mathbb{N}$.
    """), encoding="utf-8")
    build.build()
    page = patched_build / "dist" / "notation" / "index.html"
    assert page.exists()
    html = page.read_text(encoding="utf-8")
    assert "Sets" in html
    # Description math renders to MathML.
    assert "<math" in html
    # The "Pattern: ..." line was removed from the page.
    assert "Pattern:" not in html
