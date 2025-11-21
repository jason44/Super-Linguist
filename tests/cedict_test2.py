import re

def remove_cl_tag(s):
    # Pattern to match (CL:[text])
    pattern = r"\(CL:(.*?)\)"
    match = re.search(pattern, s)

    if not match:
        return s, None  # No CL tag found

    extracted_text = match.group(1)

    # Remove the whole (CL:[text]) part
    cleaned = re.sub(pattern, "", s).strip()

    return cleaned, extracted_text

cleaned, cl = remove_cl_tag("cigarette (CL:支[zhi1],條|条[tiao2],根[gen1],包[bao1],盒[he2])")
print(cleaned)
print(cl)