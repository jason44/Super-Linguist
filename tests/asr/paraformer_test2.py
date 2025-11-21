from funasr import AutoModel
# paraformer-zh is a multi-functional asr model
# use vad, punc, spk or not as you need
model = AutoModel(model="paraformer-zh", 
                  #punc_model="ct-punc"
)
res = model.generate(input=f"assets/sample1_zh.wav")
print(res)
