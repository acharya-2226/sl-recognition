(() => {
  const root = document.querySelector('.validation-cycle') || document.querySelector('.verify-layout');
  if (!root) return;
  const video = root.querySelector('.sign-camera');
  const startButton = root.querySelector('.camera-start');
  const placeholder = root.querySelector('.camera-placeholder');
  const label = root.querySelector('.prediction-label');
  const confidence = root.querySelector('.prediction-confidence');
  const status = root.querySelector('.verify-status');
  const track = (root.dataset.track || 'ASL').toUpperCase();
  const canonicalTrack = track === 'NUMBER' ? 'NUM' : track;

  const defaultBackends = { NSL: 'http://127.0.0.1:5002', NUM: 'http://127.0.0.1:5003', ASL: 'http://127.0.0.1:5001' };
  const backendKey = canonicalTrack === 'NSL' ? 'backendNsl' : canonicalTrack === 'NUM' ? 'backendNumber' : 'backendAsl';
  const backend = root.dataset[backendKey] || defaultBackends[canonicalTrack] || defaultBackends.ASL;

  const canvas = document.createElement('canvas');
  canvas.width = 320; canvas.height = 240;
  let stream; let timer; let busy = false; let accepted = false;

  const normalize = value => String(value || '').trim().toLocaleUpperCase().replace(/\s+/g, '');
  const setStatus = (text, kind = '') => { status.textContent = text; status.className = `verify-status ${kind}`; };

  function currentTarget() {
    return root.dataset.target || root.querySelector('.cycle-title')?.textContent || '';
  }

  function renderCycleItem(item) {
    root.dataset.target = item.title;
    const title = root.querySelectorAll('.cycle-title');
    title.forEach(node => { node.textContent = item.title; });
    const desc = root.querySelector('.cycle-description'); if (desc) desc.textContent = item.description || 'Show the sign clearly in the camera frame.';
    const image = root.querySelector('.cycle-image');
    const visual = root.querySelector('.cycle-visual');
    if (image && item.image) image.src = item.image;
    else if (!image && item.image) { visual.innerHTML = `<img class="cycle-image" src="${item.image}" alt="sign reference">`; }
    else if (visual) visual.innerHTML = `<span class="cycle-title">${item.title}</span>`;
  }

  // Normalizes both response shapes into one common object:
  // ASL/NSL backends return {label, confidence, available, hand_detected}
  // Number backend returns {count, hand_detected} — no confidence/model concept
  function parseResult(result) {
    if (canonicalTrack === 'NUM') {
      const hasCount = result.hand_detected && typeof result.count === 'number';
      return {
        detectedValue: hasCount ? String(result.count) : null,
        confidenceText: hasCount ? null : 'Keep your hand inside the frame.',
        unavailable: false,
        handDetected: !!result.hand_detected,
      };
    }
    return {
      detectedValue: result.label || null,
      confidenceText: result.label ? `${Math.round((result.confidence || 0) * 100)}% confidence` : (result.available === false ? 'Model files were not found by the backend.' : 'Keep your hand inside the frame.'),
      unavailable: result.available === false,
      handDetected: !!result.hand_detected,
    };
  }

  async function inspectFrame() {
    if (busy || accepted || !stream || video.readyState < 2) return;
    busy = true;
    const ctx = canvas.getContext('2d'); ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    try {
      const response = await fetch(`${backend}/predict`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({image: canvas.toDataURL('image/jpeg', 0.72)})});
      const result = await response.json();
      const parsed = parseResult(result);

      label.textContent = parsed.detectedValue || (parsed.handDetected ? 'Recognizing…' : 'No hand detected');
      confidence.textContent = parsed.detectedValue ? (parsed.confidenceText || '') : parsed.confidenceText;

      const target = currentTarget();
      if (parsed.unavailable) setStatus(`The ${track} model is unavailable. Check the model and mapping paths.`, 'error');
      else if (parsed.detectedValue && normalize(parsed.detectedValue) === normalize(target) && (canonicalTrack === 'NUM' || (result.confidence || 0) >= 0.70)) await handleMatch();
      else if (parsed.detectedValue) setStatus(`Detected ${parsed.detectedValue}. Show ${target}.`);
    } catch (error) { setStatus(`Cannot reach the ${track} recognizer at ${backend}.`, 'error'); }
    finally { busy = false; }
  }

  async function handleMatch() {
    accepted = true; setStatus('Correct sign confirmed.', 'success');
    if (root.dataset.itemUrl) {
      setTimeout(() => { window.location.href = root.dataset.nextUrl; }, 850);
      return;
    }
    const items = JSON.parse(document.getElementById('cycle-items')?.textContent || '[]');
    const index = Number(root.dataset.cycleIndex || 0);
    const next = index + 1;
    root.dataset.cycleIndex = next;
    const current = root.querySelector('.cycle-current'); const bar = root.querySelector('.cycle-progress-bar');
    if (current) current.textContent = Math.min(next + 1, items.length);
    if (bar) bar.style.width = `${(next / items.length) * 100}%`;
    if (next >= items.length) {
      root.querySelector('.verify-layout').hidden = true; root.querySelector('.cycle-progress').hidden = true; root.querySelector('.cycle-complete').hidden = false;
      return;
    }
    renderCycleItem(items[next]); accepted = false; setStatus('New sign loaded. Show it when ready.');
  }

  async function startCamera() {
    if (stream) return;
    try {
      stream = await navigator.mediaDevices.getUserMedia({video: {width: 640, height: 480}, audio: false});
      video.srcObject = stream; placeholder.hidden = true; startButton.textContent = 'Camera running'; startButton.disabled = true;
      setStatus(`Camera ready. Show ${currentTarget()}.`); timer = setInterval(inspectFrame, 700);
    } catch (_) { setStatus('Camera permission was not granted. Allow access and try again.', 'error'); }
  }
  startButton.addEventListener('click', startCamera);
  startCamera();
  window.addEventListener('beforeunload', () => { if (timer) clearInterval(timer); stream?.getTracks().forEach(track => track.stop()); });
})();