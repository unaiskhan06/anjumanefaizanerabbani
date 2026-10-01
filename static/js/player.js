/* Click-to-load YouTube player ("facade"): the heavy iframe only loads when the visitor presses play. */
(function () {
  "use strict";

  var warmed = false;
  function warmConnections() {
    if (warmed) return;
    warmed = true;
    ["https://www.youtube-nocookie.com", "https://www.google.com", "https://i.ytimg.com"].forEach(function (href) {
      var link = document.createElement("link");
      link.rel = "preconnect";
      link.href = href;
      document.head.appendChild(link);
    });
  }

  function loadPlayer(player) {
    var iframe = document.createElement("iframe");
    iframe.src = player.getAttribute("data-embed");
    iframe.title = player.getAttribute("data-title") || "YouTube video player";
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    player.innerHTML = "";
    player.appendChild(iframe);
    iframe.focus();
  }

  document.querySelectorAll("[data-player]").forEach(function (player) {
    var facade = player.querySelector(".player-facade");
    var thumb = player.querySelector(".player-thumb");

    // Upgrade to the HD thumbnail when YouTube has one (missing ones come back as a 120px placeholder).
    if (thumb && thumb.dataset.hq) {
      var hq = new Image();
      hq.onload = function () { if (hq.naturalWidth > 120) thumb.src = hq.src; };
      hq.src = thumb.dataset.hq;
    }
    if (!facade) return;
    facade.addEventListener("pointerenter", warmConnections, { once: true });
    facade.addEventListener("focus", warmConnections, { once: true });
    facade.addEventListener("click", function () { loadPlayer(player); });
  });
})();
