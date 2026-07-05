(function () {
  const pagesScript = document.getElementById("patrikaPagesData");
  const yearOptionsScript = document.getElementById("patrikaYearOptionsData");
  const reader = document.querySelector("[data-patrika-reader]");
  if (!pagesScript || !reader) {
    return;
  }

  const pages = JSON.parse(pagesScript.textContent);
  const yearOptions = yearOptionsScript ? JSON.parse(yearOptionsScript.textContent) : [];
  const patrikaByYear = new Map(yearOptions.map(function (option) {
    return [option.year, option];
  }));
  const paperFrame = document.getElementById("patrikaPaperFrame");
  const paperImage = document.getElementById("patrikaPaperImage");
  const readerShell = document.querySelector(".patrika-reader-shell");
  const pageStage = document.querySelector(".patrika-page-stage");
  const pageSelect = document.getElementById("patrikaPageSelect");
  const yearPicker = document.getElementById("patrikaYearPicker");
  const pagesDrawer = document.getElementById("patrikaPagesDrawer");
  const menuDrawer = document.getElementById("patrikaMenuDrawer");
  const toast = document.getElementById("patrikaReaderToast");
  const clipBox = document.getElementById("patrikaClipBox");
  const cropResult = document.getElementById("patrikaCropResult");
  const cropPreview = document.getElementById("patrikaCropPreview");
  const bookmarkList = document.getElementById("patrikaBookmarkList");
  const thumbnails = Array.from(document.querySelectorAll("[data-patrika-thumbnail]"));

  const bookmarkKey = `patrika-bookmarks-${reader.dataset.patrikaId || "latest"}`;
  let pageIndex = Math.max(0, pageSelect ? pageSelect.selectedIndex : 0);
  let zoom = 1;
  let clipMode = false;
  let clipStart = null;
  let swipeStart = null;
  let pinchStartDistance = 0;
  let pinchStartZoom = 1;
  let croppedImageUrl = "";

  function showToast(message) {
    if (!toast) {
      return;
    }
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(function () {
      toast.hidden = true;
    }, 2400);
  }

  function setReaderMobileSize() {
    const isMobile = window.matchMedia("(max-width: 760px)").matches
      || window.matchMedia("(hover: none) and (pointer: coarse)").matches;
    document.body.classList.toggle("patrika-reader-mobile", isMobile);

    if (!isMobile || !paperImage) {
      document.documentElement.style.removeProperty("--patrika-reader-page-height");
      document.documentElement.style.removeProperty("--patrika-reader-page-width");
      document.documentElement.style.removeProperty("--patrika-site-header-height");
      document.documentElement.style.removeProperty("--patrika-toolbar-height");
      document.documentElement.style.removeProperty("--patrika-pager-height");
      return;
    }

    const siteHeaderHeight = document.querySelector(".site-header")?.getBoundingClientRect().height || 0;
    const toolbarHeight = document.querySelector(".patrika-toolbar")?.getBoundingClientRect().height || 0;
    const viewportHeight = window.visualViewport?.height || window.innerHeight;
    const pagerHeight = document.querySelector(".patrika-bottom-pager")?.getBoundingClientRect().height || 42;
    const availableHeight = Math.max(260, viewportHeight - siteHeaderHeight - toolbarHeight - pagerHeight - 22);
    const ratio = paperImage.naturalWidth && paperImage.naturalHeight
      ? paperImage.naturalWidth / paperImage.naturalHeight
      : 0.68;
    const pageWidth = Math.max(200, Math.min(window.innerWidth * 0.96, availableHeight * ratio));
    document.documentElement.style.setProperty("--patrika-site-header-height", `${siteHeaderHeight}px`);
    document.documentElement.style.setProperty("--patrika-toolbar-height", `${toolbarHeight}px`);
    document.documentElement.style.setProperty("--patrika-pager-height", `${pagerHeight}px`);
    document.documentElement.style.setProperty("--patrika-reader-page-height", `${availableHeight}px`);
    document.documentElement.style.setProperty("--patrika-reader-page-width", `${pageWidth}px`);
  }

  function getBookmarks() {
    try {
      return JSON.parse(window.localStorage.getItem(bookmarkKey)) || [];
    } catch (error) {
      return [];
    }
  }

  function saveBookmarks(bookmarks) {
    window.localStorage.setItem(bookmarkKey, JSON.stringify(bookmarks));
  }

  function renderBookmarks() {
    const bookmarks = getBookmarks();
    if (!bookmarkList) {
      return;
    }
    if (bookmarks.length === 0) {
      bookmarkList.innerHTML = "<h3>Bookmarks</h3><p>No bookmarked pages yet.</p>";
      return;
    }
    bookmarkList.innerHTML = "<h3>Bookmarks</h3>" + bookmarks.map(function (bookmark) {
      return `<button type="button" data-bookmark-page="${bookmark.index}">${bookmark.label}</button>`;
    }).join("");
  }

  function hideClipBox() {
    if (!clipBox) {
      return;
    }
    clipBox.hidden = true;
    clipBox.style.cssText = "";
  }

  function closeCropResult() {
    if (cropResult) {
      cropResult.hidden = true;
    }
  }

  function renderPage() {
    if (!paperImage || pages.length === 0) {
      return;
    }

    const page = pages[pageIndex];
    paperImage.src = page.image;
    paperImage.alt = `${page.title} patrika page`;
    if (pageSelect) {
      pageSelect.selectedIndex = pageIndex;
    }
    thumbnails.forEach(function (thumbnail, index) {
      thumbnail.classList.toggle("is-active", index === pageIndex);
    });
    hideClipBox();
    closeCropResult();
  }

  function setPage(nextIndex) {
    if (pages.length === 0) {
      return;
    }
    pageIndex = Math.max(0, Math.min(pages.length - 1, nextIndex));
    renderPage();
  }

  function setZoom(nextZoom, announce) {
    zoom = Math.max(0.65, Math.min(2.4, nextZoom));
    paperFrame.style.transform = `scale(${zoom})`;
    if (announce !== false) {
      showToast(`Zoom ${Math.round(zoom * 100)}%`);
    }
  }

  function getTouchDistance(touches) {
    const deltaX = touches[0].clientX - touches[1].clientX;
    const deltaY = touches[0].clientY - touches[1].clientY;
    return Math.hypot(deltaX, deltaY);
  }

  function startPagePinch(event) {
    if (clipMode || event.touches.length !== 2) {
      return;
    }
    event.preventDefault();
    swipeStart = null;
    pinchStartDistance = getTouchDistance(event.touches);
    pinchStartZoom = zoom;
  }

  function movePagePinch(event) {
    if (!pinchStartDistance || event.touches.length !== 2) {
      return;
    }
    event.preventDefault();
    const nextDistance = getTouchDistance(event.touches);
    setZoom(pinchStartZoom * (nextDistance / pinchStartDistance), false);
  }

  function endPagePinch(event) {
    if (event.touches.length < 2) {
      pinchStartDistance = 0;
      pinchStartZoom = zoom;
    }
  }

  function preventBrowserGesture(event) {
    event.preventDefault();
  }

  function fitPage() {
    setZoom(1);
    document.querySelector(".patrika-page-stage")?.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  function toggleBookmark() {
    if (pages.length === 0) {
      return;
    }

    const page = pages[pageIndex];
    const bookmarks = getBookmarks();
    const exists = bookmarks.some(function (bookmark) {
      return bookmark.index === pageIndex;
    });
    const nextBookmarks = exists
      ? bookmarks.filter(function (bookmark) { return bookmark.index !== pageIndex; })
      : bookmarks.concat([{ index: pageIndex, label: page.title }]);

    saveBookmarks(nextBookmarks);
    renderBookmarks();
    showToast(exists ? `${page.title} removed from bookmarks` : `${page.title} bookmarked`);
  }

  function setClipMode(nextMode) {
    clipMode = nextMode;
    document.body.classList.toggle("patrika-clip-mode", clipMode);
    document.querySelectorAll('[data-patrika-action="clip"]').forEach(function (button) {
      button.classList.toggle("is-active-tool", clipMode);
    });
    if (!clipMode) {
      hideClipBox();
    }
  }

  function pointOnImage(event) {
    const imageRect = paperImage.getBoundingClientRect();
    return {
      x: (event.clientX - imageRect.left) / zoom,
      y: (event.clientY - imageRect.top) / zoom,
    };
  }

  function updateClipBox(start, current) {
    const left = Math.min(start.x, current.x);
    const top = Math.min(start.y, current.y);
    const width = Math.abs(current.x - start.x);
    const height = Math.abs(current.y - start.y);
    clipBox.hidden = false;
    clipBox.style.left = `${left}px`;
    clipBox.style.top = `${top}px`;
    clipBox.style.width = `${width}px`;
    clipBox.style.height = `${height}px`;
  }

  function makeClip(start, end) {
    const left = Math.min(start.x, end.x);
    const top = Math.min(start.y, end.y);
    const width = Math.abs(end.x - start.x);
    const height = Math.abs(end.y - start.y);

    if (width < 24 || height < 24) {
      showToast("Clip area is too small");
      hideClipBox();
      return "";
    }

    const ratioX = paperImage.naturalWidth / paperImage.clientWidth;
    const ratioY = paperImage.naturalHeight / paperImage.clientHeight;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * ratioX);
    canvas.height = Math.round(height * ratioY);
    canvas.getContext("2d").drawImage(
      paperImage,
      Math.round(left * ratioX),
      Math.round(top * ratioY),
      canvas.width,
      canvas.height,
      0,
      0,
      canvas.width,
      canvas.height
    );
    return canvas.toDataURL("image/png");
  }

  function showCropResult(imageUrl) {
    croppedImageUrl = imageUrl;
    cropPreview.src = imageUrl;
    cropResult.hidden = false;
    setClipMode(false);
    showToast("Crop ready");
  }

  function downloadCurrentCrop() {
    if (!croppedImageUrl) {
      showToast("Please crop a page first");
      return;
    }
    const link = document.createElement("a");
    link.download = `patrika-page-${pageIndex + 1}-clip.png`;
    link.href = croppedImageUrl;
    link.click();
  }

  async function shareCurrentCrop() {
    if (!croppedImageUrl) {
      showToast("Please crop a page first");
      return;
    }

    try {
      const response = await fetch(croppedImageUrl);
      const blob = await response.blob();
      const file = new File([blob], `patrika-page-${pageIndex + 1}-clip.png`, { type: "image/png" });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ title: document.title, text: "Cropped patrika page", files: [file] });
        return;
      }
    } catch (error) {
      // Native file sharing is optional.
    }

    const imageWindow = window.open("", "_blank", "noopener,noreferrer");
    if (imageWindow) {
      imageWindow.document.write(`<img src="${croppedImageUrl}" alt="Cropped page" style="max-width:100%">`);
    }
  }

  function shareTo(platform) {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(document.title);
    const shareUrl = platform === "facebook"
      ? `https://www.facebook.com/sharer/sharer.php?u=${url}`
      : platform === "whatsapp"
        ? `https://wa.me/?text=${text}%20-%20${url}`
        : `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
    window.open(shareUrl, "_blank", "noopener,noreferrer,width=720,height=520");
  }

  async function copyReaderLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      showToast("Reader link copied");
    } catch (error) {
      showToast(window.location.href);
    }
  }

  function handleSwipe(endX, endY, elapsed) {
    if (!swipeStart || clipMode) {
      swipeStart = null;
      return;
    }
    const deltaX = endX - swipeStart.x;
    const deltaY = endY - swipeStart.y;
    swipeStart = null;
    if (Math.abs(deltaX) < 44 || Math.abs(deltaX) < Math.abs(deltaY) * 1.2 || elapsed > 1100) {
      return;
    }
    setPage(deltaX < 0 ? pageIndex + 1 : pageIndex - 1);
  }

  function shouldIgnoreSwipeTarget(target) {
    return Boolean(target.closest(
      "button, select, input, label, aside, .patrika-bottom-pager, .patrika-toolbar, .patrika-pages-drawer, .patrika-menu-drawer, .patrika-crop-result"
    ));
  }

  function startReaderSwipe(event) {
    if (clipMode || event.touches.length !== 1 || shouldIgnoreSwipeTarget(event.target)) {
      swipeStart = null;
      return;
    }

    const touch = event.touches[0];
    swipeStart = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };
  }

  function finishReaderSwipe(event) {
    if (!swipeStart || clipMode || event.changedTouches.length !== 1 || shouldIgnoreSwipeTarget(event.target)) {
      swipeStart = null;
      return;
    }

    const touch = event.changedTouches[0];
    handleSwipe(touch.clientX, touch.clientY, Date.now() - swipeStart.time);
  }

  document.addEventListener("click", function (event) {
    const bookmarkButton = event.target.closest("[data-bookmark-page]");
    if (bookmarkButton) {
      setPage(Number(bookmarkButton.dataset.bookmarkPage));
      menuDrawer.hidden = true;
      return;
    }

    const thumbnail = event.target.closest("[data-patrika-thumbnail]");
    if (thumbnail) {
      setPage(Number(thumbnail.dataset.patrikaThumbnail));
      pagesDrawer.hidden = true;
      return;
    }

    const actionButton = event.target.closest("[data-patrika-action]");
    if (!actionButton) {
      return;
    }

    const action = actionButton.dataset.patrikaAction;
    if (action === "previous") {
      setPage(pageIndex - 1);
    } else if (action === "next") {
      setPage(pageIndex + 1);
    } else if (action === "first") {
      setPage(0);
    } else if (action === "last") {
      setPage(pages.length - 1);
    } else if (action === "reload") {
      window.location.reload();
    } else if (action === "zoom-in") {
      setZoom(zoom + 0.15);
    } else if (action === "zoom-out") {
      setZoom(zoom - 0.15);
    } else if (action === "fit") {
      fitPage();
    } else if (action === "bookmark") {
      toggleBookmark();
    } else if (action === "clip") {
      setClipMode(!clipMode);
      showToast(clipMode ? "Drag on the page to crop" : "Crop mode off");
    } else if (action === "pages") {
      pagesDrawer.hidden = false;
    } else if (action === "close-pages") {
      pagesDrawer.hidden = true;
    } else if (action === "menu") {
      renderBookmarks();
      menuDrawer.hidden = false;
    } else if (action === "close-menu") {
      menuDrawer.hidden = true;
    } else if (action === "download-crop") {
      downloadCurrentCrop();
    } else if (action === "share-crop") {
      shareCurrentCrop();
    } else if (action === "new-crop") {
      closeCropResult();
      setClipMode(true);
      showToast("Drag on the page to crop");
    } else if (action === "close-crop") {
      closeCropResult();
    } else if (action === "share-facebook") {
      shareTo("facebook");
    } else if (action === "share-whatsapp") {
      shareTo("whatsapp");
    } else if (action === "share-x") {
      shareTo("x");
    } else if (action === "copy-link") {
      copyReaderLink();
    } else if (action === "print") {
      window.print();
    } else if (action === "fullscreen") {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        reader.requestFullscreen();
      }
    }
  });

  pageSelect?.addEventListener("change", function () {
    setPage(pageSelect.selectedIndex);
  });

  yearPicker?.addEventListener("change", function () {
    const selectedYear = yearPicker.value;
    if (!selectedYear) {
      return;
    }

    const nextPatrika = patrikaByYear.get(selectedYear);
    if (!nextPatrika) {
      showToast("इस वर्ष की पत्रिका उपलब्ध नहीं है");
      return;
    }

    window.location.href = nextPatrika.url;
  });

  paperImage?.addEventListener("pointerdown", function (event) {
    if (!clipMode) {
      return;
    }
    event.preventDefault();
    paperImage.setPointerCapture(event.pointerId);
    clipStart = pointOnImage(event);
    updateClipBox(clipStart, clipStart);
  });

  paperImage?.addEventListener("pointermove", function (event) {
    if (!clipMode || !clipStart) {
      return;
    }
    updateClipBox(clipStart, pointOnImage(event));
  });

  paperImage?.addEventListener("pointerup", function (event) {
    if (!clipMode || !clipStart) {
      return;
    }
    const imageUrl = makeClip(clipStart, pointOnImage(event));
    clipStart = null;
    if (imageUrl) {
      showCropResult(imageUrl);
    }
  });

  readerShell?.addEventListener("touchstart", startReaderSwipe, { passive: true });
  readerShell?.addEventListener("touchend", finishReaderSwipe, { passive: true });
  readerShell?.addEventListener("touchcancel", function () {
    swipeStart = null;
  }, { passive: true });
  pageStage?.addEventListener("touchstart", startPagePinch, { passive: false });
  pageStage?.addEventListener("touchmove", movePagePinch, { passive: false });
  pageStage?.addEventListener("touchend", endPagePinch, { passive: true });
  pageStage?.addEventListener("touchcancel", endPagePinch, { passive: true });
  pageStage?.addEventListener("gesturestart", preventBrowserGesture);
  pageStage?.addEventListener("gesturechange", preventBrowserGesture);

  document.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") {
      setPage(pageIndex - 1);
    } else if (event.key === "ArrowRight") {
      setPage(pageIndex + 1);
    } else if (event.key === "+" || event.key === "=") {
      setZoom(zoom + 0.15);
    } else if (event.key === "-") {
      setZoom(zoom - 0.15);
    } else if (event.key === "Escape") {
      pagesDrawer.hidden = true;
      menuDrawer.hidden = true;
      closeCropResult();
      setClipMode(false);
    }
  });

  window.addEventListener("resize", setReaderMobileSize);
  window.addEventListener("orientationchange", function () {
    window.setTimeout(setReaderMobileSize, 250);
  });
  window.visualViewport?.addEventListener("resize", setReaderMobileSize);
  paperImage?.addEventListener("load", setReaderMobileSize);

  renderBookmarks();
  renderPage();
  setReaderMobileSize();
})();
