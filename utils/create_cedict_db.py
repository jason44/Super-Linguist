import json
import re
import os
from pypinyin.contrib.tone_convert import to_tone


# ---------------------------------------------------------
# 1. Helper Class for Parsing
# ---------------------------------------------------------

class CEDICTParser:
    def __init__(self):
        self.entries = {}

    def extract_classifier(self, definition):
        """Extract classifier from a single definition"""
        pattern = r"\(CL:(.*?)\)"
        match = re.search(pattern, definition)
        if not match:
            return definition, ""
        cl = match.group(1)
        cleaned = re.sub(pattern, "", definition).strip()
        return cleaned, cl
        
    def numeric_to_tone(self, text: str):
        "replaces any numeric pinyin in a definition with its tone equivalent"
        return re.sub(r'\[(.*?)\]',
                  lambda m: f'({to_tone(m.group(1))})',
                  text)

    def parse_line(self, line):
        """Parses a single line of CEDICT and adds it to the internal dictionary."""
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            return

        # Regex to extract: Traditional Simplified [pinyin] /definitions...
        # 1. Traditional (non-space)
        # 2. Simplified (non-space)
        # 3. Pinyin (content inside [])
        # 4. Raw Definitions (content after /)
        match = re.match(r'(\S+)\s+(\S+)\s+\[(.*?)\]\s+/(.*)', line)
        
        if not match:
            return

        trad, simp, pinyin, raw_defs = match.groups()
        
        # Process definitions string (remove trailing slash if present)
        if raw_defs.endswith('/'):
            raw_defs = raw_defs[:-1]
        
        # Split by slash to get individual items
        def_items = raw_defs.split('/')
        
        definitions = []
        classifiers = []
        classifier_idx = 0

        for item in def_items:
            item = item.strip()
            if not item:
                continue

            # Handle Classifiers (Measure words)
            if item.startswith('CL:'):
                cl_string = item[3:] # Strip "CL:"
                cl_string = self.numeric_to_tone(cl_string).strip()

                # Classifier block applies to all definitions preceeding it AFTER the previous classifier block
                count = classifier_idx-len(definitions)
                classifiers = classifiers[:count]
                for _ in range(-count):
                    classifiers.append(cl_string)
                classifier_idx = len(definitions)
            
            # Exclude surnames
            elif item.lower().startswith('surname'):
                continue

            # Normal definition
            else:
                # replace numeric pinyin with tone pinyin
                definition, classifier = self.extract_classifier(item)
                definition = self.numeric_to_tone(definition) 
                classifier = self.numeric_to_tone(classifier)
                definitions.append(definition)
                classifiers.append(classifier)

        # If there are no valid definitions left (e.g. it was only a surname entry),
        # skip this variation.
        if not definitions:
            return

        # Create a unique key for the characters to combine variations
        # (e.g., multi-pronunciation words like 'xing' vs 'hang')
        key = simp

        if key not in self.entries:
            self.entries[key] = {
                "traditional": trad,
                "simplified": simp,
                "variations": []
            }
        else:
            pass

        # Append this specific variation (pronunciation/meaning set)
        self.entries[key]["variations"].append({
            "pinyin": to_tone(pinyin),
            "definitions": definitions,
            "classifiers": classifiers
        })

    def parse_file(self, file_path):
        """Reads a real file from disk."""
        print(f"Parsing {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self.parse_line(line)
            return True
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
            return False

    def get_json(self):
        """Returns the list of objects as a JSON string."""
        # Convert dictionary values to a list
        result_list = list(self.entries.values())
        return json.dumps(result_list, ensure_ascii=False, indent=2)

    def save_json(self, output_path):
        """Saves the parsed data to a JSON file."""
        result_list = list(self.entries.values())
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_list, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved to {output_path}")


# ---------------------------------------------------------
# 2. Main Execution Block
# ---------------------------------------------------------

if __name__ == "__main__":
    parser = CEDICTParser()

    if parser.parse_file("asset/cedict/cedict_ts.u8"):
        parser.save_json("cedict.json")



        # Inline classifiers can appear in a variety of ways. 
        # It is best to handle these on the javascript side when we split the defs by the semi-colons
        # the classifiers apply to everything in
        # /living being; creature (CL:個|个[ge4],條|条[tiao2]/
        # /application form (CL:份[fen4])/
        # /joke; jest (CL:個|个[ge4]/[some verb]  noun->CL->verbs

        # For separated classifiers, the classifiers only apply to the definitions that come before it.
        # the words after are usually not nouns (or nouns which the classifier do not apply to?)
        # /level/grade/rank/step (of stairs)/CL:個|个[ge4]/classifier: step, level/
        # /the end/end point/finishing line (in a race)/destination/terminus/CL:個|个[ge4]/
        # /conclusion/verdict/CL:個|个[ge4]/to conclude/to reach a verdict/  noun->CL->verbs
        # 