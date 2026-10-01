/* Live search suggestions (accessible combobox) for every input with [data-suggest]. */
(function () {
  "use strict";

  var ENDPOINT = "/search/suggest/";
  var uid = 0;

  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  document.querySelectorAll("input[data-suggest]").forEach(function (input) {
    var form = input.closest("form");
    var listId = "suggest-" + (++uid);
    var list = document.createElement("ul");
    list.className = "suggest-list";
    list.id = listId;
    list.setAttribute("role", "listbox");
    list.hidden = true;
    form.appendChild(list);

    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-controls", listId);

    var active = -1;
    var controller = null;
    var lastQuery = "";

    function options() { return list.querySelectorAll("[role='option']"); }

    function close() {
      list.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      active = -1;
    }

    function highlight(i) {
      var opts = options();
      if (!opts.length) return;
      active = (i + opts.length) % opts.length;
      opts.forEach(function (o, n) { o.setAttribute("aria-selected", n === active ? "true" : "false"); });
      input.setAttribute("aria-activedescendant", opts[active].id);
      opts[active].scrollIntoView({ block: "nearest" });
    }

    function render(results, q) {
      if (!results.length) {
        list.innerHTML = '<li class="suggest-empty" role="presentation">No matches for “' + escapeHtml(q) + '”</li>';
      } else {
        list.innerHTML = results.map(function (r, i) {
          return '<li class="suggest-item" role="option" id="' + listId + '-' + i + '" aria-selected="false">' +
            '<a href="' + escapeHtml(r.url) + '" tabindex="-1">' +
            '<img src="' + escapeHtml(r.thumbnail) + '" alt="" loading="lazy" width="64" height="36">' +
            '<span><span class="suggest-title">' + escapeHtml(r.title) + '</span>' +
            '<span class="suggest-cat">' + escapeHtml(r.category) + '</span></span></a></li>';
        }).join("") +
          '<li role="presentation"><a class="suggest-all" href="/search/?q=' + encodeURIComponent(q) + '">See all results</a></li>';
      }
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
      active = -1;
    }

    var fetchSuggestions = debounce(function () {
      var q = input.value.trim();
      if (q === lastQuery) return;
      lastQuery = q;
      if (q.length < 2) { close(); return; }
      if (controller) controller.abort();
      controller = "AbortController" in window ? new AbortController() : null;
      fetch(ENDPOINT + "?q=" + encodeURIComponent(q), {
        headers: { "Accept": "application/json" },
        signal: controller ? controller.signal : undefined
      })
        .then(function (r) { return r.ok ? r.json() : { results: [] }; })
        .then(function (data) { if (input.value.trim() === q) render(data.results || [], q); })
        .catch(function () { /* network error or aborted: ignore */ });
    }, 220);

    input.addEventListener("input", fetchSuggestions);
    input.addEventListener("focus", function () { if (list.children.length && input.value.trim().length >= 2) { list.hidden = false; input.setAttribute("aria-expanded", "true"); } });
    input.addEventListener("keydown", function (e) {
      if (list.hidden) return;
      if (e.key === "ArrowDown") { e.preventDefault(); highlight(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); highlight(active - 1); }
      else if (e.key === "Escape") { e.stopPropagation(); close(); }
      else if (e.key === "Enter" && active >= 0) {
        e.preventDefault();
        window.location.href = options()[active].querySelector("a").href;
      }
    });
    document.addEventListener("click", function (e) { if (!form.contains(e.target)) close(); });
  });
})();
