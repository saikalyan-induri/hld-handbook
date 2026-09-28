"""
Generates the static multi-page HLD Handbook site (this directory) from the
single-file source at ../hld-handbook.html.

Run: python3 build.py
Reads:  ../hld-handbook.html
Writes: index.html, prereq.html, p1.html..p20.html, patterns.html,
        search-index.json, assets/style.css, assets/app.js, .nojekyll,
        README.md

Adapted from the sibling LLD Handbook's build.py. Differences from that
script (see comments at each divergence point below):
  1. Source has 22 sections: prereq, p1..p20, patterns (vs. LLD's p1..p21,
     synthesis) -- section-id regex and subsection-id regex are broadened.
  2. Diagrams here are live-rendered client-side Mermaid.js (v10.9.1, CDN),
     not pre-baked SVG -- every generated page needs the Mermaid CDN
     <script> + init block appended to SCRIPTS.
  3. No code_translations.json / language-tab feature -- HLD's <pre><code>
     blocks are API contracts, not per-language pseudocode pairs, so
     with_lang_tabs() and the whole code-tabs branch of app.js are dropped.
  4. "patterns" is the special final synthesis-style page (like LLD's
     "synthesis"): excluded from the numbered nav loop/card grid and
     appended manually as the last nav link + linked from the home page.
  5. "prereq" is numbered 0 and behaves like a normal nav/card item, with a
     special-cased "Beginner" difficulty tag (its badge text doesn't
     contain a normal difficulty word) so it isn't invisible to the
     difficulty filter.
"""
import re
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "hld-handbook.html"

src = SRC.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# 1. Extract the original <style> body (light-mode palette + all existing
#    component classes: .problem-title, .section-toc, .diagram, etc.)
# ---------------------------------------------------------------------------
style_m = re.search(r"<style>(.*?)</style>", src, re.S)
orig_css = style_m.group(1).strip()

# ---------------------------------------------------------------------------
# 2. Extract the Mermaid CDN script + init block from the end of the source
#    so every generated page can render its live "mermaid diagram" divs.
# ---------------------------------------------------------------------------
mermaid_m = re.search(
    r'(<script src="https://cdn\.jsdelivr\.net/npm/mermaid[^"]*"></script>\s*'
    r'<script>\s*mermaid\.initialize\(\{.*?\}\);\s*</script>)', src, re.S)
MERMAID_SCRIPTS = mermaid_m.group(1).strip()

# ---------------------------------------------------------------------------
# 3. Extract the 22 <section id="prereq|p\d+|patterns" class="page-break">
#    ... </section> blocks. Confirmed non-nested / sequential, so pairing by
#    index position is safe.
# ---------------------------------------------------------------------------
starts = [(m.group(1), m.end()) for m in re.finditer(
    r'<section id="(prereq|p\d+|patterns)" class="page-break">', src)]
ends = [m.start() for m in re.finditer(r"</section>", src)]
assert len(starts) == len(ends) == 22, f"expected 22/22 section pairs, got {len(starts)}/{len(ends)}"

sections = [(sid, src[s_end:e_start].strip()) for (sid, s_end), e_start in zip(starts, ends)]

TITLE_RE = re.compile(
    r'<h1 class="problem-title">(?:(\d+)\.\s*)?(.*?)\s*<span class="badge">(.*?)</span></h1>')
SUBSEC_RE = re.compile(r'<h3 id="((?:prereq|patterns|p\d+)-[a-z]+)">([A-Z]{1,2})\.\s*(.*?)</h3>')
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s):
    return TAG_RE.sub("", s).strip()


problems = []
for sid, inner in sections:
    m = TITLE_RE.search(inner)
    num, name, badge = m.groups()
    name = strip_tags(name)
    badge = strip_tags(badge)
    subs = [(mm.group(1), mm.group(2), strip_tags(mm.group(3))) for mm in SUBSEC_RE.finditer(inner)]
    problems.append({"sid": sid, "num": num, "name": name, "badge": badge, "inner": inner, "subs": subs})


def buckets_for(sid, badge):
    if sid == "prereq":
        return "Beginner"
    return " ".join(b for b in ("Beginner", "Intermediate", "Advanced") if b.lower() in badge.lower())


# ---------------------------------------------------------------------------
# 4. Sidebar (identical constant on every page; "active" link is applied
#    client-side by assets/app.js, so no per-page templating needed here)
# ---------------------------------------------------------------------------
nav_items = []
for p in problems:
    if p["sid"] == "patterns":
        continue
    nav_items.append(
        f'    <li><a href="{p["sid"]}.html" data-page="{p["sid"]}.html">{p["num"]}. {p["name"]}</a></li>')
nav_html = "\n".join(nav_items)

SIDEBAR = (
    '<button id="menu-toggle" aria-label="Toggle menu">&#9776;</button>\n'
    '<nav id="sidebar">\n'
    '  <div class="sidebar-top">\n'
    '    <a class="brand" href="index.html">HLD Handbook</a>\n'
    '    <button id="theme-toggle" aria-label="Toggle dark mode">&#127769;</button>\n'
    '  </div>\n'
    '  <div class="search-wrap">\n'
    '    <input id="search-box" type="text" placeholder="Search problems &amp; sections...">\n'
    '    <div id="search-results"></div>\n'
    '  </div>\n'
    '  <ul class="nav-list">\n'
    '    <li><a href="index.html" data-page="index.html">Home</a></li>\n'
    + nav_html + '\n'
    '    <li><a href="patterns.html" data-page="patterns.html">Patterns Playbook</a></li>\n'
    '  </ul>\n'
    '</nav>\n'
)

# ---------------------------------------------------------------------------
# 5. Page template (plain string concatenation only -- deliberately avoids
#    f-strings/.format for the big HTML/CSS/JS blocks so that literal "{" and
#    "}" characters inside extracted section HTML are never mistaken for
#    format placeholders).
# ---------------------------------------------------------------------------
HEAD_TOP = (
    "<!DOCTYPE html>\n"
    "<html lang=\"en\">\n"
    "<head>\n"
    "<meta charset=\"UTF-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "<script>document.documentElement.setAttribute('data-theme', localStorage.getItem('hld-theme') || 'light');</script>\n"
    "<title>"
)
HEAD_BOTTOM = (
    " \u2014 HLD Handbook</title>\n"
    "<link rel=\"stylesheet\" href=\"assets/style.css\">\n"
    "<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css\">\n"
    "</head>\n"
    "<body>\n"
)
SCRIPTS = (
    "\n<script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\"></script>\n"
    "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js\"></script>\n"
    "<script src=\"assets/app.js\"></script>\n"
    + MERMAID_SCRIPTS + "\n"
    "</body>\n"
    "</html>\n"
)


def render_page(title, main_html):
    return (HEAD_TOP + title + HEAD_BOTTOM + SIDEBAR
            + '<main id="content">\n<div class="content-inner">\n' + main_html
            + '\n</div>\n</main>\n' + SCRIPTS)


def prevnext(idx, seq):
    prev_html, next_html = "", ""
    if idx > 0:
        psid, plabel = seq[idx - 1]
        prev_html = f'<a class="prevnext-link prev" href="{psid}.html">&larr; {plabel}</a>'
    else:
        prev_html = '<span></span>'
    if idx < len(seq) - 1:
        nsid, nlabel = seq[idx + 1]
        next_html = f'<a class="prevnext-link next" href="{nsid}.html">{nlabel} &rarr;</a>'
    else:
        next_html = '<span></span>'
    return f'<div class="prevnext">{prev_html}{next_html}</div>'


seq = [(p["sid"], f'{p["num"]}. {p["name"]}') for p in problems if p["sid"] != "patterns"]
seq.append(("patterns", "Patterns Playbook"))

SECTOC_RE = re.compile(r'(<div class="section-toc">.*?</div>)', re.S)


def with_jumpbar(p):
    """Insert a slim sticky "jump to section" dropdown right after the
    (non-sticky) overview grid, so users always have a compact way to jump
    between lettered sections without a giant nav box staying pinned to the
    top of the page for its entire scroll range."""
    if not p["subs"]:
        return p["inner"]
    options = "".join(
        f'<option value="{aid}">{letter}. {title}</option>' for aid, letter, title in p["subs"])
    jumpbar = (
        f'<div class="jumpbar"><label for="jump-{p["sid"]}">Jump to section:</label>'
        f'<select id="jump-{p["sid"]}" class="jump-select" data-jump-select>{options}</select></div>')
    return SECTOC_RE.sub(lambda m: m.group(1) + jumpbar, p["inner"], count=1)


generated_files = set()

for idx, p in enumerate(problems):
    title = f'{p["num"]}. {p["name"]}' if p["num"] else p["name"]
    main_html = with_jumpbar(p) + prevnext(idx, seq)
    page = render_page(title, main_html)
    fname = f'{p["sid"]}.html'
    (HERE / fname).write_text(page, encoding="utf-8")
    generated_files.add(fname)

# ---------------------------------------------------------------------------
# 6. Home page (index.html) -- hero + difficulty filter + card grid, built
#    fresh (not extracted from source, source has no home page).
# ---------------------------------------------------------------------------
cards = []
for p in problems:
    if p["sid"] == "patterns":
        continue
    diff = buckets_for(p["sid"], p["badge"])
    cards.append(
        f'<a class="problem-card" href="{p["sid"]}.html" data-difficulty="{diff}">\n'
        f'  <span class="card-num">{p["num"]}</span>\n'
        f'  <span class="card-name">{p["name"]}</span>\n'
        f'  <span class="badge">{p["badge"]}</span>\n'
        f'</a>'
    )
cards_html = "\n".join(cards)

HOME_MAIN = (
    '<div class="cover">\n'
    '<h1>High-Level Design (HLD) / System Design<br>Interview Preparation Handbook</h1>\n'
    '<p><strong>20 Problems, Full Depth</strong> &middot; each covering requirements, capacity estimation, '
    'API design, data modeling, deep dives, scaling, trade-offs, and more.</p>\n'
    '<p><a href="patterns.html">View Patterns Playbook &rarr;</a></p>\n'
    '</div>\n'
    '<div class="filter-bar">\n'
    '  <button class="filter-btn active" data-filter="All">All</button>\n'
    '  <button class="filter-btn" data-filter="Beginner">Beginner</button>\n'
    '  <button class="filter-btn" data-filter="Intermediate">Intermediate</button>\n'
    '  <button class="filter-btn" data-filter="Advanced">Advanced</button>\n'
    '</div>\n'
    '<div class="card-grid">\n' + cards_html + '\n</div>\n'
)
(HERE / "index.html").write_text(render_page("Home", HOME_MAIN), encoding="utf-8")
generated_files.add("index.html")

# ---------------------------------------------------------------------------
# 7. search-index.json
# ---------------------------------------------------------------------------
index_entries = [{"title": "Home", "url": "index.html", "type": "page"}]
anchor_targets = set()
for p in problems:
    if p["sid"] == "patterns":
        index_entries.append({"title": f'{p["num"]}. {p["name"]}', "badge": p["badge"],
                               "url": "patterns.html", "type": "problem"})
    else:
        ptitle = f'{p["num"]}. {p["name"]}'
        index_entries.append({"title": ptitle, "badge": p["badge"], "url": f'{p["sid"]}.html', "type": "problem"})
    ptitle = f'{p["num"]}. {p["name"]}'
    for anchor_id, letter, subtitle in p["subs"]:
        url = f'{p["sid"]}.html#{anchor_id}'
        index_entries.append({"title": f'{letter}. {subtitle}', "parent": ptitle, "url": url, "type": "section"})
        anchor_targets.add(url)

(HERE / "search-index.json").write_text(
    json.dumps(index_entries, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------------------------------------------------------------------------
# 8. .nojekyll + README.md
# ---------------------------------------------------------------------------
(HERE / ".nojekyll").write_text("", encoding="utf-8")
(HERE / "README.md").write_text(
    "# HLD / System Design Interview Handbook\n\n"
    "A static, multi-page reference covering 20 high-level system design interview "
    "problems (URL Shortener, Rate Limiter, Twitter/News Feed, Chat System, Uber, "
    "Distributed Cache, Payment System, Dynamo-style Key-Value Store, build-your-own-Kafka, "
    "and more), each broken into requirements, capacity estimation, API design, data model, "
    "a naive design and why it breaks, seven deep dives, a full solution at scale, failure "
    "scenarios, trade-offs, and an interview simulation -- plus a Prerequisites primer on the "
    "recurring building blocks (Redis, Kafka, consistent hashing, CDNs, etc.) and a final "
    "Patterns Playbook synthesizing what recurs across all twenty problems.\n\n"
    "Includes sidebar navigation, client-side search, a difficulty filter, dark mode, "
    "copy-to-clipboard code blocks, live-rendered Mermaid diagrams, and a mobile-responsive layout.\n\n"
    "## Regenerating\n\n"
    "This site is generated from `../hld-handbook.html` (the single-page source document). "
    "To rebuild after editing that source:\n\n"
    "```bash\n"
    "python3 build.py\n"
    "```\n",
    encoding="utf-8",
)

# ---------------------------------------------------------------------------
# 9. assets/style.css = original CSS + new chrome/dark-mode/responsive rules
# ---------------------------------------------------------------------------
EXTRA_CSS = '''
/* ================= Multi-page site chrome (added by build.py) ================= */

html[data-theme="dark"]{
  --navy:#9ec5ff; --blue:#60a5fa; --gray-bg:#1e2530; --border:#334155; --accent:#a78bfa; --warn:#f59e0b;
}
html[data-theme="dark"] body{background:#0f172a; color:#e2e8f0;}
html[data-theme="dark"] tr:nth-child(even) td{background:#1a2332;}
html[data-theme="dark"] code{background:#1e2530; color:#e2e8f0;}
html[data-theme="dark"] pre code{background:none; color:inherit;}
html[data-theme="dark"] .toc-master{background:#132238;}
html[data-theme="dark"] .filter-btn{background:#1e293b; color:#e2e8f0;}
html[data-theme="dark"] .problem-card{background:#16202e;}
html[data-theme="dark"] #search-results{background:#16202e; color:#e2e8f0;}
html[data-theme="dark"] #search-results a{color:#e2e8f0; border-bottom-color:#243245;}
html[data-theme="dark"] #search-results a:hover{background:#1e293b;}

/* h3/h4 and table headers use hardcoded light-mode colors in the original
   single-page doc's own <style> block (it has no dark mode at all), and
   --navy flips to a *light* blue for dark mode everywhere else in this file
   -- so th's "white text on var(--navy) background" silently becomes
   washed-out white-on-light-blue, and h3/h4's hardcoded dark-navy/slate
   text becomes nearly invisible dark-on-dark. Override both explicitly. */
html[data-theme="dark"] h3{color:#9ec5ff;}
html[data-theme="dark"] h4{color:#94a3b8;}
html[data-theme="dark"] th{background:#132238; color:#e2e8f0;}

body{padding:0;}
#content{margin-left:250px;}
.content-inner{padding:0 36px 40px; max-width:1100px; margin:0 auto;}

#sidebar{
  position:fixed; top:0; left:0; width:250px; height:100vh; overflow-y:auto;
  background:#0f2540; color:#fff; padding:16px 14px; box-sizing:border-box; z-index:10;
}
#sidebar .sidebar-top{display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;}
#sidebar .brand{color:#fff; font-weight:700; font-size:14.5px;}
#theme-toggle{background:none; border:1px solid #4a6a91; color:#fff; border-radius:6px; padding:3px 8px; cursor:pointer; font-size:13px;}
.search-wrap{position:relative; margin-bottom:14px;}
#search-box{width:100%; padding:6px 8px; border-radius:5px; border:1px solid #4a6a91; font-size:12.5px; background:#0f2540; color:#fff;}
#search-box::placeholder{color:#9db8d8;}
#search-results{position:absolute; top:100%; left:0; right:0; background:#fff; color:#1a1f26; border-radius:6px; margin-top:4px; max-height:320px; overflow-y:auto; box-shadow:0 4px 14px rgba(0,0,0,.25); z-index:30; display:none;}
#search-results.open{display:block;}
#search-results a{display:block; padding:6px 10px; font-size:12px; border-bottom:1px solid #eee;}
#search-results a:hover{background:#eef6ff;}
#search-results .result-parent{display:block; font-size:10px; color:#888;}
.nav-list{list-style:none; margin:0; padding:0; font-size:12.5px;}
.nav-list li a{display:block; color:#cfe4ff; padding:5px 8px; border-radius:5px; margin-bottom:1px;}
.nav-list li a:hover{background:rgba(255,255,255,.08);}
.nav-list li a.active{background:var(--accent); color:#fff; font-weight:600;}

#menu-toggle{display:none; position:fixed; top:10px; left:10px; z-index:40; background:#0f2540; color:#fff; border:none; border-radius:6px; width:34px; height:34px; font-size:17px; cursor:pointer;}

h3[id]{scroll-margin-top:64px;}

.jumpbar{position:sticky; top:0; z-index:6; background:var(--gray-bg); border:1px solid var(--border); border-radius:6px; padding:8px 14px; margin:0 0 16px; display:flex; align-items:center; gap:10px; font-size:12.5px;}
.jumpbar label{font-weight:600; color:var(--navy); white-space:nowrap;}
.jump-select{flex:1; max-width:340px; padding:4px 8px; border-radius:5px; border:1px solid var(--border); font-size:12.5px; background:#fff; color:#1a1f26;}
html[data-theme="dark"] .jump-select{background:#0f172a; color:#e2e8f0;}

.prevnext{display:flex; justify-content:space-between; align-items:center; margin:36px 0 24px; padding-top:14px; border-top:1px solid var(--border);}
.prevnext-link{font-size:13px; font-weight:600;}

.filter-bar{text-align:center; margin:10px 0 22px;}
.filter-btn{background:#fff; border:1px solid var(--border); border-radius:16px; padding:5px 16px; margin:0 4px; font-size:12.5px; cursor:pointer; color:#334155;}
.filter-btn.active{background:var(--blue); color:#fff; border-color:var(--blue);}
.card-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:14px; margin:0 0 40px;}
.problem-card{display:flex; flex-direction:column; gap:6px; border:1px solid var(--border); border-radius:8px; padding:14px 16px; background:#fff; transition:box-shadow .15s, transform .15s;}
.problem-card:hover{box-shadow:0 4px 14px rgba(0,0,0,.1); transform:translateY(-2px);}
.problem-card .card-num{color:var(--accent); font-weight:700; font-size:12px;}
.problem-card .card-name{color:var(--navy); font-weight:600; font-size:14.5px;}
.problem-card.hidden{display:none;}

/* ---- read-only "editor" chrome for all <pre> code blocks ---- */
.code-window{border-radius:8px; overflow:hidden; margin:10px 0 18px; border:1px solid #1e293b; box-shadow:0 1px 3px rgba(0,0,0,.08);}
.code-window-bar{background:#1e293b; padding:7px 10px; display:flex; align-items:center; gap:6px;}
.code-window-bar .dot{width:9px; height:9px; border-radius:50%; display:inline-block;}
.code-window-bar .dot-red{background:#ef4444;}
.code-window-bar .dot-yellow{background:#f59e0b;}
.code-window-bar .dot-green{background:#22c55e;}
.code-window-bar .cw-label{color:#94a3b8; font-size:10.5px; margin-left:6px; text-transform:uppercase; letter-spacing:.04em;}
.code-window pre{margin:0; border-radius:0;}
.code-window .copy-btn{margin-left:auto; position:static; font-size:10.5px; padding:2px 9px; border-radius:4px; border:1px solid #334155; background:#0f172a; color:#e2e8f0; cursor:pointer; opacity:.85;}
.code-window .copy-btn:hover{opacity:1;}

/* highlightjs-line-numbers.js gutter */
.hljs-ln{border-collapse:collapse; width:100%;}
.hljs-ln td{padding:0; border:none;}
.hljs-ln-numbers{text-align:right; color:#516074; padding:0 10px 0 6px !important; border-right:1px solid #334155; user-select:none; white-space:nowrap; vertical-align:top; width:1%;}
.hljs-ln-code{padding:0 0 0 14px !important; vertical-align:top;}
/* the generic table zebra-striping rule (tr:nth-child(even) td) also matches the
   line-number table injected into code blocks -- kill it there so code stays on
   one consistent dark background instead of alternating with light rows */
.hljs-ln tr:nth-child(even) td, .hljs-ln tr td{background:none !important;}

/* callout/prompt boxes keep their light, colorful backgrounds even in dark mode
   (by design from the original single-page doc) -- give them dark-mode-safe
   backgrounds + text color so they stay readable instead of light-gray-on-pale-yellow */
html[data-theme="dark"] .callout{background:#132238; color:#dbeafe; border-left-color:#a78bfa;}
html[data-theme="dark"] .prompt{background:#3a2f14; color:#f5e6c8; border-left-color:#f59e0b;}

/* mermaid diagrams render their own light-theme SVG background regardless of
   page theme (mermaid.initialize uses a fixed 'base' theme) -- keep the
   surrounding card legible in dark mode without fighting the SVG itself */
html[data-theme="dark"] .diagram-caption{color:#8a93a3;}

@media (max-width: 880px){
  #sidebar{left:-260px; transition:left .22s; box-shadow:2px 0 10px rgba(0,0,0,.2);}
  #sidebar.open{left:0;}
  #content{margin-left:0;}
  .content-inner{padding:0 18px 40px;}
  #menu-toggle{display:block;}
  .section-toc{column-count:2 !important;}
}
@media (max-width: 600px){
  .section-toc{column-count:1 !important;}
  table{display:block; overflow-x:auto; white-space:nowrap;}
  .diagram{margin:14px -18px 16px;}
  h1.problem-title{display:flex; flex-direction:column; align-items:flex-start; gap:6px;}
  h1.problem-title .badge{margin-left:0;}
}
'''

(HERE / "assets" / "style.css").write_text(orig_css + "\n\n" + EXTRA_CSS, encoding="utf-8")

# ---------------------------------------------------------------------------
# 10. assets/app.js
# ---------------------------------------------------------------------------
APP_JS = '''document.addEventListener("DOMContentLoaded", function () {
  initActiveNav();
  initThemeToggle();
  initMobileMenu();
  initJumpSelect();
  initCodeChrome();
  initHighlighting();
  initSearch();
  initDifficultyFilter();
});

function initActiveNav() {
  var page = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-list a[data-page]").forEach(function (a) {
    if (a.getAttribute("data-page") === page) a.classList.add("active");
  });
}

function initThemeToggle() {
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;
  btn.addEventListener("click", function () {
    var cur = document.documentElement.getAttribute("data-theme") || "light";
    var next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("hld-theme", next);
  });
}

function initMobileMenu() {
  var toggle = document.getElementById("menu-toggle");
  var sidebar = document.getElementById("sidebar");
  if (!toggle || !sidebar) return;
  toggle.addEventListener("click", function () {
    sidebar.classList.toggle("open");
  });
  document.addEventListener("click", function (e) {
    if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove("open");
    }
  });
}

function initJumpSelect() {
  document.querySelectorAll("[data-jump-select]").forEach(function (sel) {
    sel.addEventListener("change", function () {
      if (sel.value) location.hash = sel.value;
    });
  });
}

function initCodeChrome() {
  // Wrap every <pre> in a small read-only "editor window": a title bar
  // (traffic-light dots + Copy button) on top of the existing dark <pre>.
  // No execution affordance -- this is display-only chrome. Mermaid source
  // divs are not <pre> blocks, so they're untouched here.
  document.querySelectorAll("pre").forEach(function (pre) {
    if (pre.parentElement.classList.contains("code-window")) return;
    var wrapper = document.createElement("div");
    wrapper.className = "code-window";

    var bar = document.createElement("div");
    bar.className = "code-window-bar";
    bar.innerHTML =
      '<span class="dot dot-red"></span><span class="dot dot-yellow"></span><span class="dot dot-green"></span>';

    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      var codeEl = pre.querySelector("code");
      var text = (codeEl || pre).innerText;
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = "Copied!";
        setTimeout(function () { btn.textContent = "Copy"; }, 1500);
      });
    });
    bar.appendChild(btn);

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(bar);
    wrapper.appendChild(pre);
  });
}

function initHighlighting() {
  if (typeof hljs === "undefined") return;
  document.querySelectorAll("pre code").forEach(function (block) {
    hljs.highlightElement(block);
    if (typeof hljs.lineNumbersBlock === "function") {
      hljs.lineNumbersBlock(block);
    }
  });
}

var searchIndexPromise = null;
function loadSearchIndex() {
  if (!searchIndexPromise) {
    searchIndexPromise = fetch("search-index.json").then(function (r) { return r.json(); });
  }
  return searchIndexPromise;
}

function rank(entry, q) {
  var t = entry.title.toLowerCase();
  if (t === q) return 0;
  if (t.indexOf(q) === 0) return 1;
  return 2;
}

function initSearch() {
  var box = document.getElementById("search-box");
  var results = document.getElementById("search-results");
  if (!box || !results) return;
  box.addEventListener("focus", loadSearchIndex);
  box.addEventListener("input", function () {
    var q = box.value.trim().toLowerCase();
    if (!q) { results.classList.remove("open"); results.innerHTML = ""; return; }
    loadSearchIndex().then(function (index) {
      var matches = index.filter(function (e) {
        return e.title.toLowerCase().indexOf(q) !== -1 ||
          (e.parent && e.parent.toLowerCase().indexOf(q) !== -1);
      });
      matches.sort(function (a, b) { return rank(a, q) - rank(b, q); });
      matches = matches.slice(0, 20);
      results.innerHTML = matches.map(function (e) {
        var parentLine = e.parent ? ("<span class=\\"result-parent\\">" + e.parent + "</span>") : "";
        return "<a href=\\"" + e.url + "\\">" + e.title + parentLine + "</a>";
      }).join("");
      results.classList.toggle("open", matches.length > 0);
    });
  });
  document.addEventListener("click", function (e) {
    if (!results.contains(e.target) && e.target !== box) results.classList.remove("open");
  });
}

function initDifficultyFilter() {
  var buttons = document.querySelectorAll(".filter-btn");
  if (!buttons.length) return;
  buttons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      buttons.forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      var filter = btn.getAttribute("data-filter");
      document.querySelectorAll(".problem-card").forEach(function (card) {
        var diff = card.getAttribute("data-difficulty") || "";
        var show = filter === "All" || diff.indexOf(filter) !== -1;
        card.classList.toggle("hidden", !show);
      });
    });
  });
}
'''

(HERE / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")

# ---------------------------------------------------------------------------
# 11. Verify every generated URL/anchor actually resolves
# ---------------------------------------------------------------------------
ok = True
for e in index_entries:
    url = e["url"]
    fname = url.split("#")[0]
    if fname not in generated_files:
        print("MISSING FILE:", url)
        ok = False
    if "#" in url and url not in anchor_targets:
        print("MISSING ANCHOR:", url)
        ok = False

print(f"Generated {len(generated_files)} pages, {len(index_entries)} search-index entries.")
print("Anchor/link verification:", "OK" if ok else "FAILED")
