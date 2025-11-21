from simhash import Simhash
import pypinyin
import jieba
import hanlp


# --- Text-segmentation based on on two different approaches
# Jieba uses a dictionary-based model which is faster but less accurate at segmenting.
# Hanlp uses a more accurate but slower transformer model.
# Pkuseg is inbetween the two in accuracy-speed tradeoff
def split_to_words_fast(p):
    try:
        return jieba.cut(p)
    except Exception as e:
        print(f"An error occurred during text segmentation: {e}")
        return []

try:
    print("Loading HanLP Multi-Task Learning Model for CWS and POS...")
    # ELECTRA model is much faster than the BERT model
    tagger = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH, device=0)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading HanLP model: {e}")

def split_to_words(p, tasks=['tok/fine', 'pos/ctb']):
    try:
        result = tagger(p, tasks)
        return list(zip(result['tok/fine'], result['pos/ctb']))
    except Exception as e:
        print(f"An error occurred during text segmentation: {e}")
        return []
    
def batch_split_to_words(ps, tasks=['tok/fine', 'pos/ctb']):
    try:
        results = tagger(ps, tasks=tasks)
        return [list(zip(tokens, tags)) for tokens, tags in zip(results['tok/fine'], results['pos/ctb'])]
    except Exception as e:
        print(f"An error occurred during text segmentation: {e}")
        return []


# --- Line grouping: Combining lines that are likely to be part of the same thought/sentence

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
def word_split_score(line1, line2):
    if not line1 or not line2: return 0

    # take last 3 chars of L1 and first 3 of L2
    window = line1[-3:] + line2[:3]
    words = list(split_to_words_fast(window))

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

def bounding_box(box1, box2):
    return [min(box1[0], box2[0]), min(box1[1], box2[1]), max(box1[2], box2[2]), max(box1[3], box2[3])]

# group lines that are part of the same thought/sentence/paragraph
def group_lines(data, threshold=0.2):
    lines = data['texts']
    boxes = data['boxes']

    groups = [] # list of strings
    group_boxes = [] # list of coordinates
    current = lines[0]
    current_box = boxes[0]

    for i in range(len(lines) - 1):
        L1, L2 = lines[i], lines[i+1]
        B1, B2 = boxes[i], boxes[i+1]
        score = continuation_score(L1, L2)
        #print(f"Score({i}->{i+1}) = {score:.3f}")

        if score >= threshold:
            current += L2
            current_box = bounding_box(B1, B2)
        else:
            groups.append(current)
            group_boxes.append(current_box)
            current = L2
            current_box = B2

    groups.append(current)
    group_boxes.append(current_box)
    return {'texts': groups, 'boxes': group_boxes}