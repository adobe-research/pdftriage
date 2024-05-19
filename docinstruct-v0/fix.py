from pathlib import Path
import json

with Path("questions.jsonl").open("r") as f:
    for line in f:
        try:
            json.loads(line)
        except:
            print("Problem:", line)
