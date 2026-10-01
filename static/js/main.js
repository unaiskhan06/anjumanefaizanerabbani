/* Site-wide behaviour: mobile menu, "More" dropdown, dark mode, row scrolling, share/copy. */
(function () {
  "use strict";

  var root = document.documentElement;
  var body = document.body;

  /* ---------- Dark mode (saved in localStorage) ---------- */
  document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
    var sync = function () {
      var dark = root.getAttribute("data-theme") === "dark";
      btn.setAttribute("aria-pressed", dark ? "true" : "false");
    };
    sync();
    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* private mode */ }
      sync();
    });
  });

  /* ---------- Mobile navigation ---------- */
  var navToggle = document.querySelector("[data-nav-toggle]");
  var nav = document.getElementById("site-nav");
  function setNav(open) {
    body.classList.toggle("nav-open", open);
    if (navToggle) {
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    }
  }
  if (navToggle && nav) {
    navToggle.addEventListener("click", function () {
      setNav(!body.classList.contains("nav-open"));
    });
    window.matchMedia("(min-width: 1280px)").addEventListener("change", function (e) {
      if (e.matches) setNav(false);
    });
  }

  /* ---------- "More" dropdown ---------- */
  var dropdownButtons = document.querySelectorAll("[data-dropdown]");
  function closeDropdowns(except) {
    dropdownButtons.forEach(function (btn) {
      if (btn === except) return;
      btn.setAttribute("aria-expanded", "false");
      btn.parentElement.classList.remove("is-open");
    });
  }
  dropdownButtons.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = btn.getAttribute("aria-expanded") !== "true";
      closeDropdowns(btn);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.parentElement.classList.toggle("is-open", open);
      if (open) {
        var first = btn.parentElement.querySelector(".dropdown a");
        if (first && e.detail === 0) first.focus(); // keyboard activation
      }
    });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".has-dropdown")) closeDropdowns();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var openBtn = document.querySelector("[data-dropdown][aria-expanded='true']");
    if (openBtn) { closeDropdowns(); openBtn.focus(); return; }
    if (body.classList.contains("nav-open")) { setNav(false); navToggle.focus(); }
  });

  /* ---------- Horizontal video rows: arrow buttons ---------- */
  document.querySelectorAll("[data-row-scroll]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var track = document.getElementById(btn.getAttribute("aria-controls"));
      if (!track) return;
      var dir = parseInt(btn.getAttribute("data-row-scroll"), 10);
      if (getComputedStyle(track).direction === "rtl") dir = -dir;
      track.scrollBy({ left: dir * track.clientWidth * 0.9, behavior: "smooth" });
    });
  });

  /* ---------- Copy link & native share ---------- */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (err) { reject(err); }
      document.body.removeChild(ta);
    });
  }
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    var label = btn.querySelector("[data-copy-label]") || btn;
    var original = label.textContent;
    btn.addEventListener("click", function () {
      copyText(btn.getAttribute("data-copy")).then(function () {
        label.textContent = "Link copied!";
      }, function () {
        label.textContent = "Press Ctrl+C to copy";
      });
      setTimeout(function () { label.textContent = original; }, 2200);
    });
  });
  if (navigator.share) {
    document.querySelectorAll("[data-native-share]").forEach(function (btn) {
      btn.hidden = false;
      btn.addEventListener("click", function () {
        navigator.share({ title: btn.getAttribute("data-share-title"), url: btn.getAttribute("data-share-url") })
          .catch(function () { /* user cancelled */ });
      });
    });
  }
})();
