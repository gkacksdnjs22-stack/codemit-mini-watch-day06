import json
from learning.report import build_report
from learning.support import load_observation

if __name__ == "__main__":
    rows = load_observation()
    for threshold in (10, 20):
        print(json.dumps(build_report(rows, threshold), ensure_ascii=False, indent=2))
