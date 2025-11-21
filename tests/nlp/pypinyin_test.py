from pypinyin import pinyin, lazy_pinyin, Style


print(
    pinyin('佩纳科尼', heteronym=True)
)
print(
    lazy_pinyin('佩纳科尼', v_to_u=True)
)

