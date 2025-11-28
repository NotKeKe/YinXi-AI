from pathlib import Path

JSONL_PATH = Path(__file__).parent / 'datas.jsonl'
JSONL_PATH.touch(exist_ok=True)