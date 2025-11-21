# pip install spacy-pkuseg
import spacy_pkuseg

seg = spacy_pkuseg.pkuseg(postag=True)           # 以默认配置加载模型
result = seg.cut("北京大学的学生在人工智能领域取得了显著的成果")
print(result)
