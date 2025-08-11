# def split_str_by_len(text: str, chunk_size: int = 500) -> list[str]:
#     return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

import re

def semantic_split(text, max_len=500):
    # 先用中文標點切句
    sentences = re.split(r'([。？！\n])', text)
    sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2])]
    
    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) <= max_len:
            current += sent
        else:
            chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks
