def split_str_by_len(text: str, chunk_size: int = 100) -> list[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]