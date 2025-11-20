# pip install jieba simhash
#import jieba
import spacy_pkuseg
from simhash import Simhash


# 1. Heuristic: punctuation-based continuation score
def punctuation_score(line):
    if not line: return 0
    last = line[-1]

    # These punctuation marks strongly indicate continuation
    mid_clause = "，、：；（《“‘"
    if last in mid_clause:
        return 1.0

    # These indicate sentence boundary
    end_clause = "。！？"
    if last in end_clause:
        return -0.5

    return 0.0


# 2. Heuristic: word-split detection using jieba
#    Example:
#        L1: "这是一个问"
#        L2: "题，我们必须"
#    "问题" is split → strong continuation
seg = spacy_pkuseg.pkuseg()           # 以默认配置加载模型
def word_split_score(line1, line2):
    if not line1 or not line2: return 0

    # take last 3 chars of L1 and first 3 of L2
    window = line1[-3:] + line2[:3]
    words = list(seg.cut(window))

    # if a long word spans the boundary, we count that
    score = 0.0
    for w in words:
        # word appears across line boundary
        if len(w) >= 2 and w in window and w not in line1 and w not in line2:
            score += 1.0

    return min(score, 1.0)


# 3. Tiny semantic similarity using Simhash
def semantic_similarity(line1, line2):
    if not line1 or not line2: return 0.0

    h1 = Simhash(line1).value
    h2 = Simhash(line2).value

    # Hamming distance normalized
    max_bits = 64
    dist = bin(h1 ^ h2).count("1")
    return 1 - dist / max_bits  # range 0–1


# 4. Paragraph-start cue detection
PARA_START_CUES = [
    "首先", "其次", "然而", "此外", "另外",
    "总结来说", "综上所述", "总之", "对于", "关于"
]

def paragraph_start_signal(line):
    return 1.0 if any(line.startswith(c) for c in PARA_START_CUES) else 0.0


def continuation_score(L1, L2):
    return (
        0.5 * punctuation_score(L1) +
        0.7 * word_split_score(L1, L2) +
        0.4 * semantic_similarity(L1, L2) -
        1.0 * paragraph_start_signal(L2)
    )


def group_lines(lines, threshold=0.2):
    groups = []
    current = [lines[0]]

    for i in range(len(lines) - 1):
        L1, L2 = lines[i], lines[i+1]
        score = continuation_score(L1, L2)
        print(f"Score({i}->{i+1}) = {score:.3f}")

        if score >= threshold:
            current.append(L2)
        else:
            groups.append(current)
            current = [L2]

    groups.append(current)
    return groups


if __name__ == "__main__":
    lines = [
        "这个问题非常复杂，我们必须认真考",
        "虑它的影响。",
        "此外，我们还需要考虑相关政策的变动。",
        "总结来说，未来的发展仍然不确定。"
    ]

    lines2 = [
        "置顶",
        "大家好，我是食草龙的导演。第二季终于顺利更新！这次终于实现了中日同播，日语版也",
        "同时上线了！",
        "第二季会聚焦于玲子和食草龙在亚斯嘉王国的一系列故事，剧情会更加紧凑和精彩。希望喜欢的",
        "观众多多支持，用支持您喜欢的up的方式，玩了命的三连！"
    ]

    lines3 = [
        "简介：与世无争只想过平静生活的食草龙，遇上了中二少女玲子。由于无论它怎么好言",
        "相劝都无法劝退一心向死的玲子，无计可施的它只能编造谎言，好让玲子活下去。",
        "展开"
    ]

    groups = group_lines(lines2)

    print("\nParagraph groups:")
    for g in groups:
        print("----")
        for line in g:
            print(line)
