(function () {
  const reader = document.querySelector("[data-pdf-url]");
  if (!reader) {
    return;
  }

  const pdfUrl = reader.dataset.pdfUrl;
  const title = reader.dataset.pdfTitle || "PDF";
  const stage = reader.querySelector("[data-pdf-stage]");
  const spreadStage = reader.querySelector("[data-pdf-spread-stage]");
  const thumbnailRail = reader.querySelector("[data-pdf-thumbnails]");
  const status = reader.querySelector("[data-pdf-status]");
  const pageInput = reader.querySelector("[data-pdf-page]");
  const totalLabel = reader.querySelector("[data-pdf-total]");
  const zoomLabel = reader.querySelector("[data-pdf-zoom]");
  const prevButton = reader.querySelector("[data-pdf-prev]");
  const nextButton = reader.querySelector("[data-pdf-next]");
  const zoomOutButton = reader.querySelector("[data-pdf-zoom-out]");
  const zoomInButton = reader.querySelector("[data-pdf-zoom-in]");
  const fitButton = reader.querySelector("[data-pdf-fit]");
  const singleButton = reader.querySelector("[data-pdf-single]");
  const spreadButton = reader.querySelector("[data-pdf-spread]");
  const fullscreenButton = reader.querySelector("[data-pdf-fullscreen]");
  const printButton = reader.querySelector("[data-pdf-print]");
  const primaryCanvas = reader.querySelector("[data-pdf-canvas-primary]");
  const secondaryCanvas = reader.querySelector("[data-pdf-canvas-secondary]");
  const secondaryPage = reader.querySelector("[data-pdf-secondary-page]");
  const primaryCaption = reader.querySelector("[data-pdf-caption-primary]");
  const secondaryCaption = reader.querySelector("[data-pdf-caption-secondary]");

  let pdfDocument = null;
  let pageNumber = 1;
  let pageCount = 1;
  let scale = 1;
  let mode = "single";
  let renderToken = 0;
  let thumbnailToken = 0;

  function setStatus(message, isError) {
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("pdf-reader-status-error", Boolean(isError));
  }

  function visiblePages() {
    if (mode === "spread" && pageNumber < pageCount && stage.clientWidth > 760) {
      return [pageNumber, pageNumber + 1];
    }
    return [pageNumber];
  }

  function updateControls() {
    const pages = visiblePages();
    pageInput.value = pageNumber;
    pageInput.max = pageCount;
    totalLabel.textContent = `/ ${pageCount}`;
    zoomLabel.textContent = `${Math.round(scale * 100)}%`;
    prevButton.disabled = pageNumber <= 1;
    nextButton.disabled = pages[pages.length - 1] >= pageCount;
    singleButton.classList.toggle("is-active", mode === "single");
    spreadButton.classList.toggle("is-active", mode === "spread");
  }

  function paintCanvas(canvas, pdfPage, renderScale) {
    const viewport = pdfPage.getViewport({ scale: renderScale });
    const ratio = window.devicePixelRatio || 1;
    const context = canvas.getContext("2d");

    canvas.width = Math.floor(viewport.width * ratio);
    canvas.height = Math.floor(viewport.height * ratio);
    canvas.style.width = `${Math.floor(viewport.width)}px`;
    canvas.style.height = `${Math.floor(viewport.height)}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);

    return pdfPage.render({
      canvasContext: context,
      viewport: viewport,
    }).promise;
  }

  function renderCurrentPages() {
    if (!pdfDocument) {
      return;
    }

    const token = ++renderToken;
    const pages = visiblePages();
    setStatus(pages.length === 2 ? `Opening pages ${pages[0]}-${pages[1]}...` : `Opening page ${pages[0]}...`);
    secondaryPage.hidden = pages.length === 1;
    spreadStage.classList.toggle("is-spread", pages.length === 2);
    updateControls();
    updateActiveThumbnail();

    Promise.all(
      pages.map(function (number, index) {
        const canvas = index === 0 ? primaryCanvas : secondaryCanvas;
        const caption = index === 0 ? primaryCaption : secondaryCaption;
        caption.textContent = `Page ${number}`;
        return pdfDocument.getPage(number).then(function (page) {
          return paintCanvas(canvas, page, scale);
        });
      })
    ).then(function () {
      if (token !== renderToken) {
        return;
      }
      setStatus("");
      updateControls();
    }).catch(function () {
      if (token !== renderToken) {
        return;
      }
      showFallback("PDF page could not be rendered. Use Open or Download.");
    });
  }

  function queueRender(number) {
    pageNumber = Math.min(Math.max(number, 1), pageCount);
    renderCurrentPages();
  }

  function fitWidth() {
    if (!pdfDocument) {
      return;
    }

    pdfDocument.getPage(pageNumber).then(function (page) {
      const baseViewport = page.getViewport({ scale: 1 });
      const pagesAcross = mode === "spread" && stage.clientWidth > 760 && pageNumber < pageCount ? 2 : 1;
      const availableWidth = Math.max(stage.clientWidth - 64 - (pagesAcross - 1) * 18, 280);
      scale = Math.min(Math.max((availableWidth / pagesAcross) / baseViewport.width, 0.48), 2.6);
      renderCurrentPages();
    });
  }

  function updateActiveThumbnail() {
    thumbnailRail.querySelectorAll("[data-thumbnail-page]").forEach(function (button) {
      const number = Number(button.dataset.thumbnailPage);
      const isActive = visiblePages().includes(number);
      button.classList.toggle("is-active", isActive);
    });
  }

  function renderThumbnails() {
    const token = ++thumbnailToken;
    thumbnailRail.innerHTML = "";

    for (let number = 1; number <= pageCount; number += 1) {
      const button = document.createElement("button");
      const canvas = document.createElement("canvas");
      const label = document.createElement("span");
      button.type = "button";
      button.className = "pdf-thumbnail";
      button.dataset.thumbnailPage = String(number);
      button.setAttribute("aria-label", `Go to page ${number}`);
      label.textContent = `Page ${number}`;
      button.appendChild(canvas);
      button.appendChild(label);
      button.addEventListener("click", function () {
        queueRender(number);
        stage.scrollTo({ top: 0, behavior: "smooth" });
      });
      thumbnailRail.appendChild(button);

      pdfDocument.getPage(number).then(function (page) {
        if (token !== thumbnailToken) {
          return null;
        }
        return paintCanvas(canvas, page, 0.18);
      }).catch(function () {
        canvas.remove();
      });
    }
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
    queueRender(pageNumber - (mode === "spread" ? 2 : 1));
  });

  nextButton.addEventListener("click", function () {
    queueRender(pageNumber + (mode === "spread" ? 2 : 1));
  });

  pageInput.addEventListener("change", function () {
    queueRender(Number(pageInput.value) || 1);
    stage.scrollTo({ top: 0, behavior: "smooth" });
  });

  zoomOutButton.addEventListener("click", function () {
    scale = Math.max(0.45, scale - 0.12);
    renderCurrentPages();
  });

  zoomInButton.addEventListener("click", function () {
    scale = Math.min(2.8, scale + 0.12);
    renderCurrentPages();
  });

  fitButton.addEventListener("click", fitWidth);

  singleButton.addEventListener("click", function () {
    mode = "single";
    fitWidth();
  });

  spreadButton.addEventListener("click", function () {
    mode = "spread";
    if (pageNumber > 1 && pageNumber % 2 === 0) {
      pageNumber -= 1;
    }
    fitWidth();
  });

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
      prevButton.click();
    }
    if (event.key === "ArrowRight") {
      nextButton.click();
    }
    if (event.key === "+") {
      zoomInButton.click();
    }
    if (event.key === "-") {
      zoomOutButton.click();
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
        renderThumbnails();
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
