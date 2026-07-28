import json
import os
import tempfile

from build_cross_analysis import keyword_counts
from build_reading_latest import compare


def test_compare():
    previous = [{"name": "现言脑洞", "books": [
        {"title": "旧书", "url": "u1", "reads": "1万", "intro": ""},
        {"title": "掉榜书", "url": "u2", "reads": "2万", "intro": ""},
    ]}]
    today = [{"name": "现言脑洞", "books": [
        {"title": "新书", "url": "u3", "reads": "3万", "intro": ""},
        {"title": "旧书", "url": "u1", "reads": "1.5万", "intro": ""},
    ]}]
    result = compare(today, previous)["现言脑洞"]
    assert result["new_count"] == 1
    assert result["dropped_count"] == 1
    assert result["reads_growth"][0]["growth"] == "+5000"


def test_keywords():
    counts = keyword_counts([
        {"title": "穿书女配", "intro": "豪门太子爷"},
        {"title": "穿书炮灰", "intro": "系统逆袭"},
    ])
    assert counts["穿书"] == 2
    assert counts["豪门"] == 1
    assert counts["系统"] == 1


if __name__ == "__main__":
    test_compare()
    test_keywords()
    print("reading pipeline checks passed")
