# pip install spacy-pkuseg
import spacy_pkuseg

seg = spacy_pkuseg.pkuseg(postag=True)           # 以默认配置加载模型
result = seg.cut("龙蛇混杂")
print(result)
