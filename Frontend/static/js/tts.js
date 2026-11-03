(() => {
  'use strict';

  const root = document.querySelector('.tts-page');
  if (!root) return;

  const video = root.querySelector('.tts-camera');
  const startButton = root.querySelector('.tts-camera-start');
  const placeholder = root.querySelector('.tts-camera-placeholder');
  const status = root.querySelector('.tts-status');
  const detected = root.querySelector('#tts-detected');
  const confidence = root.querySelector('#tts-confidence');
  const holdBar = root.querySelector('#tts-hold-bar');
  const holdLabel = root.querySelector('#tts-hold-label');
  const bufferField = root.querySelector('#tts-buffer');
  const playButton = root.querySelector('#tts-play');
  const pauseButton = root.querySelector('#tts-pause');
  const clearButton = root.querySelector('#tts-clear');
  const trackButtons = Array.from(root.querySelectorAll('.tts-track-button'));

  const backendByTrack = {
    ASL: root.dataset.backendAsl,
    NSL: root.dataset.backendNsl,
    NUM: root.dataset.backendNum,
  };
  const HOLD_MS = 1000;
  const CONFIDENCE_THRESHOLD = 0.70;
  const canvas = document.createElement('canvas');
  canvas.width = 320;
  canvas.height = 240;

  let track = (root.dataset.initialTrack || '').toUpperCase();
  let stream = null;
  let timer = null;
  let busy = false;
  let buffer = '';
  let candidate = '';
  let candidateSince = 0;
  let committedCandidate = '';

  // SpeechSynthesis is local, immediate, offline-capable, and needs no API key.
  // Cloud TTS would add a network round trip, cost, and another failure point.
  const speechSupported = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

  function setStatus(message, kind) {
    status.textContent = message;
    status.className = `tts-status ${kind || ''}`;
  }

  function normalize(value) {
    return String(value || '').trim().toLocaleUpperCase().replace(/\s+/g, '');
  }

  function updateHold(progress) {
    const bounded = Math.max(0, Math.min(100, progress));
    holdBar.style.width = `${bounded}%`;
    holdLabel.textContent = `${Math.round(bounded)}%`;
  }

  function resetHold() {
    candidate = '';
    candidateSince = 0;
    committedCandidate = '';
    updateHold(0);
  }

  function speak(text) {
    if (!speechSupported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    // No voice is forced: the browser selects the user's default system voice.
    window.speechSynthesis.speak(utterance);
  }

  function removeLastSymbol(text) {
    if (typeof Intl !== 'undefined' && Intl.Segmenter) {
      const segments = Array.from(new Intl.Segmenter(undefined, {granularity: 'grapheme'}).segment(text));
      return segments.slice(0, -1).map(segment => segment.segment).join('');
    }
    return Array.from(text).slice(0, -1).join('');
  }

  function commitSign(value) {
    const control = normalize(value).toLowerCase();

    // These are editing commands, not text to append or words to speak.
    // The recognizer may return SPACE, SPACEBAR, or a spaced variant such as
    // "space bar"; normalize() removes case and internal whitespace first.
    if (control === 'space' || control === 'spacebar') {
      // Prevent repeated space signs from creating accidental double spaces.
      if (buffer && !buffer.endsWith(' ')) buffer += ' ';
      bufferField.value = buffer;
      if (speechSupported) window.speechSynthesis.cancel();
      setStatus('Space added to the text buffer.', 'success');
      return;
    }

    if (control === 'del' || control === 'backspace') {
      buffer = removeLastSymbol(buffer);
      bufferField.value = buffer;
      if (speechSupported) window.speechSynthesis.cancel();
      setStatus('Last sign removed from the text buffer.', 'success');
      return;
    }

    buffer += value;
    bufferField.value = buffer;
    speak(value);
    setStatus(`Added ${value} to the text buffer.`, 'success');
  }

  function resetDetectionForTrack() {
    resetHold();
    detected.textContent = 'Waiting for a hand…';
    confidence.textContent = `Using ${track === 'NUM' ? 'Number' : track} recognition.`;
  }

  function selectTrack(nextTrack, selectedButton) {
    track = nextTrack;
    trackButtons.forEach(button => {
      const isSelected = button === selectedButton;
      button.classList.toggle('active', isSelected);
      button.setAttribute('aria-selected', String(isSelected));
    });
    resetDetectionForTrack();
    setStatus(`Selected ${track === 'NUM' ? 'Number' : track}. Hold a sign steadily for one second.`);
  }

  function parseResult(result) {
    if (track === 'NUM') {
      if (result.hand_detected && typeof result.count === 'number') {
        return {
          value: String(result.count),
          confidenceText: 'Hand count detected',
          unavailable: false,
        };
      }
      return {
        value: '',
        confidenceText: 'Keep your hand inside the frame.',
        unavailable: false,
      };
    }

    return {
      value: result.label || '',
      confidenceText: result.label
        ? `${Math.round((result.confidence || 0) * 100)}% confidence`
        : result.available === false
          ? 'Model files were not found by the backend.'
          : 'Keep your hand inside the frame.',
      unavailable: result.available === false,
    };
  }

  function updateHoldState(value) {
    if (!value) {
      resetHold();
      return false;
    }

    if (normalize(value) !== normalize(candidate)) {
      candidate = value;
      candidateSince = Date.now();
      committedCandidate = '';
      updateHold(0);
      return false;
    }

    const elapsed = Date.now() - candidateSince;
    const progress = Math.min(100, (elapsed / HOLD_MS) * 100);
    updateHold(progress);

    if (elapsed >= HOLD_MS && committedCandidate !== candidate) {
      committedCandidate = candidate;
      commitSign(candidate);
      return true;
    }
    return false;
  }

  async function inspectFrame() {
    if (busy || !stream || video.readyState < 2) return;
    busy = true;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    try {
      const backend = backendByTrack[track];
      const response = await fetch(`${backend}/predict`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image: canvas.toDataURL('image/jpeg', 0.72)}),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Recognizer returned ${response.status}`);

      const parsed = parseResult(result);
      detected.textContent = parsed.value || (result.hand_detected ? 'Recognizing…' : 'No hand detected');
      confidence.textContent = parsed.confidenceText;

      if (parsed.unavailable) {
        setStatus(`The ${track} model is unavailable. Check the model and mapping paths.`, 'error');
        resetHold();
        return;
      }

      if (parsed.value && track !== 'NUM' && (result.confidence || 0) < CONFIDENCE_THRESHOLD) {
        setStatus('Prediction is below 70% confidence. Hold the sign steadily.', '');
        resetHold();
        return;
      }

      const committed = updateHoldState(parsed.value);
      if (!committed && parsed.value) {
        const elapsed = Date.now() - candidateSince;
        const remaining = Math.max(0, HOLD_MS - elapsed);
        setStatus(`Hold ${parsed.value} steadily for ${Math.ceil(remaining / 100) / 10}s.`, '');
      }
    } catch (error) {
      resetHold();
      setStatus(`Cannot reach the ${track} recognizer. Check that its Flask service is running.`, 'error');
    } finally {
      busy = false;
    }
  }

  async function startCamera() {
    if (stream) {
      try {
        await video.play();
        startButton.textContent = 'Camera running';
        startButton.disabled = true;
        setStatus(`Camera ready. Hold a ${track === 'NUM' ? 'Number' : track} sign steadily.`);
        if (!timer) timer = window.setInterval(inspectFrame, 700);
      } catch (error) {
        setStatus('Camera permission is granted. Click Start preview again.', '');
      }
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus('Camera access requires localhost or HTTPS in a supported browser.', 'error');
      return;
    }

    try {
      const cameraStream = await navigator.mediaDevices.getUserMedia({
        video: {width: 640, height: 480},
        audio: false,
      });
      stream = cameraStream;
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      video.srcObject = stream;
      placeholder.hidden = true;
      startButton.textContent = 'Camera running';
      startButton.disabled = true;

      // Some browsers block play() when startup began without a user gesture.
      // Keep the valid stream attached and let the fallback button retry playback.
      try {
        await video.play();
      } catch (playError) {
        setStatus('Camera permission is granted. Click Camera running to start the preview.', '');
        startButton.textContent = 'Start preview';
        startButton.disabled = false;
        return;
      }

      setStatus(`Camera ready. Hold a ${track === 'NUM' ? 'Number' : track} sign steadily.`);
      timer = window.setInterval(inspectFrame, 700);
    } catch (error) {
      stream = null;
      const reason = error && error.name === 'NotAllowedError'
        ? 'Camera permission was denied. Allow camera access and try again.'
        : error && error.name === 'NotFoundError'
          ? 'No camera was found on this device.'
          : error && error.name === 'NotReadableError'
            ? 'The camera is already being used by another application.'
            : 'Camera could not be opened. Use localhost or HTTPS and check browser permissions.';
      setStatus(reason, 'error');
    }
  }

  trackButtons.forEach(button => {
    button.addEventListener('click', () => selectTrack(button.dataset.track, button));
  });

  playButton.addEventListener('click', () => {
    if (!buffer) {
      setStatus('The text buffer is empty.', 'error');
      return;
    }
    speak(buffer);
    setStatus('Playing the text buffer.', 'success');
  });

  pauseButton.addEventListener('click', () => {
    if (!speechSupported) {
      setStatus('Speech synthesis is not supported by this browser.', 'error');
      return;
    }
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      pauseButton.textContent = 'Pause';
      setStatus('Speech resumed.', 'success');
    } else if (window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
      pauseButton.textContent = 'Resume';
      setStatus('Speech paused.');
    } else {
      setStatus('No speech is currently playing.');
    }
  });

  clearButton.addEventListener('click', () => {
    buffer = '';
    bufferField.value = '';
    resetHold();
    if (speechSupported) window.speechSynthesis.cancel();
    pauseButton.textContent = 'Pause';
    setStatus('Text buffer cleared.', 'success');
  });

  if (!speechSupported) {
    setStatus('Speech synthesis is unavailable; recognition will still work.', 'error');
    playButton.disabled = true;
    pauseButton.disabled = true;
  }

  if (track) {
    const initialButton = trackButtons.find(button => button.dataset.track === track);
    if (initialButton) selectTrack(track, initialButton);
    startCamera();
  }

  function cleanup() {
    if (timer) window.clearInterval(timer);
    if (speechSupported) window.speechSynthesis.cancel();
    if (stream) stream.getTracks().forEach(cameraTrack => cameraTrack.stop());
  }

  window.addEventListener('beforeunload', cleanup);
  window.addEventListener('pagehide', cleanup);
})();
