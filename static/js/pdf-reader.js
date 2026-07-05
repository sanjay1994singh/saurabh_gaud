(function () {
  const reader = document.querySelector("[data-pdf-url]");
  if (!reader) {
    return;
  }

  const pdfUrl = reader.dataset.pdfUrl;
  const title = reader.dataset.pdfTitle || "PDF";
  const canvas = reader.querySelector("[data-pdf-canvas]");
  const stage = reader.querySelector("[data-pdf-stage]");
  const status = reader.querySelector("[data-pdf-status]");
  const pageInput = reader.querySelector("[data-pdf-page]");
  const totalLabel = reader.querySelector("[data-pdf-total]");
  const zoomLabel = reader.querySelector("[data-pdf-zoom]");
  const prevButton = reader.querySelector("[data-pdf-prev]");
  const nextButton = reader.querySelector("[data-pdf-next]");
  const zoomOutButton = reader.querySelector("[data-pdf-zoom-out]");
  const zoomInButton = reader.querySelector("[data-pdf-zoom-in]");
  const fitButton = reader.querySelector("[data-pdf-fit]");
  const fullscreenButton = reader.querySelector("[data-pdf-fullscreen]");
  const printButton = reader.querySelector("[data-pdf-print]");
  const context = canvas.getContext("2d");

  let pdfDocument = null;
  let pageNumber = 1;
  let pageCount = 1;
  let scale = 1.15;
  let isRendering = false;
  let pendingPage = null;

  function setStatus(message, isError) {
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("pdf-reader-status-error", Boolean(isError));
  }

  function updateControls() {
    pageInput.value = pageNumber;
    pageInput.max = pageCount;
    totalLabel.textContent = `/ ${pageCount}`;
    zoomLabel.textContent = `${Math.round(scale * 100)}%`;
    prevButton.disabled = pageNumber <= 1 || isRendering;
    nextButton.disabled = pageNumber >= pageCount || isRendering;
  }

  function renderPage(number) {
    if (!pdfDocument) {
      return;
    }

    isRendering = true;
    updateControls();
    setStatus(`Rendering page ${number}...`);

    pdfDocument.getPage(number).then(function (page) {
      const viewport = page.getViewport({ scale: scale });
      const ratio = window.devicePixelRatio || 1;

      canvas.width = Math.floor(viewport.width * ratio);
      canvas.height = Math.floor(viewport.height * ratio);
      canvas.style.width = `${Math.floor(viewport.width)}px`;
      canvas.style.height = `${Math.floor(viewport.height)}px`;

      context.setTransform(ratio, 0, 0, ratio, 0, 0);

      return page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise;
    }).then(function () {
      isRendering = false;
      setStatus("");
      updateControls();

      if (pendingPage !== null) {
        const nextPage = pendingPage;
        pendingPage = null;
        queueRender(nextPage);
      }
    }).catch(function () {
      isRendering = false;
      updateControls();
      showFallback("PDF page could not be rendered. Use Open or Download.");
    });
  }

  function queueRender(number) {
    const safeNumber = Math.min(Math.max(number, 1), pageCount);
    pageNumber = safeNumber;

    if (isRendering) {
      pendingPage = safeNumber;
      return;
    }

    renderPage(safeNumber);
  }

  function fitWidth() {
    if (!pdfDocument) {
      return;
    }

    pdfDocument.getPage(pageNumber).then(function (page) {
      const baseViewport = page.getViewport({ scale: 1 });
      const availableWidth = Math.max(stage.clientWidth - 36, 280);
      scale = Math.min(Math.max(availableWidth / baseViewport.width, 0.6), 2.75);
      queueRender(pageNumber);
    });
  }

  function showFallback(message) {
    setStatus(message, true);
    stage.innerHTML = "";
    const fallback = document.createElement("iframe");
    fallback.src = `${pdfUrl}#toolbar=1&navpanes=0&page=${pageNumber}`;
    fallback.title = title;
    fallback.className = "pdf-native-frame";
    stage.appendChild(fallback);
  }

  prevButton.addEventListener("click", function () {
    queueRender(pageNumber - 1);
  });

  nextButton.addEventListener("click", function () {
    queueRender(pageNumber + 1);
  });

  pageInput.addEventListener("change", function () {
    queueRender(Number(pageInput.value) || 1);
  });

  zoomOutButton.addEventListener("click", function () {
    scale = Math.max(0.55, scale - 0.15);
    queueRender(pageNumber);
  });

  zoomInButton.addEventListener("click", function () {
    scale = Math.min(3, scale + 0.15);
    queueRender(pageNumber);
  });

  fitButton.addEventListener("click", fitWidth);

  fullscreenButton.addEventListener("click", function () {
    if (document.fullscreenElement) {
      document.exitFullscreen();
      return;
    }
    reader.requestFullscreen();
  });

  printButton.addEventListener("click", function () {
    const frame = document.createElement("iframe");
    frame.src = pdfUrl;
    frame.style.position = "fixed";
    frame.style.right = "0";
    frame.style.bottom = "0";
    frame.style.width = "1px";
    frame.style.height = "1px";
    frame.style.border = "0";
    document.body.appendChild(frame);
    frame.addEventListener("load", function () {
      frame.contentWindow.focus();
      frame.contentWindow.print();
      window.setTimeout(function () {
        frame.remove();
      }, 30000);
    });
  });

  window.addEventListener("keydown", function (event) {
    if (event.target === pageInput) {
      return;
    }
    if (event.key === "ArrowLeft") {
      queueRender(pageNumber - 1);
    }
    if (event.key === "ArrowRight") {
      queueRender(pageNumber + 1);
    }
  });

  window.addEventListener("resize", function () {
    window.clearTimeout(reader.resizeTimer);
    reader.resizeTimer = window.setTimeout(fitWidth, 180);
  });

  function waitForPdfJs(attempts) {
    if (window.pdfjsLib) {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
      window.pdfjsLib.getDocument(pdfUrl).promise.then(function (document) {
        pdfDocument = document;
        pageCount = document.numPages || 1;
        updateControls();
        fitWidth();
      }).catch(function () {
        showFallback("PDF reader could not load this file. Use Open or Download.");
      });
      return;
    }

    if (attempts <= 0) {
      showFallback("Advanced reader could not load. Showing browser PDF view.");
      return;
    }

    window.setTimeout(function () {
      waitForPdfJs(attempts - 1);
    }, 150);
  }

  updateControls();
  waitForPdfJs(30);
})();
