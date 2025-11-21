import sys
sys.path.append('lib/CosyVoice')
sys.path.append('lib/CosyVoice/third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio

cosyvoice = CosyVoice2('lib/CosyVoice/pretrained_models/CosyVoice2-0.5B', load_jit=False, load_trt=False, load_vllm=False, fp16=False)

prompt_speech_16k = load_wav('assets/sample1_zh.ogg', 16000)
#for i, j in enumerate(cosyvoice.inference_zero_shot('收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。', 'You have the worst luck running into me!', prompt_speech_16k, stream=False)):
#for i, j in enumerate(cosyvoice.inference_zero_shot("Beat it loser! You got what you deserved. Let me say it so you'll understand: 滚开，废物！你活该！", 'You have the worst luck running into me!', prompt_speech_16k, stream=False)):
#for i, j in enumerate(cosyvoice.inference_cross_lingual("滚开，废物！你活该！", prompt_speech_16k, stream=False)):
#for i, j in enumerate(cosyvoice.inference_instruct2("滚开，废物！你活该！", "汉语普通话发音",prompt_speech_16k, stream=False)):
#for i, j in enumerate(cosyvoice.inference_zero_shot("滚开，废物！你活该！", ruan_mei_text,prompt_speech_16k, stream=False)):
#for i, j in enumerate(cosyvoice.inference_instruct2("你做出了多么明智的决定啊！我为你感到骄傲。", "发音要慢且清晰", prompt_speech_16k, stream=False, speed=0.9)):
for i, j in enumerate(cosyvoice.inference_zero_shot("你做出了多么明智的决定啊！我为你感到骄傲。", "无须行礼，此身虽然尊贵殊胜，不过此般前来，是想要做些微服游历民间的事。我看上了你的身手，现在你就是我的御侧保镖了。不用担心，遇到危险，我会出手的。", prompt_speech_16k, stream=False, speed=0.9)):
    torchaudio.save('zero_shot_{}.wav'.format(i), j['tts_speech'], cosyvoice.sample_rate)

# the only punctuation that should be used are periods and commas, anything else may cause errors in the llm.

