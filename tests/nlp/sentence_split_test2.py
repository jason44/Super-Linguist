import jieba
import jieba.posseg as pseg

# jieba uses a dictionary approach while pkuseg uses a small nlp model 
# so jieba is able to recognize idioms (given that it is in the dicitonary)
# but pkuseg is much better at recognizing nouns because it does not rely on 
# a dictionary which is all but certain to be missing contemporary nouns.

#jieba.enable_paddle()
words= pseg.cut("我看到那个骑自行车的小女孩了")
#words= pseg.cut("研究生命的起源。", use_paddle=True)
result = [(w.word, w.flag) for w in words]
print(result)
