(() => {
  const ID = 'phishing-result-card';
  function removeExisting() {
    const el = document.getElementById(ID);
    if (el) el.remove();
  }
  function renderCard(data) {
    const label = data.label;
    const score = (data.score ?? 0).toFixed(3);
    removeExisting();
    const card = document.createElement('div');
    card.id = ID;
    card.style.position = 'fixed';
    card.style.top = '16px';
    card.style.right = '16px';
    card.style.zIndex = '2147483647';
    card.style.width = '170px';
    card.style.borderRadius = '6px';
    card.style.background = '#fff';
    card.style.boxShadow = '0 8px 24px rgba(0,0,0,0.20)';
    card.style.fontFamily = 'system-ui, -apple-system, Segoe UI, Roboto, Arial';
    card.style.color = '#212121';

    const header = document.createElement('div');
    header.textContent = 'RESULTS';
    header.style.fontWeight = '600';
    header.style.fontSize = '13px';
    header.style.letterSpacing = '0.6px';
    header.style.textAlign = 'center';
    header.style.padding = '8px 10px 0 10px';
    header.style.color = '#424242';

    const circleWrap = document.createElement('div');
    circleWrap.style.display = 'flex';
    circleWrap.style.alignItems = 'center';
    circleWrap.style.justifyContent = 'center';
    circleWrap.style.padding = '6px 10px 14px 10px';

    const circle = document.createElement('div');
    circle.style.width = '96px';
    circle.style.height = '96px';
    circle.style.borderRadius = '50%';
    circle.style.background = label === 'phishing' ? '#ef5350' : '#66bb6a';
    circle.style.display = 'flex';
    circle.style.alignItems = 'center';
    circle.style.justifyContent = 'center';
    circle.style.color = '#fff';
    circle.style.fontWeight = '600';
    circle.style.boxShadow = 'inset 0 0 0 6px rgba(0,0,0,0.06)';
    circle.textContent = label === 'phishing' ? 'Phishing' : 'Safe';

    const footer = document.createElement('div');
    footer.style.fontSize = '11px';
    footer.style.color = '#757575';
    footer.style.textAlign = 'center';
    footer.style.padding = '0 10px 10px 10px';
    footer.textContent = `Score: ${score}`;

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '4px';
    closeBtn.style.right = '6px';
    closeBtn.style.width = '22px';
    closeBtn.style.height = '22px';
    closeBtn.style.border = 'none';
    closeBtn.style.background = 'transparent';
    closeBtn.style.color = '#9e9e9e';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = () => card.remove();

    circleWrap.appendChild(circle);
    card.appendChild(closeBtn);
    card.appendChild(header);
    card.appendChild(circleWrap);
    card.appendChild(footer);
    document.documentElement.appendChild(card);

    if (label !== 'phishing') {
      setTimeout(() => { try { card.remove(); } catch (_) {} }, 4000);
    }
  }

  async function runCheck() {
    try {
      const url = window.location.href;
      const response = await new Promise((resolve) => {
        try {
          chrome.runtime.sendMessage({ type: 'CHECK_URL', url }, (resp) => resolve(resp));
        } catch (e) { resolve({ ok: false, error: String(e) }); }
      });
      if (!response || !response.ok) return; 
      const data = response.data;
      if (!data || data.status !== 'ok') return;
      renderCard(data);
    } catch (_) { /* ignore */ }
  }

  // Initial run
  runCheck();
  // Re-run when URL changes (SPA support)
  let lastHref = location.href;
  setInterval(() => {
    if (lastHref !== location.href) {
      lastHref = location.href;
      runCheck();
    }
  }, 1500);
})();





