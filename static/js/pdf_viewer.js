/* ==========================================================================
   Modern In-Website PDF Viewer (powered by PDF.js)
   - Matches Google Docs / Clean Viewer aesthetics (floating bottom pill, popout)
   - Handles both local (/media/pdfs/...) and remote (Cloudinary) files
   - High-DPI canvas rendering with smooth vertical scroll & lazy-loading
   - Interactive zoom in/out/fit, keyboard shortcuts, page jumping & fullscreen
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
  const viewerWrap = document.getElementById("pdfViewer");
  if (!viewerWrap) return;

  const pdfUrl = viewerWrap.dataset.pdfUrl;
  if (!pdfUrl) return;

  const scrollContainer = document.getElementById("pdfScrollContainer");
  const pagesContainer = document.getElementById("pdfPages");
  const loadingState = document.getElementById("pdfLoading");
  const toolbar = document.getElementById("pdfToolbar");
  const prevBtn = document.getElementById("pdfPrevBtn");
  const nextBtn = document.getElementById("pdfNextBtn");
  const currentPageInput = document.getElementById("pdfCurrentPage");
  const totalPagesEl = document.getElementById("pdfTotalPages");
  const zoomInBtn = document.getElementById("pdfZoomInBtn");
  const zoomOutBtn = document.getElementById("pdfZoomOutBtn");
  const zoomResetBtn = document.getElementById("pdfZoomResetBtn");
  const fullscreenBtn = document.getElementById("pdfFullscreenBtn");

  if (!window.pdfjsLib) {
    console.error("PDF.js library is not loaded.");
    if (loadingState) {
      loadingState.innerHTML = `
        <div style="text-align:center; padding: 24px;">
          <p style="margin-bottom: 12px; color: #fff;">Unable to load PDF viewer engine.</p>
          <a class="btn btn-primary" href="${pdfUrl}" target="_blank" rel="noopener">Open PDF directly</a>
        </div>`;
    }
    return;
  }

  // Set worker source
  pdfjsLib.GlobalWorkerOptions.workerSrc = window.PDF_WORKER_SRC || "/static/js/vendor/pdf.worker.min.js";

  let pdfDoc = null;
  let totalPages = 0;
  let currentPage = 1;
  let userZoom = 1.0;
  let baseScale = 1.0;
  let pageWidth = 0;
  let pageHeight = 0;
  const renderedPages = new Set();
  const renderingPages = new Set();
  let pageElements = [];
  let isNavigating = false;

  let renderObserver = null;
  let visiblePageObserver = null;

  async function init() {
    try {
      const loadingTask = pdfjsLib.getDocument({
        url: pdfUrl,
        cMapUrl: "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/",
        cMapPacked: true,
      });

      pdfDoc = await loadingTask.promise;
      totalPages = pdfDoc.numPages;
      if (totalPagesEl) totalPagesEl.textContent = totalPages;
      if (currentPageInput) currentPageInput.max = totalPages;

      const firstPage = await pdfDoc.getPage(1);
      const initialViewport = firstPage.getViewport({ scale: 1.0 });
      pageWidth = initialViewport.width;
      pageHeight = initialViewport.height;

      calculateBaseScale();
      createPagePlaceholders();
      setupObservers();

      if (loadingState) loadingState.style.display = "none";
      if (toolbar) toolbar.style.display = "flex";

      renderVisiblePages();
    } catch (err) {
      console.error("Error loading PDF document:", err);
      if (loadingState) {
        loadingState.innerHTML = `
          <div style="text-align:center; padding: 24px;">
            <p style="margin-bottom: 12px; color: #fff;">Failed to render document preview.</p>
            <a class="btn btn-primary" href="${pdfUrl}" target="_blank" rel="noopener" download>Download / View PDF</a>
          </div>`;
      }
    }
  }

  function calculateBaseScale() {
    if (!scrollContainer || pageWidth === 0) return;
    const availableWidth = scrollContainer.clientWidth - 48;
    if (availableWidth > 0 && pageWidth > 0) {
      baseScale = Math.min(availableWidth / pageWidth, 1.4);
    } else {
      baseScale = 1.0;
    }
  }

  function getEffectiveScale() {
    return baseScale * userZoom;
  }

  function createPagePlaceholders() {
    pagesContainer.innerHTML = "";
    pageElements = [];
    renderedPages.clear();
    renderingPages.clear();

    const scale = getEffectiveScale();
    const targetW = Math.floor(pageWidth * scale);
    const targetH = Math.floor(pageHeight * scale);

    for (let i = 1; i <= totalPages; i++) {
      const pageCard = document.createElement("div");
      pageCard.className = "pdf-page-card";
      pageCard.id = `pdf-page-${i}`;
      pageCard.dataset.pageNumber = i;
      pageCard.style.width = `${targetW}px`;
      pageCard.style.height = `${targetH}px`;

      const canvas = document.createElement("canvas");
      canvas.className = "pdf-page-canvas";
      pageCard.appendChild(canvas);

      pagesContainer.appendChild(pageCard);
      pageElements.push(pageCard);
    }
  }

  function setupObservers() {
    if (renderObserver) renderObserver.disconnect();
    if (visiblePageObserver) visiblePageObserver.disconnect();

    renderObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const pageNum = parseInt(entry.target.dataset.pageNumber, 10);
            renderPage(pageNum);
          }
        });
      },
      {
        root: scrollContainer,
        rootMargin: "400px 0px 400px 0px",
      }
    );

    pageElements.forEach((el) => renderObserver.observe(el));

    visiblePageObserver = new IntersectionObserver(
      (entries) => {
        if (isNavigating) return;
        let mostVisible = null;
        let maxRatio = 0;
        entries.forEach((entry) => {
          if (entry.intersectionRatio > maxRatio) {
            maxRatio = entry.intersectionRatio;
            mostVisible = entry.target;
          }
        });
        if (mostVisible) {
          const num = parseInt(mostVisible.dataset.pageNumber, 10);
          updateCurrentPage(num);
        }
      },
      {
        root: scrollContainer,
        threshold: [0.2, 0.5, 0.8],
      }
    );

    pageElements.forEach((el) => visiblePageObserver.observe(el));
  }

  async function renderPage(pageNum) {
    if (!pdfDoc || renderedPages.has(pageNum) || renderingPages.has(pageNum)) return;
    renderingPages.add(pageNum);

    try {
      const page = await pdfDoc.getPage(pageNum);
      const pageCard = document.getElementById(`pdf-page-${pageNum}`);
      if (!pageCard) return;

      const canvas = pageCard.querySelector("canvas");
      const ctx = canvas.getContext("2d");

      const scale = getEffectiveScale();
      const viewport = page.getViewport({ scale: scale });
      const dpr = window.devicePixelRatio || 1;

      canvas.width = Math.floor(viewport.width * dpr);
      canvas.height = Math.floor(viewport.height * dpr);
      canvas.style.width = `${Math.floor(viewport.width)}px`;
      canvas.style.height = `${Math.floor(viewport.height)}px`;

      pageCard.style.width = `${Math.floor(viewport.width)}px`;
      pageCard.style.height = `${Math.floor(viewport.height)}px`;

      const renderContext = {
        canvasContext: ctx,
        transform: [dpr, 0, 0, dpr, 0, 0],
        viewport: viewport,
      };

      await page.render(renderContext).promise;
      renderedPages.add(pageNum);
    } catch (err) {
      console.error(`Error rendering page ${pageNum}:`, err);
    } finally {
      renderingPages.delete(pageNum);
    }
  }

  function renderVisiblePages() {
    pageElements.forEach((el) => {
      const rect = el.getBoundingClientRect();
      const containerRect = scrollContainer.getBoundingClientRect();
      if (rect.bottom >= containerRect.top - 300 && rect.top <= containerRect.bottom + 300) {
        const pageNum = parseInt(el.dataset.pageNumber, 10);
        renderPage(pageNum);
      }
    });
  }

  function updateCurrentPage(num) {
    if (num < 1 || num > totalPages) return;
    currentPage = num;
    if (currentPageInput && document.activeElement !== currentPageInput) {
      currentPageInput.value = currentPage;
    }
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
  }

  function scrollToPage(pageNum) {
    if (pageNum < 1 || pageNum > totalPages) return;
    updateCurrentPage(pageNum);
    const targetCard = document.getElementById(`pdf-page-${pageNum}`);
    if (targetCard) {
      isNavigating = true;
      targetCard.scrollIntoView({ behavior: "smooth", block: "start" });
      renderPage(pageNum);
      setTimeout(() => {
        isNavigating = false;
      }, 500);
    }
  }

  function applyZoom(newZoom) {
    userZoom = Math.max(0.5, Math.min(newZoom, 2.5));
    const scale = getEffectiveScale();
    const targetW = Math.floor(pageWidth * scale);
    const targetH = Math.floor(pageHeight * scale);

    pageElements.forEach((el) => {
      el.style.width = `${targetW}px`;
      el.style.height = `${targetH}px`;
      const canvas = el.querySelector("canvas");
      if (canvas) {
        canvas.style.width = `${targetW}px`;
        canvas.style.height = `${targetH}px`;
      }
    });

    renderedPages.clear();
    renderingPages.clear();
    renderVisiblePages();
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => scrollToPage(currentPage - 1));
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", () => scrollToPage(currentPage + 1));
  }

  if (currentPageInput) {
    currentPageInput.addEventListener("change", (e) => {
      const val = parseInt(e.target.value, 10);
      if (!isNaN(val)) scrollToPage(val);
    });
    currentPageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        currentPageInput.blur();
      }
    });
  }

  if (zoomInBtn) {
    zoomInBtn.addEventListener("click", () => applyZoom(userZoom + 0.2));
  }
  if (zoomOutBtn) {
    zoomOutBtn.addEventListener("click", () => applyZoom(userZoom - 0.2));
  }
  if (zoomResetBtn) {
    zoomResetBtn.addEventListener("click", () => {
      calculateBaseScale();
      applyZoom(1.0);
    });
  }

  if (fullscreenBtn) {
    fullscreenBtn.addEventListener("click", () => {
      if (!document.fullscreenElement) {
        if (viewerWrap.requestFullscreen) viewerWrap.requestFullscreen();
        else if (viewerWrap.webkitRequestFullscreen) viewerWrap.webkitRequestFullscreen();
      } else {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
      }
    });
  }

  viewerWrap.setAttribute("tabindex", "0");
  viewerWrap.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft" || e.key === "PageUp") {
      e.preventDefault();
      scrollToPage(currentPage - 1);
    } else if (e.key === "ArrowRight" || e.key === "PageDown") {
      e.preventDefault();
      scrollToPage(currentPage + 1);
    } else if (e.key === "+" || e.key === "=") {
      e.preventDefault();
      applyZoom(userZoom + 0.2);
    } else if (e.key === "-") {
      e.preventDefault();
      applyZoom(userZoom - 0.2);
    } else if (e.key === "0") {
      e.preventDefault();
      calculateBaseScale();
      applyZoom(1.0);
    }
  });

  let resizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      calculateBaseScale();
      applyZoom(userZoom);
    }, 200);
  });

  init();
});
