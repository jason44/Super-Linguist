# pip install spacy-pkuseg
import spacy_pkuseg

seg = spacy_pkuseg.pkuseg(postag=True)           # 以默认配置加载模型
result = seg.cut("这个问题非常复杂，我们必须认真考虑它的影响。")
print(result)