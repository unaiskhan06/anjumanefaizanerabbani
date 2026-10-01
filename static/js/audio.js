/* Custom HTML5 audio player: play/pause, seek, volume, playlist and auto-next. */
(function () {
  "use strict";

  var player = document.querySelector("[data-audio-player]");
  if (!player) return;

  var audio = player.querySelector("[data-audio]");
  var btnPlay = player.querySelector("[data-ap-play]");
  var btnPrev = player.querySelector("[data-ap-prev]");
  var btnNext = player.querySelector("[data-ap-next]");
  var btnMute = player.querySelector("[data-ap-mute]");
  var seek = player.querySelector("[data-ap-seek]");
  var volume = player.querySelector("[data-ap-volume]");
  var elTitle = player.querySelector("[data-ap-title]");
  var elArtist = player.querySelector("[data-ap-artist]");
  var elCurrent = player.querySelector("[data-ap-current]");
  var elDuration = player.querySelector("[data-ap-duration]");
  var list = document.querySelector("[data-ap-list]");
  var items = Array.prototype.slice.call(list.querySelectorAll(".playlist-item"));
  var current = -1;
  var seeking = false;

  function fmt(sec) {
    if (!isFinite(sec) || sec < 0) return "0:00";
    var m = Math.floor(sec / 60), s = Math.floor(sec % 60);
    var h = Math.floor(m / 60);
    if (h) { m = m % 60; return h + ":" + String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0"); }
    return m + ":" + String(s).padStart(2, "0");
  }

  function load(i, autoplay) {
    if (!items.length) return;
    current = (i + items.length) % items.length;
    var item = items[current];
    items.forEach(function (el, n) {
      el.classList.toggle("is-current", n === current);
      if (n === current) el.setAttribute("aria-current", "true"); else el.removeAttribute("aria-current");
    });
    audio.src = item.getAttribute("data-src");
    elTitle.textContent = item.getAttribute("data-title");
    elArtist.textContent = item.getAttribute("data-artist") || "";
    seek.value = 0;
    elCurrent.textContent = "0:00";
    if (autoplay) play();
    if ("mediaSession" in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: item.getAttribute("data-title"),
        artist: item.getAttribute("data-artist") || "Anjuman-e-Faizan-e-Rabbani"
      });
    }
  }

  function play() {
    if (current < 0) load(0, false);
    var p = audio.play();
    if (p && p.catch) p.catch(function () { /* autoplay blocked until user interacts */ });
  }

  function toggle() { audio.paused ? play() : audio.pause(); }

  btnPlay.addEventListener("click", toggle);
  btnPrev.addEventListener("click", function () {
    if (audio.currentTime > 3) { audio.currentTime = 0; return; }
    load(current - 1, true);
  });
  btnNext.addEventListener("click", function () { load(current + 1, true); });

  items.forEach(function (item, i) {
    item.addEventListener("click", function () {
      if (i === current) toggle(); else load(i, true);
    });
  });

  audio.addEventListener("play", function () {
    player.classList.add("is-playing"); list.classList.add("is-playing");
    btnPlay.setAttribute("aria-label", "Pause");
  });
  audio.addEventListener("pause", function () {
    player.classList.remove("is-playing"); list.classList.remove("is-playing");
    btnPlay.setAttribute("aria-label", "Play");
  });
  audio.addEventListener("loadedmetadata", function () { elDuration.textContent = fmt(audio.duration); });
  audio.addEventListener("timeupdate", function () {
    if (seeking || !audio.duration) return;
    seek.value = (audio.currentTime / audio.duration) * 100;
    elCurrent.textContent = fmt(audio.currentTime);
  });
  audio.addEventListener("ended", function () {
    if (current < items.length - 1) load(current + 1, true);
  });
  audio.addEventListener("error", function () {
    elArtist.textContent = "This track could not be loaded.";
  });

  seek.addEventListener("input", function () {
    seeking = true;
    if (audio.duration) elCurrent.textContent = fmt((seek.value / 100) * audio.duration);
  });
  seek.addEventListener("change", function () {
    if (audio.duration) audio.currentTime = (seek.value / 100) * audio.duration;
    seeking = false;
  });

  function syncMute() {
    var muted = audio.muted || audio.volume === 0;
    player.classList.toggle("is-muted", muted);
    btnMute.setAttribute("aria-label", muted ? "Unmute" : "Mute");
  }
  volume.addEventListener("input", function () {
    audio.volume = parseFloat(volume.value);
    audio.muted = audio.volume === 0;
    try { localStorage.setItem("audioVolume", volume.value); } catch (e) {}
    syncMute();
  });
  btnMute.addEventListener("click", function () { audio.muted = !audio.muted; syncMute(); });
  try {
    var saved = localStorage.getItem("audioVolume");
    if (saved !== null) { volume.value = saved; audio.volume = parseFloat(saved); }
  } catch (e) {}
  syncMute();

  // Keyboard: space toggles when focus isn't on a form control.
  document.addEventListener("keydown", function (e) {
    if (e.code === "Space" && !e.target.closest("input, textarea, button, a, select")) {
      e.preventDefault(); toggle();
    }
  });

  if ("mediaSession" in navigator) {
    navigator.mediaSession.setActionHandler("previoustrack", function () { load(current - 1, true); });
    navigator.mediaSession.setActionHandler("nexttrack", function () { load(current + 1, true); });
  }

  load(0, false);
})();
