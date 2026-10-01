/* Admin helper: live thumbnail + player preview while pasting a YouTube link. */
(function () {
  "use strict";

  function extractId(value) {
    value = (value || "").trim();
    if (/^[A-Za-z0-9_-]{11}$/.test(value)) return value;
    var m = value.match(/(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|live\/|v\/))([A-Za-z0-9_-]{11})/);
    return m ? m[1] : null;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var input = document.getElementById("id_youtube_url");
    if (!input) return;
    var hint = document.createElement("div");
    hint.className = "help";
    hint.style.marginTop = "6px";
    input.insertAdjacentElement("afterend", hint);

    function update() {
      var id = extractId(input.value);
      var thumbBox = document.getElementById("yt-thumb-preview");
      var playerBox = document.getElementById("yt-player-preview");
      if (!input.value.trim()) { hint.textContent = ""; return; }
      if (!id) {
        hint.textContent = "⚠ This does not look like a YouTube link yet.";
        hint.style.color = "#ba2121";
        return;
      }
      hint.textContent = "✓ Video ID detected: " + id + (input.value.indexOf("/shorts/") > -1 ? " (Short)" : "");
      hint.style.color = "#16794c";
      if (thumbBox) {
        thumbBox.innerHTML = '<img src="https://img.youtube.com/vi/' + id + '/hqdefault.jpg" width="320" style="border-radius:6px;aspect-ratio:16/9;object-fit:cover" alt="">';
      }
      if (playerBox) {
        var iframe = playerBox.querySelector("iframe");
        var src = "https://www.youtube-nocookie.com/embed/" + id + "?rel=0";
        if (iframe && iframe.src !== src) iframe.src = src;
      }
    }
    input.addEventListener("input", update);
    input.addEventListener("change", update);
    if (!input.readOnly) update();
  });
})();
