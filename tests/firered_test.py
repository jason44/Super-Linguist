import sys
sys.path.append("lib/FireRedASR")

from fireredasr.models.fireredasr import FireRedAsr

batch_uttid = ["BAC009S0764W0121"]
batch_wav_path = ["asset/sample4_zh.ogg"]

# FireRedASR-AED
model = FireRedAsr.from_pretrained("aed", "pretrained_models/FireRedASR-AED-L")
results = model.transcribe(
    batch_uttid,
    batch_wav_path,
    {
        "use_gpu": 1,
        "beam_size": 3,
        "nbest": 1,
        "decode_max_len": 0,
        "softmax_smoothing": 1.25,
        "aed_length_penalty": 0.6,
        "eos_penalty": 1.0
    }
)
print(results)