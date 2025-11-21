from funasr import AutoModel

"""
[0,10,5] indicates that the real-time display granularity is 10*60ms=600ms, 
and the lookahead information is 5*60ms=300ms. So each inference input is 600ms
16kHz*60ms=960ms is the chunk stride
"""

chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
encoder_chunk_look_back = 4 #number of chunks to lookback for encoder self-attention
decoder_chunk_look_back = 1 #number of encoder chunks to lookback for decoder cross-attention

model = AutoModel(model="paraformer-zh-streaming")

import soundfile
import librosa
import os

wav_file = "assets/sample1_zh.ogg"
speech, sample_rate = soundfile.read(wav_file)

if sample_rate != 16000:
    speech = librosa.resample(speech, orig_sr=sample_rate, target_sr=16000)
    sample_rate = 16000

chunk_stride = chunk_size[1] * 960 # 600ms

cache = {}
output = ""
total_chunk_num = int(len((speech)-1)/chunk_stride+1)
for i in range(total_chunk_num):
    speech_chunk = speech[i*chunk_stride:(i+1)*chunk_stride]
    print(speech_chunk.shape, speech.shape)
    is_final = i == total_chunk_num - 1
    res = model.generate(input=speech_chunk, cache=cache, is_final=is_final, chunk_size=chunk_size, encoder_chunk_look_back=encoder_chunk_look_back, decoder_chunk_look_back=decoder_chunk_look_back)
    output += res[0]['text']
    print(res)

print(output)
