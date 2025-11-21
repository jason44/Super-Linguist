import re
import sqlite3
from pypinyin.contrib.tone_convert import to_tone3

class CreateHSK:
    def __init__(self, id, path='asset/hsk_dict/chinese.db', table='hsk_inclusive'):
        self.id = id
        self.path = path
        self.table = table
        self.create_freq_map()
        self.create_numeric_map()

        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor() 
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hsk_id INTEGER NOT NULL, 
                frequency INTEGER,
                simple TEXT NOT NULL,
                traditional TEXT NOT NULL,
                pinyin TEXT NOT NULL,
                numeric TEXT NOT NULL,
                meaning TEXT NOT NULL,
                classifier TEXT
            );
        """)

    def create_freq_map(self):
        self.freq_map = {}
        f = open(f"asset/hsk_dict/frequencies/Final-Merged-{self.id}.txt")
        for line in f.readlines():
            word, freq = line.split()
            self.freq_map[word] = freq

    def create_numeric_map(self):
        self.numeric_map = {}
        f = open(f"asset/hsk_dict/pinyin/HSK{self.id}.txt")
        for line in f.readlines():
            word, _, numeric = line.split('\t', 2)
            word = word.strip('\ufeff')  # I don't know why
            self.numeric_map[word] = numeric.strip(' \n')

    def append_to_db(self):
        f = open(f"asset/hsk_dict/meanings/HSK {self.id} with clear meaning.txt")
        words = []
        for line in f.readlines():
            trad, simple, pinyin, meaning = line.split(',', 3)
            #meaning = meaning.strip('"\n')

            pattern = r'm\.\[([A-Za-z_]+)\]'
            meaning = re.sub(pattern, r'As a measure word describing: \1', meaning)

            # replace some shorthands and move classifiers to a separate object
            pattern = r'\bCL:([\S+]+)\b'
            _classifierInfo = re.findall(pattern, meaning)
            classifier = ""
            if _classifierInfo: 
                _classifierInfo = _classifierInfo[0].split('[')[0]
                classifier = _classifierInfo.split('|')[1] if '|' in _classifierInfo else _classifierInfo[0]
            

            meaning = re.sub(pattern, '', meaning)
            meaning = meaning.replace("det.", "As a determiner")
            meaning = meaning.strip('"\n , ]')

            numeric = self.numeric_map.get(simple)
            if not numeric: numeric = to_tone3(pinyin) # fallback for when numeric_map does not have the word

            freq = self.freq_map.get(simple)
            if not freq: freq = 9999999

            print(f"{self.id}, {trad} | {simple} | {freq} | {pinyin} | {numeric} | {meaning} | CL: {classifier}")
            words.append((self.id, freq, simple, trad, pinyin, numeric, meaning, classifier))

        self.cursor.executemany(f"""
        INSERT OR IGNORE INTO {self.table} (hsk_id, frequency, simple, traditional, pinyin, numeric, meaning, classifier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, words)

        self.conn.commit()
        self.conn.close()
        f.close()



if __name__ == "__main__":
    for i in range(1, 6+1):
        c = CreateHSK(id=i)
        c.append_to_db()
    c = CreateHSK(id='7-9')
    c.append_to_db()

