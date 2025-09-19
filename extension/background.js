// Background service worker: store default API base and handle checks
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.get({ apiBase: '' }, (s) => {
    if (!s.apiBase) {
      chrome.storage.sync.set({ apiBase: 'http://127.0.0.1:5000' });
    }
  });
});

async function getApiBase() {
  return await new Promise((resolve) => chrome.storage.sync.get({ apiBase: 'http://127.0.0.1:5000' }, resolve));
}

function extractHostname(inputUrl) {
  try {
    const u = new URL(inputUrl);
    return u.hostname;
  } catch (_) {
    try { return new URL('http://' + inputUrl).hostname; } catch (e) { return inputUrl; }
  }
}

async function checkUrl(url) {
  const { apiBase } = await getApiBase();
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), 15000);
  try {
    const domain = extractHostname(url);
    const resp = await fetch(`${apiBase}/api/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain }),
      signal: controller.signal
    });
    const data = await resp.json().catch(() => null);
    return { statusCode: resp.status, ok: resp.ok, data };
  } finally {
    clearTimeout(t);
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === 'CHECK_URL' && msg.url) {
    checkUrl(msg.url)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // async
  }
});





