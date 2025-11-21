import os

def parse_file(file_path):
    """Reads a real file from disk."""
    print(f"Parsing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                split = line.split('/CL')
                if len(split) > 2:
                #if '/CL' in line and '(CL' in line:
                    print(line)
        return True
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return False
    


parse_file('assets/cedict/cedict_ts.u8')
