document.addEventListener("DOMContentLoaded", function () {
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
        var parentLine = e.parent ? ("<span class=\"result-parent\">" + e.parent + "</span>") : "";
        return "<a href=\"" + e.url + "\">" + e.title + parentLine + "</a>";
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
