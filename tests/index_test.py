# uv --project lib/index-tts run test/index_test.py  <--- from OpenLinguist directory
import sys
sys.path.append("lib/index-tts")

from indextts.infer_v2 import IndexTTS2
tts = IndexTTS2(cfg_path="lib/index-tts/checkpoints/config.yaml", model_dir="lib/index-tts/checkpoints", use_fp16=True, use_cuda_kernel=False, use_deepspeed=False)
#text = "酒楼丧尽天良，开始借机竞拍房间，哎，一群蠢货。"
text = "ai4xin1"
tts.infer(
    spk_audio_prompt='asset/sample1_zh.ogg', 
    emo_vector=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], # [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
    use_random=False, # no random emo_vector
    text=text, 
    output_path="gen.wav", 
    stream_return=False,
    verbose=True,
    top_p=0.8,
    top_k=20,
    temperature=0.1,
)

