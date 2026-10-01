/* Gallery lightbox: click to open, arrows / keyboard / swipe to navigate, Esc to close, focus is trapped. */
(function () {
  "use strict";

  var dialog = document.querySelector("[data-lightbox-dialog]");
  var links = Array.prototype.slice.call(document.querySelectorAll("[data-lightbox]"));
  if (!dialog || !links.length) return;

  var img = dialog.querySelector("[data-lb-img]");
  var caption = dialog.querySelector("[data-lb-caption]");
  var count = dialog.querySelector("[data-lb-count]");
  var btnClose = dialog.querySelector("[data-lb-close]");
  var btnPrev = dialog.querySelector("[data-lb-prev]");
  var btnNext = dialog.querySelector("[data-lb-next]");
  var index = 0;
  var opener = null;

  function show(i) {
    index = (i + links.length) % links.length;
    var link = links[index];
    var text = link.getAttribute("data-caption") || "";
    img.src = link.getAttribute("href");
    img.alt = text || "Gallery photo " + (index + 1);
    caption.textContent = text;
    count.textContent = (index + 1) + " / " + links.length;
    // Preload neighbours for smooth navigation.
    [index + 1, index - 1].forEach(function (n) {
      var pre = new Image();
      pre.src = links[(n + links.length) % links.length].getAttribute("href");
    });
  }

  function open(i) {
    opener = document.activeElement;
    show(i);
    dialog.hidden = false;
    document.body.classList.add("no-scroll");
    btnClose.focus();
  }

  function close() {
    dialog.hidden = true;
    document.body.classList.remove("no-scroll");
    img.src = "";
    if (opener) opener.focus();
  }

  links.forEach(function (link, i) {
    link.addEventListener("click", function (e) { e.preventDefault(); open(i); });
  });
  btnClose.addEventListener("click", close);
  btnPrev.addEventListener("click", function () { show(index - 1); });
  btnNext.addEventListener("click", function () { show(index + 1); });
  dialog.addEventListener("click", function (e) {
    if (e.target === dialog || e.target.classList.contains("lightbox-figure")) close();
  });

  document.addEventListener("keydown", function (e) {
    if (dialog.hidden) return;
    var rtl = document.documentElement.dir === "rtl";
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(index + (rtl ? -1 : 1));
    else if (e.key === "ArrowLeft") show(index + (rtl ? 1 : -1));
    else if (e.key === "Tab") {
      var focusables = [btnClose, btnPrev, btnNext];
      var pos = focusables.indexOf(document.activeElement);
      e.preventDefault();
      focusables[(pos + (e.shiftKey ? -1 : 1) + focusables.length) % focusables.length].focus();
    }
  });

  var startX = null, startY = null;
  dialog.addEventListener("touchstart", function (e) {
    startX = e.touches[0].clientX; startY = e.touches[0].clientY;
  }, { passive: true });
  dialog.addEventListener("touchend", function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    var dy = e.changedTouches[0].clientY - startY;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) show(index + (dx < 0 ? 1 : -1));
    else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close(); // swipe down to close
    startX = null;
  }, { passive: true });
})();
