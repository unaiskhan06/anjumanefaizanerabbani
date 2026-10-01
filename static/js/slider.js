/* Hero slider: autoplay, arrows, dots, swipe, pause on hover/focus, respects reduced motion. */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-slider]").forEach(function (slider) {
    var slides = Array.prototype.slice.call(slider.querySelectorAll(".slide"));
    var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-slider-dot]"));
    if (slides.length < 2) return;

    var interval = parseInt(slider.getAttribute("data-interval"), 10) || 6000;
    var index = 0;
    var timer = null;
    var paused = false;

    function go(n) {
      index = (n + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        var active = i === index;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", active ? "false" : "true");
        slide.querySelectorAll("a, button").forEach(function (el) {
          if (active) el.removeAttribute("tabindex"); else el.setAttribute("tabindex", "-1");
        });
        var img = slide.querySelector("img[loading='lazy']");
        if (active && img) img.loading = "eager";
      });
      dots.forEach(function (dot, i) {
        dot.classList.toggle("is-active", i === index);
        if (i === index) dot.setAttribute("aria-current", "true"); else dot.removeAttribute("aria-current");
      });
      // Pre-load the next slide's image.
      var nextImg = slides[(index + 1) % slides.length].querySelector("img");
      if (nextImg) nextImg.loading = "eager";
    }

    function stop() { clearInterval(timer); timer = null; }
    function start() {
      stop();
      if (reduceMotion || paused || document.hidden) return;
      timer = setInterval(function () { go(index + 1); }, interval);
    }
    function restart() { start(); }

    var prev = slider.querySelector("[data-slider-prev]");
    var next = slider.querySelector("[data-slider-next]");
    if (prev) prev.addEventListener("click", function () { go(index - 1); restart(); });
    if (next) next.addEventListener("click", function () { go(index + 1); restart(); });
    dots.forEach(function (dot) {
      dot.addEventListener("click", function () { go(parseInt(dot.getAttribute("data-slider-dot"), 10)); restart(); });
    });

    // Pause on hover and while keyboard focus is inside.
    slider.addEventListener("mouseenter", function () { paused = true; stop(); });
    slider.addEventListener("mouseleave", function () { paused = false; start(); });
    slider.addEventListener("focusin", function () { paused = true; stop(); });
    slider.addEventListener("focusout", function (e) {
      if (!slider.contains(e.relatedTarget)) { paused = false; start(); }
    });
    document.addEventListener("visibilitychange", start);

    slider.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { go(index - 1); }
      if (e.key === "ArrowRight") { go(index + 1); }
    });

    // Touch swipe.
    var startX = null, startY = null;
    slider.addEventListener("touchstart", function (e) {
      startX = e.touches[0].clientX; startY = e.touches[0].clientY; stop();
    }, { passive: true });
    slider.addEventListener("touchend", function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      var dy = e.changedTouches[0].clientY - startY;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) go(index + (dx < 0 ? 1 : -1));
      startX = null;
      start();
    }, { passive: true });

    go(0);
    start();
  });
})();
