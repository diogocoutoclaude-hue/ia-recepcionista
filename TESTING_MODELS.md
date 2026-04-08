# Portuguese STT Model Testing Guide

This guide helps you test multiple local speech-to-text models optimized for European Portuguese (pt-PT) using Google Colab.

## Quick Start

1. **Open the notebook in Google Colab:**
   - Upload `portuguese_stt_testing.ipynb` to Google Drive
   - Right-click → Open with → Google Colaboratory
   - Or directly upload to Colab

2. **Enable GPU (Important!):**
   - Runtime → Change runtime type → GPU (T4 or better)
   - This makes testing 4-10x faster

3. **Upload your test audio:**
   - Use `Gravação2.m4a` or any Portuguese audio file
   - Formats supported: WAV, MP3, M4A, WebM, FLAC

4. **Run all cells:**
   - Runtime → Run all
   - Or press `Ctrl+F9`

5. **Wait for results:**
   - Testing takes ~5-15 minutes depending on audio length
   - Results will be displayed and downloadable as JSON

## Models Being Tested

### 1. Wav2Vec2 Portuguese Models
- **jonatasgrosman/wav2vec2-large-xlsr-53-portuguese**: Most popular Portuguese model
- **facebook/mms-1b-all**: Meta's 1000+ language model with Portuguese adapter

**Pros:**
- Specifically trained on Portuguese
- Good accent handling
- Fast inference

**Cons:**
- May struggle with domain-specific terms
- Sometimes less accurate than Whisper for complex audio

### 2. SeamlessM4T v2 (Meta)
- State-of-the-art multilingual model
- Strong Portuguese support (both pt-PT and pt-BR)

**Pros:**
- Latest technology from Meta
- Excellent multilingual capabilities
- Good with accents

**Cons:**
- Larger model size
- Slightly slower

### 3. Faster-Whisper (Large V2 & V3)
- Optimized Whisper implementation (CTranslate2)
- 4x faster than original Whisper
- 70% less memory usage

**Pros:**
- Fast and efficient
- Includes your dental clinic prompt
- Voice Activity Detection (VAD) built-in
- Production-ready

**Cons:**
- Still Whisper-based (but optimized)

### 4. Portuguese Fine-tuned Whisper
- **pierreguillou/whisper-large-v3-portuguese**: Community fine-tuned on Portuguese data

**Pros:**
- Specifically optimized for Portuguese
- Better than base Whisper for pt-PT

**Cons:**
- Depends on fine-tuning quality

## Expected Results

The notebook will output:

1. **Comparison Table:**
   - Model name
   - Processing time
   - Transcription preview

2. **Full Transcriptions:**
   - Complete text from each model
   - Easy to compare quality

3. **JSON Results File:**
   - All results saved
   - Includes timing and metadata

## What to Look For

When evaluating results, check for:

1. **Accuracy of European Portuguese:**
   - Proper handling of pt-PT vs pt-BR
   - Correct accent marks (á, ã, ç, etc.)
   - European Portuguese vocabulary

2. **Dental Terminology:**
   - consulta, marcação
   - dentista, ortodontia
   - obturação, branqueamento
   - Insurance names: ADSE, Multicare, Médis

3. **Context Understanding:**
   - Names (clinic name, person names)
   - Dates and times
   - Phone numbers

4. **Speed:**
   - Real-time factor (processing time vs audio duration)
   - Lower is better

## Next Steps After Testing

Once you identify the best model:

### Option A: Deploy Locally with Faster-Whisper
If Faster-Whisper wins:
```python
# Use in your main.py - much faster than current Groq setup
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio_path, language="pt")
```

### Option B: Deploy with Wav2Vec2
If Wav2Vec2 wins:
```python
from transformers import pipeline

pipe = pipeline("automatic-speech-recognition",
                model="jonatasgrosman/wav2vec2-large-xlsr-53-portuguese")
result = pipe(audio_array)
```

### Option C: Deploy with SeamlessM4T
If SeamlessM4T wins:
```python
from transformers import SeamlessM4Tv2ForSpeechToText, AutoProcessor

processor = AutoProcessor.from_pretrained("facebook/seamless-m4t-v2-large")
model = SeamlessM4Tv2ForSpeechToText.from_pretrained("facebook/seamless-m4t-v2-large")
```

### Option D: Hybrid Approach (Recommended)
Use the fastest model + LLM post-processing:
1. Transcribe with best model
2. Pass to LLM (like GPT-4 or Claude) with context:
   ```
   "Fix any transcription errors in this Portuguese dental clinic call.
   Context: Clínica Dentária Sol Nascente, common terms: consulta, marcação..."
   ```
3. Get corrected transcription

## Troubleshooting

**Out of Memory Error:**
- Use smaller batch sizes
- Switch to CPU (slower but works)
- Use smaller models first

**Model Download Fails:**
- Check internet connection
- Models are large (1-3GB each)
- May need to restart runtime

**SeamlessM4T Error:**
- Requires latest transformers
- Try: `!pip install -U transformers`

**Poor Results for All Models:**
- Audio quality issues
- Background noise
- Check if audio is actually Portuguese
- Try noise reduction preprocessing

## Tips for Best Results

1. **Audio Quality Matters:**
   - Clear audio = better transcription
   - Reduce background noise
   - Use your audio normalization (already implemented)

2. **Test with Multiple Samples:**
   - Don't rely on one audio file
   - Test with different speakers
   - Test with different scenarios (appointment, emergency, etc.)

3. **Consider the Trade-offs:**
   - Accuracy vs Speed
   - Cloud vs Local
   - Cost vs Quality

4. **Hybrid Approaches Work:**
   - Fast model + LLM correction
   - Multiple models + voting
   - Model ensemble

## Questions to Answer After Testing

- [ ] Which model has the best accuracy for pt-PT?
- [ ] Which model handles dental terms best?
- [ ] What's the speed vs quality trade-off?
- [ ] Can you run the best model locally on your server?
- [ ] Would LLM post-processing help?
- [ ] Should you use a hybrid approach?

## Need Help?

If you need assistance integrating the winning model into your FastAPI app, I can help you:
- Set up the model in production
- Optimize inference speed
- Add LLM post-processing
- Create fallback mechanisms
- Handle edge cases

Good luck with testing! 🚀
