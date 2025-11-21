import os
import argparse
import sqlite3

# conda cosyvoice
# uv --project lib/index-tts run utils/generate_spoken.py --tts_type index --output_dir asset/spoken_output --update_db

# --- Configuration ---
DB_PATH = "asset/chinese.db" # Path to your SQLite database
TABLE_NAME = "hsk_inclusive"
OUTPUT_DIR = "spoken_output"   # Folder to save TTS files
LANGUAGE = "zh"             # Language for TTS

parser = argparse.ArgumentParser(description='Generate speech')
parser.add_argument('--tts_type', type=str, choices=['gTTS', 'index'], default='gTTS', help='Type of text-to-speech engine (default: gTTS)')
parser.add_argument('--output_dir', action='store', default=OUTPUT_DIR, help='Output directory for TTS files' )
parser.add_argument('--update_db', action='store_true', default=False)
args = parser.parse_args()

import sys
sys.path.append("lib/index-tts")
from indextts.infer_v2 import IndexTTS2
tts = IndexTTS2(
    cfg_path="lib/index-tts/checkpoints/config.yaml", 
    model_dir="lib/index-tts/checkpoints", 
    use_fp16=True, 
    use_cuda_kernel=False, 
    use_deepspeed=False
)

def main():
    if args.tts_type == 'gTTS':
        from gtts import gTTS
    generate()


def generate_speech(text, tts_type, fp):
    if tts_type == 'gTTS':
        _tts = gTTS(text=text, lang=LANGUAGE)
        _tts.save(fp)
    else:
        tts.infer(
            spk_audio_prompt='asset/sample1_zh.ogg', 
            emo_vector=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], # [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
            use_random=False, # no random emo_vector
            text=text, 
            output_path=fp, 
            stream_return=False,
            verbose=False,
            top_p=0.8,
            top_k=20,
            temperature=0.1,
        )
    print(f"🔊 Generated TTS for '{text}' -> {fp}")

def generate():
    # --- Setup ---
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Connect to database ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Ensure 'spoken' column exists ---
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    columns = [col[1] for col in cursor.fetchall()]

    if "spoken" not in columns:
        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN spoken TEXT")
        conn.commit()
        print("Added missing 'spoken' column to the table.")

    # --- Fetch entries ---
    # index-tts doesn't fully support all of the pinyin tonal marks, so we can't reliably use numeric here
    # just hope that index-tts produces the right reading of the word. 
    cursor.execute(f"SELECT rowid, simple FROM {TABLE_NAME}") 
    #cursor.execute(f"SELECT rowid, numeric FROM {TABLE_NAME}")
    rows = cursor.fetchall()

    for rowid, word in rows[8000:]:
        if not word: continue

        fp = os.path.join(args.output_dir, f"{word}.ogg")
        generate_speech(word, args.tts_type, fp)

        if args.update_db:
            cursor.execute(
                f"UPDATE {TABLE_NAME} SET spoken = ? WHERE rowid = ?",
                (fp, rowid)
            )
        if rowid % 50 == 0: # commit every 50 since we have a big dataset to process
            print(f"Processed {rowid} entries... you can now safely stop the script if needed.\n------------------------------------------\n")
            conn.commit()

    conn.commit()
    conn.close()
    print("✅ All done!")


if __name__ == "__main__":
    main()