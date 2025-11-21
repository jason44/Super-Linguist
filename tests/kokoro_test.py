from kokoro import KPipeline
import soundfile as sf
import torch
pipeline = KPipeline(lang_code='z')
text = '''只是雨滴有什么麻烦的。这还没有打雷呢'''

generator = pipeline(
    text, voice='zf_xiaoxiao', # <= change voice here
    speed=0.8, split_pattern=r'\n+'
)

for i, (gs, ps, audio) in enumerate(generator):
    print(i)  # i => index
    print(gs) # gs => graphemes/text
    print(ps) # ps => phonemes
    sf.write(f'{text}.wav', audio, 24000) # save each audio file