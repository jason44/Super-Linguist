"""
conda: funasr
"""

# FasterWhisper requires cuDNN and cuBLAS (install from Nvidia website)
# TODO: test how well this performs on audio with a lot of noise eg: background music and sfx. If the performance is lackluster, then consider adding a neural voice isolator step before ASR.
# TODO: Get inference working on a separate thread so that inference can happen in shorter intervals than VAD silence removal 
# however if inference step is shorter than VAD step, then if vad does detect the 

import torch
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

from funasr import AutoModel
model = AutoModel(model="paraformer-zh", 
                  #punc_model="ct-punc", 
                  disable_update=True
)

# CONFIG
SAMPLE_RATE = 16000            # model expected sample rate
CHANNELS = 1
CONTEXT_SECONDS = 15.0         # fixed size moving window (change as needed)
STEP_SECONDS = 1.0             # how often to run inference (controls latency)
CHUNK_SIZE = SAMPLE_RATE * STEP_SECONDS


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
    
    def clear(self):
        """Clear the buffer."""
        self.buffer = np.zeros((0,), dtype=np.int16)

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


class StreamingASR:
    def __init__(self,
                 model,
                 buffer: RollingBuffer,
                 step_seconds: float,
                 emit_callback: Callable[[str], None],
                 sample_rate: int = SAMPLE_RATE,
                 lang: Optional[str] = None):
        self.model = model
        self.buffer = buffer
        self.step_seconds = step_seconds
        self.emit_cb = emit_callback
        self.sample_rate = sample_rate
        self.lang = lang

        self.vad_model = load_silero_vad()

        self.full_text = ""
        self.text_outputs = []
        self._lock = asyncio.Lock()

    async def infer_once(self):
        # ensure we do only one inference at a time
        async with self._lock:
            wav_bytes = self.buffer.get_wav_bytes()
            if len(wav_bytes) == 0:
                return
            # Run transcription on wav bytes
            res = self.model.generate(input=wav_bytes)
            # assemble text from segments
            self.full_text = res[0]['text'].replace(' ', '')
            self.emit_cb(self)


def emit_print(asr: StreamingASR):
    print(f"[EMIT] '{asr.full_text}'")
    print(f"[OUTPUTS] {asr.text_outputs} + {asr.full_text}")
    print(f"[CONCAT_OUTPUTS] '{' '.join(asr.text_outputs) + ' ' +  asr.full_text}'")


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
                #speech_detected = len(get_speech_timestamps(block, asr.vad_model, sampling_rate=asr.sample_rate))
                THRESHOLD = 0.98
                speech_detected = bool(asr.vad_model.audio_forward(torch.from_numpy(block).float(), sr=SAMPLE_RATE).abs().max() > THRESHOLD)
                if not speech_detected:
                    asr.buffer.clear() # this will cause inference issues for smaller STEP_SECONDS values because small pauses in sentences will trigger a loss of context
                    # clearing the cache only makes sense if the vad only cuts out silences longer than like 1 or 2 seconds
                    # but if we don't clear the cache then we can't detect sentence boundaries properly
                    if asr.full_text:
                        asr.text_outputs.append(asr.full_text)
                        asr.full_text = ""
                    continue # don't add to the buffer if the entire second long chunk is just silence
                asr.buffer.append(pcm_float_to_int16(block))
                await asr.infer_once()
                #print(block.shape, block.dtype)


async def main():
    rb = RollingBuffer(CONTEXT_SECONDS, SAMPLE_RATE)
    asr = StreamingASR(model=model, buffer=rb, step_seconds=STEP_SECONDS, emit_callback=emit_print)
    await system_audio_stream(asr)

if __name__ == "__main__":
    asyncio.run(main())
