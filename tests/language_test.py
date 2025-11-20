# pip install transformers sentence-transformers torch
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, BertTokenizer, BertForMaskedLM
from sentence_transformers import SentenceTransformer


# -----------------------------------------------------
# Load modern Chinese LLM
# -----------------------------------------------------
#qwen_model_name = "Qwen/Qwen2.5-0.5B-Instruct"
qwen_model_name = "Qwen/Qwen3-0.6B"

qwen_tokenizer = AutoTokenizer.from_pretrained(qwen_model_name)
qwen_model = AutoModelForCausalLM.from_pretrained(
    qwen_model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)
qwen_model.eval()


# -----------------------------------------------------
# Load BERT for fragment detection
# -----------------------------------------------------
bert_model_name = "bert-base-chinese"
bert_tokenizer = BertTokenizer.from_pretrained(bert_model_name)
bert_model = BertForMaskedLM.from_pretrained(bert_model_name)
bert_model.eval()


# -----------------------------------------------------
# Load Chinese Sentence-BERT for semantic similarity
# -----------------------------------------------------
embedder = SentenceTransformer("shibing624/text2vec-base-chinese")


# -----------------------------------------------------
# Utility: Qwen continuation score
# -----------------------------------------------------
def qwen_continuation_score(line1, line2):
    """
    Compute LM continuation score:
    S = logprob(line1 + line2) - logprob(line1)
    """
    def logprob(text):
        inputs = qwen_tokenizer(text, return_tensors="pt").to(qwen_model.device)
        with torch.no_grad():
            out = qwen_model(**inputs, labels=inputs["input_ids"])
        return -out.loss.item()  # negative loss = logprob up to a constant

    return logprob(line1 + line2) - logprob(line1)


# -----------------------------------------------------
# Fragment detection with BERT
# -----------------------------------------------------
def bert_fragment_score(line):
    if len(line) < 2:
        return 0.0

    masked = line[:-1] + "[MASK]"
    inputs = bert_tokenizer(masked, return_tensors="pt")
    mask_idx = (inputs.input_ids == bert_tokenizer.mask_token_id).nonzero(as_tuple=True)[1]

    with torch.no_grad():
        outputs = bert_model(**inputs)

    logits = outputs.logits[0, mask_idx, :]
    probs = logits.softmax(dim=-1)

    true_id = bert_tokenizer.convert_tokens_to_ids(line[-1])
    return probs[0, true_id].item()


# -----------------------------------------------------
# Next-character prediction using Qwen
# -----------------------------------------------------
def next_char_prediction_score(line1, line2, top_k=20):
    context = line1[-20:]  # last N chars
    inputs = qwen_tokenizer(context, return_tensors="pt").to(qwen_model.device)

    with torch.no_grad():
        outputs = qwen_model(**inputs)

    last_logits = outputs.logits[0, -1]
    topk_ids = torch.topk(last_logits, k=top_k).indices.tolist()
    preds = qwen_tokenizer.convert_ids_to_tokens(topk_ids)

    first_char = line2[0]
    return 1.0 if first_char in preds else 0.0


# -----------------------------------------------------
# Embedding similarity
# -----------------------------------------------------
def embedding_similarity(a, b):
    e1 = embedder.encode([a])[0]
    e2 = embedder.encode([b])[0]
    return float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2)))


# -----------------------------------------------------
# Combine into final score
# -----------------------------------------------------
def continuation_score(L1, L2):
    A = qwen_continuation_score(L1, L2)
    B = bert_fragment_score(L1)
    C = next_char_prediction_score(L1, L2)
    D = embedding_similarity(L1, L2)

    return (
        0.40 * A +
        0.20 * B +
        0.20 * C +
        0.15 * D
    )


# -----------------------------------------------------
# Group lines into paragraphs
# -----------------------------------------------------
def group_lines(lines, threshold=0.0):
    groups = []
    cur = [lines[0]]

    for i in range(len(lines) - 1):
        L1, L2 = lines[i], lines[i+1]
        score = continuation_score(L1, L2)
        print(f"Score({i}->{i+1}) = {score:.4f}")

        if score >= threshold:
            cur.append(L2)
        else:
            groups.append(cur)
            cur = [L2]

    groups.append(cur)
    return groups


# -----------------------------------------------------
# Example
# -----------------------------------------------------
if __name__ == "__main__":
    lines = [
        "这个问题非常复杂，我们必须认真考",
        "虑它的影响。",
        "此外，我们还需要考虑相关政策的变动。",
        "总结来说，未来的发展仍然不确定。"
    ]

    groups = group_lines(lines)

    print("\nParagraph groups:")
    for g in groups:
        print("-----")
        for line in g:
            print(line)
