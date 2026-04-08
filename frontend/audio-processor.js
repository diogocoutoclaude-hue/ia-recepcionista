/**
 * AudioWorkletProcessor — runs on a dedicated audio thread.
 * Collects PCM samples and computes RMS energy for VAD / level meter.
 */
class RecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._stopped = false;
    this.port.onmessage = (e) => {
      if (e.data === 'stop') this._stopped = true;
    };
  }

  process(inputs) {
    if (this._stopped) return false;

    const input = inputs[0];
    if (!input || !input[0] || input[0].length === 0) return true;

    const samples = input[0]; // Float32Array — mono channel

    // Compute RMS energy for VAD / level indicator
    let sum = 0;
    for (let i = 0; i < samples.length; i++) {
      sum += samples[i] * samples[i];
    }
    const rms = Math.sqrt(sum / samples.length);

    // Send a copy of the samples + energy to the main thread
    this.port.postMessage({ samples: samples.slice(), rms });

    return true;
  }
}

registerProcessor('recorder-processor', RecorderProcessor);
