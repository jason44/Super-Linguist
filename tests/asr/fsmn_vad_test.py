from funasr import AutoModel

chunk_size = 600 # ms
model = AutoModel(model="fsmn-vad")

import soundfile

wav_file = f"assets/sample1_zh.ogg"
speech, sample_rate = soundfile.read(wav_file)

if sample_rate != 16000:
    import librosa
    speech = librosa.resample(speech, orig_sr=sample_rate, target_sr=16000)
    sample_rate = 16000

chunk_stride = int(chunk_size * sample_rate / 1000)

cache = {}
total_chunk_num = int(len((speech)-1)/chunk_stride+1)
for i in range(total_chunk_num):
    speech_chunk = speech[i*chunk_stride:(i+1)*chunk_stride]
    is_final = i == total_chunk_num - 1
    res = model.generate(input=speech_chunk, cache=cache, is_final=is_final, chunk_size=chunk_size)
    if len(res[0]["value"]):
        print(res) # there is voice activity
