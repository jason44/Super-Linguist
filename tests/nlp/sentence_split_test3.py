import os
import hanlp
from typing import List, Tuple


os.environ['HANLP_VERBOSE'] = '0'

# --- HanLP Model Initialization ---
# The Multi-Task Learning (MTL) model is loaded once at the start.
# This model performs Tokenization, POS Tagging, NER, and more,
# using a single, high-accuracy neural network (ELECTRA-based).
# We load it outside the function so the model isn't reloaded on every call.
try:
    print("Loading HanLP Multi-Task Learning Model for CWS, POS, and Pinyin...")
    # Using a comprehensive pre-trained model for robust analysis
    tagger = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading HanLP model. Please ensure you have run 'pip install hanlp'. Details: {e}")
    tagger = None # Ensure the program doesn't crash if loading fails

def segment_and_tag_chinese(text: str) -> List[Tuple[str, str, str]]:
    """
    Performs Chinese Word Segmentation (CWS), Part-of-Speech (POS) tagging,
    and Pinyin conversion on a given Chinese text using a HanLP neural 
    Multi-Task Learning model.

    Args:
        text: The Chinese sentence or paragraph to process.

    Returns:
        A list of tuples, where each tuple is (word, pos_tag, pinyin).
        Returns an empty list if the HanLP model failed to load.
    """
    if not tagger:
        return []

    # The MTL model is called as a function. 
    # We specify the tasks we want to ensure consistent output keys.
    try:
        # Added 'pinyin' to the tasks list
        result = tagger(text, tasks=['tok/fine', 'pos/ctb'])
        
        # The result is a dictionary. We extract the tokens, tags, and pinyins.
        tokens = result['tok/fine']
        tags = result['pos/ctb']
        pinyins = result['pinyin']
        
        # Combine the segmented words, their corresponding POS tags, and Pinyin
        tagged_words = list(zip(tokens, tags, pinyins))
        
        return tagged_words

    except Exception as e:
        print(f"An error occurred during processing: {e}")
        return []


def split_to_words_many(ps, tasks=['tok/fine', 'pos/ctb']):
    try:
        results = tagger(ps, tasks=tasks)
        return [list(zip(tokens, tags)) for tokens, tags in zip(results['tok/fine'], results['pos/ctb'])]
    except Exception as e:
        print(f"An error occurred during text segmentation: {e}")
        return []

# --- Demonstration ---
if __name__ == "__main__":
    if tagger:
        sentence = "北京大学的学生在人工智能领域取得了显著的成果。"
        sentence2 = "离开佩纳科尼后，他们的下一站是安弗勒斯。"
        print(f"\n--- Processing Sentence ---\nInput: {sentence}\n")

        tagged_output = split_to_words_many([sentence, sentence2])
        for out in tagged_output:
            print(out)
    else:
        print("\nCould not run the demonstration as the HanLP model failed to load.")