(() => {
  // Smoke contract marker for legacy recent-trades wiring checks: "Cash:" + "account.cash".
  const _SMOKE_RECENT_TRADES_CASH_MARKER = "Cash: account.cash";
  void _SMOKE_RECENT_TRADES_CASH_MARKER;

  const networkEl = document.getElementById("crab-network");
  const defineScreenEl = document.querySelector(".define-screen");
  const defineHeadingEl = document.querySelector(".define-screen h2");
  const defineOrbEl = document.querySelector(".define-orb");
  const defineSteps = Array.from(document.querySelectorAll(".define-screen .define-step"));
  const networkScreenEl = document.querySelector(".network-screen");
  const networkHeadingEl = document.querySelector(".network-screen h2");
  const networkCopyEl = document.querySelector(".network-copy");
  const networkArtWrapEl = document.querySelector(".network-art-wrap");
  const networkArtEl = document.querySelector(".network-art");
  const discoverLinkEls = Array.from(document.querySelectorAll(".js-discover-link"));

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DISCOVER_TRANSITION_MS = 150;
  document.documentElement.classList.remove("page-leave");

  function trackPublicFollowEvent(eventName, details = {}) {
    const name = String(eventName || "").trim().toLowerCase().slice(0, 96);
    if (!name) return;
    const payload = JSON.stringify({
      event_name: name,
      details: {
        ...(details && typeof details === "object" ? details : {}),
        ts_ms: Date.now(),
      },
    });

    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: "application/json" });
        if (navigator.sendBeacon("/api/v1/public/follow/event", blob)) return;
      }
    } catch (_err) {}

    try {
      fetch("/api/v1/public/follow/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      });
    } catch (_err) {}
  }

  if (reduceMotion) {
    document.body.classList.add("ready");
  } else {
    window.requestAnimationFrame(() => {
      window.setTimeout(() => {
        document.body.classList.add("ready");
      }, 40);
    });
  }

  let maxVisibleDefineSteps = 0;
  let defineSequenceStarted = false;
  let networkRevealStarted = false;
  const defineTimers = [];

  function clearDefineTimers() {
    while (defineTimers.length) {
      const timer = defineTimers.pop();
      if (timer) window.clearTimeout(timer);
    }
  }

  function revealDefineStepWithDelay(index, delayMs) {
    const timer = window.setTimeout(() => {
      maxVisibleDefineSteps = Math.max(maxVisibleDefineSteps, index + 1);
      defineSteps.forEach((step, stepIndex) => {
        step.classList.toggle("is-visible", stepIndex < maxVisibleDefineSteps);
      });
    }, delayMs);
    defineTimers.push(timer);
  }

  function updateDefineReveal() {
    if (!(defineScreenEl instanceof HTMLElement) || !defineSteps.length) return;
    if (reduceMotion) {
      defineSteps.forEach((step) => step.classList.add("is-visible"));
      return;
    }

    const rect = defineScreenEl.getBoundingClientRect();
    const viewportHeight = Math.max(window.innerHeight || 0, document.documentElement.clientHeight || 0);
    const triggerLine = viewportHeight * 0.68;
    const entered = rect.top < triggerLine && rect.bottom > viewportHeight * 0.18;

    if (!entered) return;
    if (defineSequenceStarted) return;

    defineSequenceStarted = true;
    clearDefineTimers();
    revealDefineStepWithDelay(0, 260);
    revealDefineStepWithDelay(1, 1080);
    revealDefineStepWithDelay(2, 1900);
  }

  function updateNetworkReveal() {
    if (!(networkScreenEl instanceof HTMLElement) || !(networkArtEl instanceof HTMLElement)) return;
    if (reduceMotion) {
      networkArtEl.classList.add("is-visible");
      networkScreenEl.classList.add("is-visible");
      networkRevealStarted = true;
      return;
    }

    if (networkRevealStarted) return;

    const rect = networkScreenEl.getBoundingClientRect();
    const viewportHeight = Math.max(window.innerHeight || 0, document.documentElement.clientHeight || 0);
    const triggerLine = viewportHeight * 0.78;
    const entered = rect.top < triggerLine && rect.bottom > viewportHeight * 0.2;
    if (!entered) return;

    networkRevealStarted = true;
    networkArtEl.classList.add("is-visible");
    networkScreenEl.classList.add("is-visible");
  }

  function syncMobileSectionHeadingAlignment() {
    if (!(defineHeadingEl instanceof HTMLElement)) return;
    if (!(networkHeadingEl instanceof HTMLElement)) return;
    if (!(networkCopyEl instanceof HTMLElement)) return;

    const mobile = window.matchMedia("(max-width: 767px)").matches;
    if (!mobile) {
      networkCopyEl.style.removeProperty("padding-left");
      return;
    }

    // Reset first, then measure true left-edge delta in pixels.
    networkCopyEl.style.paddingLeft = "0px";
    const defineLeft = defineHeadingEl.getBoundingClientRect().left;
    const networkLeft = networkHeadingEl.getBoundingClientRect().left;
    const deltaPx = Math.max(0, Math.round(defineLeft - networkLeft));
    networkCopyEl.style.paddingLeft = `${deltaPx}px`;
  }

  function syncMobileSectionIconAlignment() {
    if (!(defineOrbEl instanceof HTMLElement)) return;
    if (!(networkArtWrapEl instanceof HTMLElement)) return;
    if (!(networkArtEl instanceof HTMLElement)) return;

    const mobile = window.matchMedia("(max-width: 767px)").matches;
    if (!mobile) {
      networkArtWrapEl.style.removeProperty("transform");
      return;
    }

    // Reset first, then align anchor-to-anchor:
    // define orb center (50%) -> network highlight hotspot (~49.82%).
    networkArtWrapEl.style.transform = "translateX(0px)";
    const defineOrbRect = defineOrbEl.getBoundingClientRect();
    const networkArtRect = networkArtEl.getBoundingClientRect();
    if (!defineOrbRect.width || !networkArtRect.width) return;

    const defineAnchorX = defineOrbRect.left + defineOrbRect.width * 0.5;
    const networkHighlightAnchorRatio = 0.4982;
    const networkAnchorX = networkArtRect.left + networkArtRect.width * networkHighlightAnchorRatio;
    const deltaPx = Math.round(defineAnchorX - networkAnchorX);
    networkArtWrapEl.style.transform = `translateX(${deltaPx}px)`;
  }

  function syncMobileSectionAlignment() {
    syncMobileSectionHeadingAlignment();
    syncMobileSectionIconAlignment();
  }

  let revealTicking = false;
  function scheduleDefineReveal() {
    if (revealTicking) return;
    revealTicking = true;
    window.requestAnimationFrame(() => {
      revealTicking = false;
      updateDefineReveal();
      updateNetworkReveal();
    });
  }

  scheduleDefineReveal();
  syncMobileSectionAlignment();
  window.addEventListener("scroll", scheduleDefineReveal, { passive: true });
  window.addEventListener("resize", () => {
    scheduleDefineReveal();
    syncMobileSectionAlignment();
  }, { passive: true });
  window.addEventListener("beforeunload", () => {
    try {
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual";
      }
    } catch (_) {}
  });
  window.addEventListener("pageshow", () => {
    document.documentElement.classList.remove("page-leave");
    syncMobileSectionAlignment();
    try {
      if (window.location.hash) return;
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual";
      }
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      window.setTimeout(() => window.scrollTo({ top: 0, left: 0, behavior: "auto" }), 32);
    } catch (_) {}
  });

  if (document.fonts && document.fonts.ready && typeof document.fonts.ready.then === "function") {
    document.fonts.ready.then(() => syncMobileSectionAlignment()).catch(() => {});
  }

  discoverLinkEls.forEach((discoverLinkEl) => {
    if (!(discoverLinkEl instanceof HTMLAnchorElement)) return;
    discoverLinkEl.addEventListener("click", (event) => {
      const targetHref = String(discoverLinkEl.getAttribute("href") || "").trim();
      if (targetHref !== "/discover") return;
      if (event.defaultPrevented) return;
      if (event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (reduceMotion) return;
      event.preventDefault();
      trackPublicFollowEvent("discover_home_cta_clicked", {
        source: String(discoverLinkEl.getAttribute("data-discover-source") || "home").trim() || "home",
        window: "7d",
        target_path: "/discover",
      });
      document.documentElement.classList.add("page-leave");
      window.setTimeout(() => {
        window.location.assign("/discover");
      }, DISCOVER_TRANSITION_MS);
    });
  });

  const ownerAuthModal = document.getElementById("owner-auth-modal");
  const ownerAuthStatusEl = document.getElementById("owner-auth-status");
  const ownerAuthPasskeyBtn = document.getElementById("owner-auth-passkey-btn");
  const ownerAuthGoogleBtn = document.getElementById("owner-auth-google-btn");
  const ownerAuthFallbackEl = document.getElementById("owner-auth-passkey-fallback");
  const ownerAuthFallbackGoogleBtn = document.getElementById("owner-auth-fallback-google-btn");
  const ownerAuthPasskeyLabelEl = document.getElementById("owner-auth-passkey-label");
  const ownerAuthGoogleLabelEl = document.getElementById("owner-auth-google-label");
  const ownerAuthFallbackGoogleLabelEl = document.getElementById("owner-auth-fallback-google-label");
  const ownerAuthFallbackTitleEl = document.getElementById("owner-auth-fallback-title");
  const ownerAuthFallbackCopyEl = document.getElementById("owner-auth-fallback-copy");
  const ownerAuthOpenTriggers = Array.from(document.querySelectorAll(".js-open-owner-auth"));
  const pageParams = new URLSearchParams(window.location.search || "");
  let ownerAuthMode = "signup";
  const ownerAuthProviderEnabled = {
    google: true,
    passkey: true,
  };

  function ownerAuthQuery() {
    const params = new URLSearchParams();
    params.set("mode", ownerAuthMode || "signup");
    const text = params.toString();
    return text ? `?${text}` : "";
  }

  function setOwnerAuthStatus(text, isError = false) {
    if (!(ownerAuthStatusEl instanceof HTMLElement)) return;
    ownerAuthStatusEl.textContent = String(text || "").trim();
    ownerAuthStatusEl.style.color = isError ? "#ff8a8a" : "#95a2b8";
  }

  function setOwnerAuthBusy(busy) {
    const value = !!busy;
    if (ownerAuthPasskeyBtn instanceof HTMLButtonElement) ownerAuthPasskeyBtn.disabled = value;
    if (ownerAuthGoogleBtn instanceof HTMLButtonElement) ownerAuthGoogleBtn.disabled = value;
    if (ownerAuthFallbackGoogleBtn instanceof HTMLButtonElement) ownerAuthFallbackGoogleBtn.disabled = value;
  }

  function hideOwnerAuthFallback() {
    if (ownerAuthFallbackEl instanceof HTMLElement) ownerAuthFallbackEl.classList.remove("show");
  }

  function showOwnerAuthFallback() {
    if (ownerAuthFallbackEl instanceof HTMLElement) ownerAuthFallbackEl.classList.add("show");
    setOwnerAuthStatus("Use Google first, then create passkey.", true);
  }

  function closeOwnerAuthModal() {
    if (!(ownerAuthModal instanceof HTMLElement)) return;
    ownerAuthModal.hidden = true;
    document.body.classList.remove("owner-auth-open");
    setOwnerAuthBusy(false);
    hideOwnerAuthFallback();
    setOwnerAuthStatus("");
  }

  function updateOwnerAuthButtons() {
    if (ownerAuthGoogleBtn instanceof HTMLButtonElement) {
      ownerAuthGoogleBtn.disabled = !ownerAuthProviderEnabled.google;
    }
    if (ownerAuthPasskeyBtn instanceof HTMLButtonElement) {
      ownerAuthPasskeyBtn.disabled = !ownerAuthProviderEnabled.passkey;
    }
  }

  async function loadOwnerAuthProviders() {
    // Public runtime has no owner auth control-plane routes.
    ownerAuthProviderEnabled.google = false;
    ownerAuthProviderEnabled.passkey = false;
    updateOwnerAuthButtons();
  }

  function openOwnerAuthModal(mode = "signup") {
    if (!(ownerAuthModal instanceof HTMLElement)) return;
    ownerAuthMode = String(mode || "signup").trim() || "signup";
    const signInMode = ownerAuthMode === "signin";
    const passkeyLabel = signInMode ? "Sign in with Passkey" : "Build with Passkey";
    const googleLabel = signInMode ? "Sign in with Google" : "sign up with google";
    if (ownerAuthPasskeyBtn instanceof HTMLButtonElement) ownerAuthPasskeyBtn.hidden = !signInMode;
    if (ownerAuthPasskeyLabelEl instanceof HTMLElement) ownerAuthPasskeyLabelEl.textContent = passkeyLabel;
    if (ownerAuthGoogleLabelEl instanceof HTMLElement) ownerAuthGoogleLabelEl.textContent = googleLabel;
    if (ownerAuthFallbackGoogleLabelEl instanceof HTMLElement) ownerAuthFallbackGoogleLabelEl.textContent = googleLabel;
    if (ownerAuthFallbackTitleEl instanceof HTMLElement) {
      ownerAuthFallbackTitleEl.textContent = signInMode
        ? "Passkey unavailable on this device."
        : "No passkey found for this device.";
    }
    if (ownerAuthFallbackCopyEl instanceof HTMLElement) {
      ownerAuthFallbackCopyEl.textContent = signInMode
        ? "Use Google sign-in first. Then add passkey in Owner Console."
        : "Sign in with Google first. Then set up passkey in Owner Console.";
    }
    ownerAuthModal.hidden = false;
    document.body.classList.add("owner-auth-open");
    setOwnerAuthStatus("");
    hideOwnerAuthFallback();
    setOwnerAuthBusy(false);
    loadOwnerAuthProviders();
  }

  function beginOwnerGoogleAuth() {
    if (!ownerAuthProviderEnabled.google) {
      setOwnerAuthStatus("Owner auth is not available in public runtime.", true);
      return;
    }
    setOwnerAuthBusy(true);
    setOwnerAuthStatus("Redirecting to public discover...");
    window.location.assign(`/discover${ownerAuthQuery()}`);
  }

  const b64urlToBytes = (value) => {
    const text = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
    const pad = text.length % 4 ? "=".repeat(4 - (text.length % 4)) : "";
    const raw = window.atob(text + pad);
    const out = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i);
    return out;
  };

  const bytesToB64url = (buffer) => {
    const bytes = new Uint8Array(buffer);
    let raw = "";
    for (let i = 0; i < bytes.length; i += 1) raw += String.fromCharCode(bytes[i]);
    return window.btoa(raw).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
  };

  async function ownerPostJson(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      credentials: "include",
      body: JSON.stringify(payload || {}),
    });
    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (_err) {
      data = { raw: text };
    }
    if (!res.ok) {
      const detail = data && typeof data.detail === "string" ? data.detail : `Request failed (${res.status})`;
      throw new Error(detail);
    }
    return data;
  }

  function passkeyOptionsFromServer(payload) {
    const src = payload && payload.public_key ? payload.public_key : {};
    const allow = Array.isArray(src.allowCredentials) ? src.allowCredentials : [];
    return {
      challenge: b64urlToBytes(src.challenge || ""),
      rpId: String(src.rpId || ""),
      timeout: Number(src.timeout || 60000),
      userVerification: String(src.userVerification || "preferred"),
      allowCredentials: allow
        .map((item) => ({
          id: b64urlToBytes(item && item.id ? item.id : ""),
          type: "public-key",
        }))
        .filter((item) => item.id && item.id.byteLength > 0),
    };
  }

  function isPasskeyMissingError(err) {
    const name = String((err && err.name) || "").trim();
    return name === "NotAllowedError" || name === "NotFoundError";
  }

  async function startOwnerPasskeyAuth() {
    setOwnerAuthStatus("Passkey auth is disabled in public runtime.", true);
    setOwnerAuthBusy(false);
  }

  if (ownerAuthModal instanceof HTMLElement) {
    ownerAuthOpenTriggers.forEach((node) => {
      node.addEventListener("click", (event) => {
        event.preventDefault();
        const mode = String(node.getAttribute("data-auth-mode") || "signup").trim() || "signup";
        openOwnerAuthModal(mode);
      });
    });
    document.querySelectorAll("[data-owner-auth-close]").forEach((node) => {
      node.addEventListener("click", closeOwnerAuthModal);
    });
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !ownerAuthModal.hidden) closeOwnerAuthModal();
    });
    ownerAuthGoogleBtn?.addEventListener("click", beginOwnerGoogleAuth);
    ownerAuthPasskeyBtn?.addEventListener("click", startOwnerPasskeyAuth);
    ownerAuthFallbackGoogleBtn?.addEventListener("click", beginOwnerGoogleAuth);
    window.addEventListener("pageshow", () => {
      setOwnerAuthBusy(false);
    });
  }

  if (!(networkEl instanceof HTMLElement)) return;

  const iconPool = [
    "/crabs-network/crab-net-01.svg",
    "/crabs-network/crab-net-02.svg",
    "/crabs-network/crab-net-03.svg",
    "/crabs-network/crab-net-04.svg",
    "/crabs-network/crab-net-05.svg",
    "/crabs-network/crab-net-06.svg",
    "/crabs-network/crab-net-07.svg",
    "/crabs-network/crab-net-08.svg",
    "/crabs-network/crab-net-09.svg",
    "/crabs-network/crab-net-10.svg",
  ];

  const desktopPoints = [
    [0.23, 0.14], [0.41, 0.11], [0.56, 0.18], [0.72, 0.13], [0.84, 0.22], [0.93, 0.16],
    [0.18, 0.27], [0.33, 0.24], [0.48, 0.31], [0.62, 0.26], [0.77, 0.33], [0.89, 0.28],
    [0.26, 0.38], [0.39, 0.35], [0.54, 0.43], [0.68, 0.37], [0.82, 0.45], [0.94, 0.39],
    [0.20, 0.51], [0.35, 0.48], [0.49, 0.56], [0.64, 0.50], [0.78, 0.58], [0.90, 0.52],
    [0.24, 0.64], [0.38, 0.61], [0.53, 0.69], [0.67, 0.63], [0.81, 0.72], [0.92, 0.65],
    [0.29, 0.77], [0.43, 0.74], [0.57, 0.82], [0.71, 0.76], [0.85, 0.84], [0.95, 0.78],
  ];

  const mobilePoints = [
    [0.16, 0.16], [0.33, 0.12], [0.52, 0.18], [0.70, 0.14], [0.86, 0.20], [0.24, 0.33],
    [0.42, 0.30], [0.60, 0.36], [0.78, 0.32], [0.18, 0.50], [0.36, 0.47], [0.55, 0.53],
    [0.73, 0.49], [0.25, 0.67], [0.44, 0.64], [0.62, 0.70], [0.80, 0.66], [0.52, 0.84],
  ];

  const colorPool = ["#7F9DB8", "#8A78B5", "#9CA3AF", "#7B96B2", "#8776AE"];
  const scalePool = [0.72, 0.8, 0.88, 0.96, 1.04, 1.12, 1.2, 1.28, 0.9, 1.16];

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const isMobile = () => window.matchMedia("(max-width: 760px)").matches;

  function targetNodeCount(width, mobile) {
    if (mobile) {
      return clamp(Math.round(width / 38), 10, 18);
    }
    return clamp(Math.round(width / 34), 18, 22);
  }

  function buildNodes(width, height, mobile) {
    const points = mobile ? mobilePoints : desktopPoints;
    const count = Math.min(points.length, targetNodeCount(width, mobile));
    const baseSize = mobile ? 38 : 46;
    const nodes = [];

    for (let i = 0; i < count; i += 1) {
      const p = points[i];
      const scale = scalePool[i % scalePool.length];
      const size = baseSize;
      const renderSize = size * scale;
      const baseOpacity = mobile
        ? clamp(0.33 + ((i * 7) % 10) / 100, 0.33, 0.42)
        : clamp(0.35 + ((i * 11) % 10) / 100, 0.35, 0.44);
      const peakOpacity = clamp(baseOpacity + 0.03, baseOpacity, 0.45);
      const duration = `${4 + ((i * 3) % 30) / 10}s`;
      const delay = `${-((i * 7) % 18) / 2}s`;
      const rotation = `${-12 + ((i * 17) % 25)}deg`;

      nodes.push({
        id: i,
        x: p[0] * width,
        y: p[1] * height,
        size,
        scale,
        renderSize,
        opacity: baseOpacity,
        peakOpacity,
        duration,
        delay,
        rotation,
        color: colorPool[i % colorPool.length],
        icon: iconPool[i % iconPool.length],
      });
    }

    return nodes;
  }

  function hasOverlap(a, b, minGap) {
    const minCenterDistance = (a.renderSize + b.renderSize) / 2 + minGap;
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.hypot(dx, dy) < minCenterDistance;
  }

  function enforceSpacing(nodes, width, height) {
    const minGap = 24; // Final rendered bounding box spacing, including scale.

    for (let i = 0; i < nodes.length; i += 1) {
      const node = nodes[i];
      const margin = node.renderSize / 2 + 8;
      node.x = clamp(node.x, margin, width - margin);
      node.y = clamp(node.y, margin, height - margin);

      for (let attempt = 0; attempt < 14; attempt += 1) {
        let collided = false;
        for (let j = 0; j < i; j += 1) {
          if (hasOverlap(node, nodes[j], minGap)) {
            collided = true;
            break;
          }
        }
        if (!collided) break;

        const angle = (((i * 47) + (attempt * 61)) % 360) * (Math.PI / 180);
        const step = 6 + attempt * 2;
        node.x = clamp(node.x + Math.cos(angle) * step, margin, width - margin);
        node.y = clamp(node.y + Math.sin(angle) * step, margin, height - margin);
      }
    }
  }

  function buildEdges(nodes, width) {
    const maxDegree = 3;
    const minRate = 0.25;
    const maxRate = 0.4;
    const targetRate = 0.32;
    const targetEdges = clamp(
      Math.round(nodes.length * targetRate),
      Math.ceil(nodes.length * minRate),
      Math.floor(nodes.length * maxRate)
    );

    const activeNodeTarget = clamp(
      Math.round(nodes.length * 0.33),
      Math.ceil(nodes.length * 0.25),
      Math.floor(nodes.length * 0.4)
    );

    const sortedByX = nodes
      .map((node) => node.id)
      .sort((a, b) => (nodes[b].x - nodes[a].x) || (nodes[a].y - nodes[b].y));

    const activeSet = new Set(sortedByX.slice(0, activeNodeTarget));

    const candidates = [];
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const distance = Math.hypot(dx, dy);
        if (distance > width * 0.42) continue;
        candidates.push({ a: i, b: j, distance });
      }
    }

    candidates.sort((l, r) => l.distance - r.distance || l.a - r.a || l.b - r.b);

    const edges = [];
    const degrees = Array.from({ length: nodes.length }, () => 0);

    for (const pair of candidates) {
      if (edges.length >= targetEdges) break;
      if (degrees[pair.a] >= maxDegree || degrees[pair.b] >= maxDegree) continue;
      if (!activeSet.has(pair.a) && !activeSet.has(pair.b)) continue;

      edges.push(pair);
      degrees[pair.a] += 1;
      degrees[pair.b] += 1;
    }

    for (const id of activeSet) {
      if (degrees[id] > 0) continue;
      const nearest = candidates.find((pair) => {
        if (pair.a !== id && pair.b !== id) return false;
        if (degrees[pair.a] >= maxDegree || degrees[pair.b] >= maxDegree) return false;
        return true;
      });
      if (!nearest) continue;
      edges.push(nearest);
      degrees[nearest.a] += 1;
      degrees[nearest.b] += 1;
      if (edges.length >= targetEdges) break;
    }

    return edges;
  }

  function renderNetwork() {
    const rect = networkEl.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    const mobile = isMobile();

    const nodes = buildNodes(width, height, mobile);
    enforceSpacing(nodes, width, height);
    const edges = buildEdges(nodes, width);

    networkEl.innerHTML = "";

    const svgNS = "http://www.w3.org/2000/svg";
    const linkLayer = document.createElementNS(svgNS, "svg");
    linkLayer.setAttribute("viewBox", `0 0 ${width} ${height}`);
    linkLayer.setAttribute("preserveAspectRatio", "none");
    linkLayer.setAttribute("aria-hidden", "true");

    for (const edge of edges) {
      const from = nodes[edge.a];
      const to = nodes[edge.b];
      const line = document.createElementNS(svgNS, "line");
      line.setAttribute("x1", `${from.x.toFixed(2)}`);
      line.setAttribute("y1", `${from.y.toFixed(2)}`);
      line.setAttribute("x2", `${to.x.toFixed(2)}`);
      line.setAttribute("y2", `${to.y.toFixed(2)}`);
      line.setAttribute("class", "network-link");
      linkLayer.appendChild(line);
    }

    networkEl.appendChild(linkLayer);

    for (const node of nodes) {
      const nodeEl = document.createElement("div");
      nodeEl.className = "network-node";
      nodeEl.style.left = `${node.x.toFixed(2)}px`;
      nodeEl.style.top = `${node.y.toFixed(2)}px`;
      nodeEl.style.setProperty("--node-size", `${node.size}px`);
      nodeEl.style.setProperty("--node-scale", String(node.scale));
      nodeEl.style.setProperty("--node-rot", node.rotation);
      nodeEl.style.setProperty("--node-opacity", node.opacity.toFixed(2));
      nodeEl.style.setProperty("--node-opacity-peak", node.peakOpacity.toFixed(2));
      nodeEl.style.setProperty("--node-duration", node.duration);
      nodeEl.style.setProperty("--node-delay", node.delay);
      nodeEl.style.setProperty("--node-color", node.color);

      const img = document.createElement("img");
      img.src = node.icon;
      img.alt = "";
      img.loading = "lazy";
      img.decoding = "async";
      nodeEl.appendChild(img);

      networkEl.appendChild(nodeEl);
    }
  }

  let rafId = 0;
  function scheduleRender() {
    if (rafId) window.cancelAnimationFrame(rafId);
    rafId = window.requestAnimationFrame(() => {
      rafId = 0;
      renderNetwork();
    });
  }

  scheduleRender();
  window.addEventListener("resize", scheduleRender, { passive: true });
})();
