## using VADIterator class
from silero_vad import (load_silero_vad,
                        read_audio,
                        get_speech_timestamps,
                        save_audio,
                        VADIterator,
                        collect_chunks)

from pprint import pprint
import os, wave



SAMPLING_RATE = 16000

model = load_silero_vad(opset_version=16)
vad_iterator = VADIterator(model, sampling_rate=SAMPLING_RATE)
#wav = read_audio(f'asset/sample4_zh.ogg', sampling_rate=SAMPLING_RATE)
wav = read_audio(f'asset/silence.wav', sampling_rate=SAMPLING_RATE)


def stream_example():
    window_size_samples = 512 if SAMPLING_RATE == 16000 else 256
    for i in range(0, len(wav), window_size_samples):
        chunk = wav[i: i+ window_size_samples]
        if len(chunk) < window_size_samples:
            break
        speech_dict = vad_iterator(chunk, return_seconds=True)
        if speech_dict:
            print(speech_dict, end=' ')
    vad_iterator.reset_states() # reset model states after each audio

def full_audio_example():
    predicts = model.audio_forward(wav, sr=SAMPLING_RATE)
    print(predicts)


def full_timestamps():
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=SAMPLING_RATE)
    pprint(speech_timestamps)

def save_silence_wav(duration_seconds=1.0, path='asset/silence.wav'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    num_samples = int(SAMPLING_RATE * float(duration_seconds))
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLING_RATE)
        # 16-bit little-endian zeros for silence
        wf.writeframes(b'\x00\x00' * num_samples)
    print(f"Saved {duration_seconds}s of silence to {path}")


full_audio_example()
#save_silence_wav(duration_seconds=6.0, path='asset/silence.wav')