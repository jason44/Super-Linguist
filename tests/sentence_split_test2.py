import jieba.posseg as pseg

words= pseg.cut("龙蛇混杂")
result = [(w.word, w.flag) for w in words]
print(result)
