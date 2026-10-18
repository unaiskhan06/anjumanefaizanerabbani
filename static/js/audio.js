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

  /* Show a brief "no audio" toast on the player bar. */
  function showNoAudioToast() {
    var old = player.querySelector(".ap-toast");
    if (old) old.remove();
    var toast = document.createElement("div");
    toast.className = "ap-toast";
    toast.textContent = "No audio available";
    player.appendChild(toast);
    setTimeout(function () { toast.classList.add("ap-toast--visible"); }, 10);
    setTimeout(function () { toast.classList.remove("ap-toast--visible"); }, 2200);
    setTimeout(function () { toast.remove(); }, 2600);
  }

  /* Find the next playable (has audio) item index in a given direction. */
  function nextPlayable(from, dir) {
    for (var n = 1; n <= items.length; n++) {
      var idx = (from + n * dir + items.length) % items.length;
      if (!items[idx].hasAttribute("data-no-audio")) return idx;
    }
    return -1; /* every item is image-only */
  }

  /* Zoom controls state */
  var zoomScale = 1.0;
  var MIN_ZOOM = 0.5;
  var MAX_ZOOM = 3.5;
  var ZOOM_STEP = 0.25;

  var viewer = player.querySelector("[data-ap-viewer]");
  var viewerImg = player.querySelector("[data-ap-viewer-img]");
  var viewerHeading = player.querySelector("[data-ap-viewer-heading]");
  var btnZoomIn = player.querySelector("[data-ap-zoom-in]");
  var btnZoomOut = player.querySelector("[data-ap-zoom-out]");
  var btnZoomReset = player.querySelector("[data-ap-zoom-reset]");
  var elZoomLevel = player.querySelector("[data-ap-zoom-level]");

  function updateZoom(newScale) {
    zoomScale = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(newScale * 100) / 100));
    if (viewerImg) {
      if (zoomScale > 1) {
        viewerImg.style.maxWidth = "none";
        viewerImg.style.width = (zoomScale * 100) + "%";
      } else if (zoomScale < 1) {
        viewerImg.style.maxWidth = "100%";
        viewerImg.style.width = (zoomScale * 100) + "%";
      } else {
        viewerImg.style.maxWidth = "100%";
        viewerImg.style.width = "auto";
      }
    }
    if (elZoomLevel) {
      elZoomLevel.textContent = Math.round(zoomScale * 100) + "%";
    }
  }

  if (btnZoomIn) {
    btnZoomIn.addEventListener("click", function () { updateZoom(zoomScale + ZOOM_STEP); });
  }
  if (btnZoomOut) {
    btnZoomOut.addEventListener("click", function () { updateZoom(zoomScale - ZOOM_STEP); });
  }
  if (btnZoomReset) {
    btnZoomReset.addEventListener("click", function () { updateZoom(1.0); });
  }

  function load(i, autoplay) {
    if (!items.length) return;
    current = (i + items.length) % items.length;
    var item = items[current];
    items.forEach(function (el, n) {
      el.classList.toggle("is-current", n === current);
      if (n === current) el.setAttribute("aria-current", "true"); else el.removeAttribute("aria-current");
    });

    var title = item.getAttribute("data-title") || "";
    var artist = item.getAttribute("data-artist") || "";
    elTitle.textContent = title;
    elArtist.textContent = artist;

    var lyricsUrl = item.getAttribute("data-lyrics");
    var coverUrl = item.getAttribute("data-image");
    var displayImg = lyricsUrl || coverUrl;

    /* Avatar thumbnail */
    var apImg = player.querySelector("[data-ap-image]");
    var apIcon = player.querySelector(".ap-icon");
    if (apImg) {
      if (displayImg) { apImg.src = displayImg; apImg.style.display = "block"; }
      else { apImg.style.display = "none"; }
    }
    if (apIcon) apIcon.style.display = displayImg ? "none" : "block";

    /* Embedded Zoomable Image Viewer */
    if (viewer && viewerImg) {
      if (displayImg) {
        viewer.style.display = "block";
        viewerImg.src = displayImg;
        viewerImg.alt = title + " (Lyrics / Image)";
        if (viewerHeading) {
          viewerHeading.textContent = lyricsUrl ? "Lyrics Sheet" : "Image View";
        }
        updateZoom(1.0);
      } else {
        viewer.style.display = "none";
        viewerImg.src = "";
      }
    }

    var hasAudio = !item.hasAttribute("data-no-audio") && Boolean(item.getAttribute("data-src"));

    if (!hasAudio) {
      /* ONLY IMAGE: hide play buttons, seekbar, and sound */
      player.classList.add("is-image-only");
      audio.pause();
      player.classList.remove("is-playing");
      list.classList.remove("is-playing");
      btnPlay.setAttribute("aria-label", "Play");
      audio.removeAttribute("src");
      seek.value = 0; elCurrent.textContent = "0:00"; elDuration.textContent = "0:00";
      return;
    }

    /* HAS BOTH IMAGE AND AUDIO: show play buttons and sound */
    player.classList.remove("is-image-only");
    audio.src = item.getAttribute("data-src");
    seek.value = 0;
    elCurrent.textContent = "0:00";
    if (autoplay) play();
    if ("mediaSession" in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: title,
        artist: artist || "Anjuman-e-Faizan-e-Rabbani"
      });
    }
  }

  function play() {
    if (current < 0 || items[current].hasAttribute("data-no-audio")) {
      var nxt = nextPlayable(current < 0 ? -1 : current, 1);
      if (nxt >= 0) {
        load(nxt, true);
        return;
      }
      showNoAudioToast();
      return;
    }
    var p = audio.play();
    if (p && p.catch) p.catch(function () { /* autoplay blocked until user interacts */ });
  }

  function toggle() { audio.paused ? play() : audio.pause(); }

  btnPlay.addEventListener("click", toggle);
  btnPrev.addEventListener("click", function () {
    if (audio.currentTime > 3) { audio.currentTime = 0; return; }
    var prv = nextPlayable(current, -1);
    if (prv >= 0) load(prv, true);
    else showNoAudioToast();
  });
  btnNext.addEventListener("click", function () {
    var nxt = nextPlayable(current, 1);
    if (nxt >= 0) load(nxt, true);
    else showNoAudioToast();
  });

  items.forEach(function (item, i) {
    item.addEventListener("click", function () {
      if (item.hasAttribute("data-no-audio")) {
        load(i, false);   /* show the card in player bar without playing */
        return;
      }
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
    var nxt = nextPlayable(current, 1);
    if (nxt >= 0 && nxt !== current) load(nxt, true);
  });
  audio.addEventListener("error", function () {
    if (current >= 0 && items[current] && items[current].hasAttribute("data-no-audio")) return;
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

  /* Start on the first playable track (skip image-only). */
  var first = items[0] && items[0].hasAttribute("data-no-audio") ? nextPlayable(-1, 1) : 0;
  if (first >= 0) load(first, false);
})();
