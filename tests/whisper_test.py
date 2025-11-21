"""
Streaming ASR with Whisper and a fixed-size moving context window.

Strategy:
 - Keep a rolling PCM buffer of exactly `context_seconds` seconds.
 - On every step (new chunk or timer), run ASR on the entire buffer.
 - Diff the newly produced full-buffer transcript vs previous full-buffer transcript
   and emit only the new tail text (delta).
 - Use overlap/step size to control latency vs stability.
"""

# FasterWhisper requires cuDNN and cuBLAS (install from Nvidia website)
# TODO: add option to use FireRedASR (which is larger at 1.1b instead of 808m parameters but supposedly performs much better at Mandarin)
# TODO: test how well this performs on audio with a lot of noise eg: background music and sfx. If the performance is lackluster, then consider adding a neural voice isolator step before ASR.
# BUG: Whisper hallucinates nonsense from silence. Need to add VAD to skip silent segments

import asyncio
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from difflib import SequenceMatcher
from typing import Callable, Optional
import io

import soundcard as sc
from silero_vad import (load_silero_vad,
                        read_audio,
                        get_speech_timestamps,
                        save_audio,
                        VADIterator,
                        collect_chunks)


# Choose model backend: 'faster-whisper'
MODEL_BACKEND = "faster-whisper"

# Import model (lazy import so user can choose)
if MODEL_BACKEND == "faster-whisper":
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        raise RuntimeError("Install faster-whisper or change MODEL_BACKEND") from e
else:
    pass


# CONFIG
SAMPLE_RATE = 16000            # model expected sample rate
CHANNELS = 1
CONTEXT_SECONDS = 15.0         # fixed size moving window (change as needed)
STEP_SECONDS = 3.0             # how often to run inference (controls latency)
LANG = None                    # None = auto-detect; set to "en" for english
MODEL_SIZE = "turbo"           # or "medium", "small" (faster-whisper sizes)
CHUNK_SIZE = SAMPLE_RATE * STEP_SECONDS # 30ms chunks for VAD

# instantiate model (faster-whisper example)
if MODEL_BACKEND == "faster-whisper":
    model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="int8_float16")
else:
    pass


class RollingBuffer:
    def __init__(self, context_seconds: float, sample_rate: int):
        self.sample_rate = sample_rate
        self.context_seconds = context_seconds
        self.max_samples = int(context_seconds * sample_rate)
        self.buffer = np.zeros((0,), dtype=np.int16)  # store int16 PCM

    def append(self, pcm16: np.ndarray):
        """Append new int16 PCM chunk; keep only last max_samples."""
        if pcm16.dtype != np.int16:
            raise ValueError("pcm16 must be int16")
        self.buffer = np.concatenate((self.buffer, pcm16), axis=0)
        if len(self.buffer) > self.max_samples:
            # keep last max_samples
            self.buffer = self.buffer[-self.max_samples :]

    def get_wav_bytes(self) -> bytes:
        """Return the current buffer as WAV bytes (16kHz mono)."""
        # write to bytes using soundfile
        bio = io.BytesIO()
        sf.write(bio, self.buffer.astype(np.int16), self.sample_rate, format="WAV", subtype="PCM_16")
        bio.seek(0)
        return bio.read()

    # unused but may be useful
    def get_samples(self) -> np.ndarray:
        return self.buffer.copy()

    # unused but may be useful
    def get_duration(self) -> float:
        return len(self.buffer) / self.sample_rate


def pcm_float_to_int16(float_pcm: np.ndarray) -> np.ndarray:
    """Convert float PCM in range [-1,1] to int16."""
    clipped = np.clip(float_pcm, -1.0, 1.0)
    return (clipped * 32767).astype(np.int16)


def diff_new_tail(prev_text: str, new_text: str) -> tuple[str, int]:
    """
    Find the longest matching block between prev_text and new_text using SequenceMatcher.
    Return a tuple (unmatched_new, replace_count):
      - unmatched_new: the parts of new_text that are NOT part of the longest match
                       (concatenation of prefix and suffix around the longest match), trimmed.
      - replace_count: if longest match length < len(prev_text), return len(prev_text) - match_length,
                       otherwise 0.
    """
    s = SequenceMatcher(None, prev_text, new_text)
    match = s.find_longest_match(0, len(prev_text), 0, len(new_text))
    # parts of new_text not covered by the longest match (prefix + suffix)
    unmatched_new = (new_text[: match.b] + new_text[match.b + match.size :]).strip()
    replace_count = 0 if match.size >= len(prev_text) else (len(prev_text) - match.size)
    return unmatched_new, replace_count


class StreamingASR:
    def __init__(self,
                 model,
                 buffer: RollingBuffer,
                 step_seconds: float,
                 emit_callback: Callable[[str], None],
                 sample_rate: int = SAMPLE_RATE,
                 lang: Optional[str] = LANG):
        self.model = model
        self.buffer = buffer
        self.step_seconds = step_seconds
        self.emit_cb = emit_callback
        self.sample_rate = sample_rate
        self.lang = lang

        self.vad_model = load_silero_vad()

        self._prev_full_transcript = ""  # last transcription for full buffer
        self._emit_full_text = ""  # for debugging
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """Start background inference loop if desired."""
        self._running = True
        asyncio.create_task(self._periodic_infer())

    async def stop(self):
        self._running = False

    async def _periodic_infer(self):
        while self._running:
            await self.infer_once()
            await asyncio.sleep(self.step_seconds)

    async def infer_once(self):
        # ensure we do only one inference at a time
        async with self._lock:
            wav_bytes = self.buffer.get_wav_bytes()
            if len(wav_bytes) == 0:
                return
            # Run transcription on wav bytes
            if MODEL_BACKEND == "faster-whisper":
                segments, info = self.model.transcribe(io.BytesIO(wav_bytes), beam_size=5, language=self.lang, vad_filter=False)
                # assemble text from segments
                full_text = "".join([seg.text.strip() for seg in segments]).strip()
            else:
                pass

            # compute the delta vs previous full transcription and emit only the new tail
            delta, off = diff_new_tail(self._prev_full_transcript, full_text)
            if delta:
                self.emit_cb(self, delta, off)
                print(off)
            # update previous
            self._prev_full_transcript = full_text


# Example emit callback (replace with websocket send)
def emit_print(asr: StreamingASR, text: str, offset: int):
    print(f"[EMIT] '{text}'")
    # If offset > 0, remove that many characters from the end
    if offset > 0:
        asr._emit_full_text = asr._emit_full_text[:-offset]
    asr._emit_full_text += text
    print(f"[FULL] '{asr._emit_full_text}'")


# Example usage: simulate incoming audio chunks (e.g., produced by microphone callback)
async def simulate_microphone_stream(asr: StreamingASR):
    """
    This simulates incoming audio frames: instead of a real mic, it reads chunks from a WAV file.
    Replace this with actual microphone capture (sounddevice or pyaudio) in production.
    """
    import soundfile as sf
    # replace with path to a test long wav file sampled at SAMPLE_RATE
    TEST_WAV = "asset/sample4_zh.ogg"
    data, sr = sf.read(TEST_WAV, dtype="int16")
    if sr != SAMPLE_RATE:
        # resample using pydub
        audio = AudioSegment(data.tobytes(), frame_rate=sr, sample_width=2, channels=1)
        audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1)
        raw = np.frombuffer(audio.raw_data, dtype=np.int16)
    else:
        raw = data if data.ndim == 1 else data[:, 0]
    chunk_samples = int(STEP_SECONDS * SAMPLE_RATE)
    idx = 0
    while idx < len(raw):
        # TODO: stop inferring
        chunk = raw[idx: idx + chunk_samples]
        idx += chunk_samples
        asr.buffer.append(chunk.astype(np.int16))
        # we can call infer immediately or rely on periodic loop
        await asr.infer_once()
        await asyncio.sleep(STEP_SECONDS * 0.8)  # simulate realtime arrival

async def system_audio_stream(asr: StreamingASR):
    loopback_name = 'Monitor of Starship/Matisse HD Audio Controller Analog Stereo'
    speaker = sc.get_microphone(loopback_name, include_loopback=True)        
    volume_gain = 42.0 # the audio coming from the loopback device is unusually quiet we need it amplified for the vad
    if speaker:
        with speaker.recorder(samplerate=asr.sample_rate, channels=1) as mic:
            print("LISTENING...")
            while True:
                block = (mic.record(numframes = CHUNK_SIZE) * volume_gain).flatten()
                speech_detected = len(get_speech_timestamps(block, asr.vad_model, sampling_rate=asr.sample_rate))
                if not speech_detected:
                    continue # don't add to the buffer if the entire second long chunk is just silence
                asr.buffer.append(pcm_float_to_int16(block))
                await asr.infer_once()
                #print(block.shape, block.dtype)


async def main():
    rb = RollingBuffer(CONTEXT_SECONDS, SAMPLE_RATE)
    asr = StreamingASR(model=model, buffer=rb, step_seconds=STEP_SECONDS, emit_callback=emit_print)
    #await asr.start()
    # If you have a real stream, feed pcm chunks to rb.append(...) from your capture callback.
    # Here we simulate:
    #await simulate_microphone_stream(asr)
    await system_audio_stream(asr)
    #await asr.stop()

if __name__ == "__main__":
    asyncio.run(main())
