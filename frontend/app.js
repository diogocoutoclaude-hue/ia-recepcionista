/* ── Recepcionista Virtual — frontend ── */

const statusBar = document.getElementById('status-bar');
const statusText = document.getElementById('status-text');
const spinner = document.querySelector('.spinner');
const chat = document.getElementById('chat');
const micBtn = document.getElementById('mic-btn');
const muteBtn = document.getElementById('mute-btn');
const clearBtn = document.getElementById('clear-btn');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');
const toastContainer = document.getElementById('toast-container');

let history = [];
let muted = false;
let recording = false;
let currentAudio = null;
let isStopping = false; // Prevent multiple simultaneous stops

// AudioContext + AudioWorklet recording state
let audioContext = null;
let workletNode = null;
let sourceNode = null;
let stream = null;
let pcmChunks = [];

// VAD state
const SILENCE_THRESHOLD = 0.008;
const SILENCE_TIMEOUT = 2000;
let silenceStart = null;
let vadActive = false;

// ── Utilities ──────────────────────────────────────────────────────────────

function setStatus(text, cls = '', showSpinner = false) {
  statusText.textContent = text;
  statusBar.className = cls;
  if (showSpinner) {
    spinner.classList.remove('hidden');
  } else {
    spinner.classList.add('hidden');
  }
}

function showToast(message, type = 'info') {
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function appendMsg(role, text) {
  const div = document.createElement('div');
  div.className = `msg ${role === 'user' ? 'user' : role === 'system' ? 'system-msg' : 'assistant'}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'msg assistant typing-dots';
  el.id = 'typing';
  el.innerHTML = '<span></span><span></span><span></span>';
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

function removeTyping() {
  document.getElementById('typing')?.remove();
}

// ── WAV encoder ────────────────────────────────────────────────────────────

function encodeWav(samples, sampleRate) {
  const len = samples.length;
  const buffer = new ArrayBuffer(44 + len * 2);
  const view = new DataView(buffer);

  function writeStr(off, str) {
    for (let i = 0; i < str.length; i++) view.setUint8(off + i, str.charCodeAt(i));
  }

  writeStr(0, 'RIFF');
  view.setUint32(4, 36 + len * 2, true);
  writeStr(8, 'WAVE');
  writeStr(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, 'data');
  view.setUint32(40, len * 2, true);

  let offset = 44;
  for (let i = 0; i < len; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    offset += 2;
  }
  return new Blob([buffer], { type: 'audio/wav' });
}

function concatFloat32Arrays(chunks) {
  let totalLength = 0;
  for (const c of chunks) totalLength += c.length;
  const result = new Float32Array(totalLength);
  let offset = 0;
  for (const c of chunks) { result.set(c, offset); offset += c.length; }
  return result;
}

// ── Audio level indicator ─────────────────────────────────────────────────

function updateMicLevel(rms) {
  const scale = Math.min(rms / 0.15, 1);
  const ringSize = 4 + scale * 18;
  const opacity = 0.15 + scale * 0.5;
  micBtn.style.boxShadow = `0 0 0 ${ringSize}px rgba(239, 68, 68, ${opacity})`;
}

function clearMicLevel() {
  micBtn.style.boxShadow = '';
}

// ── Audio recording via AudioWorklet ──────────────────────────────────────

const SAMPLE_RATE = 16000;

async function startRecording() {
  if (recording || isStopping) return;
  isStopping = false; // Reset flag when starting new recording

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { sampleRate: SAMPLE_RATE, channelCount: 1, echoCancellation: true, noiseSuppression: true }
    });
  } catch {
    setStatus('Acesso ao microfone negado', 'error');
    appendMsg('system', 'Acesso ao microfone negado. Permita o acesso e tente novamente.');
    showToast('Permissão do microfone necessária', 'error');
    return;
  }

  audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });

  try {
    setStatus('A preparar gravação…', 'thinking', true);
    await audioContext.audioWorklet.addModule('/static/audio-processor.js');
  } catch (err) {
    console.error('AudioWorklet failed:', err);
    setStatus('Erro ao iniciar gravação', 'error');
    showToast('Erro ao carregar módulo de gravação', 'error');
    stream.getTracks().forEach(t => t.stop());
    return;
  }

  sourceNode = audioContext.createMediaStreamSource(stream);
  workletNode = new AudioWorkletNode(audioContext, 'recorder-processor');
  pcmChunks = [];
  silenceStart = null;
  vadActive = false;

  workletNode.port.onmessage = (e) => {
    const { samples, rms } = e.data;
    pcmChunks.push(new Float32Array(samples));
    if (recording) updateMicLevel(rms);

    // Only process VAD if still recording and not stopping
    if (!recording || isStopping) return;

    if (rms > SILENCE_THRESHOLD) {
      vadActive = true;
      silenceStart = null;
    } else if (vadActive) {
      if (!silenceStart) {
        silenceStart = Date.now();
      } else if (Date.now() - silenceStart > SILENCE_TIMEOUT) {
        stopRecording();
      }
    }
  };

  sourceNode.connect(workletNode);
  workletNode.connect(audioContext.destination);

  recording = true;
  micBtn.classList.add('active');
  setStatus('A gravar… fale agora (para automaticamente)', 'listening');
  showToast('Gravação iniciada', 'info');
}

async function stopRecording() {
  if (!recording || isStopping) return;

  // Set all flags immediately and synchronously
  isStopping = true;
  recording = false;
  silenceStart = null; // Stop VAD from triggering again
  vadActive = false;

  micBtn.classList.remove('active');
  clearMicLevel();
  setStatus('A processar…', 'thinking', true);
  showToast('Gravação parada', 'success');

  //wait for a second to make sure all message was saved
  await new Promise(resolve => setTimeout(resolve, 1000));

  if (workletNode) { workletNode.port.postMessage('stop'); workletNode.disconnect(); }
  if (sourceNode) sourceNode.disconnect();
  if (audioContext) audioContext.close();
  if (stream) stream.getTracks().forEach(t => t.stop());

  const allSamples = concatFloat32Arrays(pcmChunks);
  pcmChunks = [];
  const wavBlob = encodeWav(allSamples, SAMPLE_RATE);

  if (wavBlob.size < 80000) {
    setStatus('Nenhum áudio captado — tente novamente');
    isStopping = false; // Reset flag
    return;
  }
  else console.log(wavBlob.size)

  await transcribeAndSend(wavBlob);
  isStopping = false; // Reset flag after transcription completes
}

async function transcribeAndSend(wavBlob, retryCount = 0) {
  const MAX_RETRIES = 2;
  try {
    setStatus('A transcrever…', 'thinking', true);
    const form = new FormData();
    form.append('audio', wavBlob, 'recording.wav');
    const res = await fetch('/transcribe', { method: 'POST', body: form });
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
    const { text } = await res.json();
    if (text && text.trim()) {
      await sendMessage(text.trim());
    } else {
      setStatus('Não foi possível ouvir — tente novamente');
      showToast('Não foi possível captar áudio. Por favor, fale mais alto.', 'warning');
    }
  } catch (err) {
    console.error('Transcription error:', err);
    if (retryCount < MAX_RETRIES) {
      setStatus(`A tentar novamente (${retryCount + 1}/${MAX_RETRIES})…`, 'thinking', true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return transcribeAndSend(wavBlob, retryCount + 1);
    }
    setStatus(`Erro na transcrição: ${err.message}`, 'error');
    showToast('Erro ao transcrever áudio. Tente novamente ou use o campo de texto.', 'error');
  }
}

// ── TTS ───────────────────────────────────────────────────────────────────

function stopSpeaking() {
  if (currentAudio) { currentAudio.pause(); currentAudio = null; }
}

// ── Backend: chat ─────────────────────────────────────────────────────────

async function sendMessage(userText) {
  if (!userText.trim()) return;
  stopSpeaking();
  appendMsg('user', userText);
  history.push({ role: 'user', content: userText });
  setStatus('A pensar…', 'thinking', true);
  showTyping();

  try {
    if (muted) {
      // Muted — text only, skip TTS
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
      const { reply } = await res.json();
      removeTyping();
      history.push({ role: 'assistant', content: reply });
      appendMsg('assistant', reply);
      setStatus('Pronto — clique no microfone ou escreva abaixo');
    } else {
      // Combined LLM + Piper TTS in one round trip
      const res = await fetch('/chat-speak/piper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);

      const reply = decodeURIComponent(res.headers.get('X-Reply-Text') || '');
      removeTyping();
      history.push({ role: 'assistant', content: reply });
      appendMsg('assistant', reply);

      setStatus('A falar…', 'speaking');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudio = audio;
      audio.onended = () => { URL.revokeObjectURL(url); currentAudio = null; setStatus('Pronto — clique no microfone ou escreva abaixo'); };
      audio.onerror = () => setStatus('Erro TTS', 'error');
      audio.play().catch(err => {
        console.warn('Audio play prevented:', err);
        setStatus('Áudio pronto (clique para ouvir)', 'error');
      });
    }
  } catch (err) {
    removeTyping();
    appendMsg('system', `Erro: ${err.message}`);
    setStatus('Erro — verifique a consola', 'error');
    console.error(err);
  }
}

// ── Controls ──────────────────────────────────────────────────────────────

micBtn.addEventListener('click', () => {
  if (recording) stopRecording();
  else { stopSpeaking(); startRecording(); }
});

muteBtn.addEventListener('click', () => {
  muted = !muted;
  muteBtn.textContent = muted ? '🔇' : '🔊';
  if (muted) {
    stopSpeaking();
    showToast('Voz desativada', 'info');
  } else {
    showToast('Voz ativada', 'success');
  }
});

clearBtn.addEventListener('click', () => {
  stopSpeaking();
  if (recording) stopRecording();
  history = [];
  chat.innerHTML = '';
  setStatus('Conversa apagada');
  showToast('Conversa reiniciada', 'success');
  setTimeout(() => sendMessage('Olá'), 400);
});

sendBtn.addEventListener('click', () => {
  const val = textInput.value.trim();
  if (val) { textInput.value = ''; sendMessage(val); }
});

textInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const val = textInput.value.trim();
    if (val) { textInput.value = ''; sendMessage(val); }
  }
});

// ── Unlock overlay & initial greeting ─────────────────────────────────────

let unlocked = false;
let workletLoaded = false;

window.addEventListener('load', () => {
  const overlay = document.getElementById('unlock-overlay');
  const unlockBtn = document.getElementById('unlock-btn');

  // Focus trap for accessibility
  unlockBtn.focus();

  overlay.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      unlockBtn.focus();
    }
  });

  unlockBtn.addEventListener('click', async () => {
    unlocked = true;
    overlay.classList.add('hidden');
    showToast('Bem-vindo! A recepcionista está pronta.', 'success');
    setTimeout(() => sendMessage('Olá'), 400);
  });

  // Support Enter key on unlock button
  unlockBtn.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      unlockBtn.click();
    }
  });
});
