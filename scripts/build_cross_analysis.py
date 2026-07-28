import collections
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
KEYWORDS = [
    "穿书", "重生", "系统", "空间", "团宠", "萌宝", "幼崽", "女配", "炮灰", "反派",
    "年代", "七零", "八零", "军婚", "豪门", "总裁", "太子爷", "先婚后爱", "追妻",
    "甜宠", "强制爱", "兽世", "星际", "末世", "玄学", "直播", "娱乐圈", "校园",
    "替嫁", "换亲", "种田", "经商", "悬疑", "万人迷", "修罗场", "无CP", "职业",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def keyword_counts(books):
    counter = collections.Counter()
    for book in books:
        text = f"{book.get('title', '')} {book.get('intro', '')}"
        for word in KEYWORDS:
            if word in text:
                counter[word] += 1
    return counter


def top_items(counter, limit=10):
    return [{"keyword": key, "count": value} for key, value in counter.most_common(limit)]


def index_categories(data):
    return {cat.get("name"): cat for cat in data.get("categories", [])}


def main():
    new_path = os.path.join(DATA_DIR, "latest_ranks.json")
    reading_path = os.path.join(DATA_DIR, "reading_latest_ranks.json")
    if not os.path.exists(new_path) or not os.path.exists(reading_path):
        raise SystemExit("缺少新书榜或阅读榜最新数据")

    new_data = load_json(new_path)
    reading_data = load_json(reading_path)
    new_map = index_categories(new_data)
    reading_map = index_categories(reading_data)
    names = sorted(set(new_map) & set(reading_map))
    categories = []

    for name in names:
        new_books = new_map[name].get("books", [])
        reading_books = reading_map[name].get("books", [])
        new_counts = keyword_counts(new_books)
        reading_counts = keyword_counts(reading_books)
        verified = new_counts & reading_counts
        emerging = new_counts - reading_counts
        mature = reading_counts - new_counts

        shared_urls = sorted(
            set(book.get("url") for book in new_books if book.get("url"))
            & set(book.get("url") for book in reading_books if book.get("url"))
        )
        categories.append({
            "name": name,
            "new_book_count": len(new_books),
            "reading_book_count": len(reading_books),
            "same_title_or_url_count": len(shared_urls),
            "verified_keywords": top_items(verified, 8),
            "emerging_keywords": top_items(emerging, 8),
            "mature_keywords": top_items(mature, 8),
            "new_top_books": [book.get("title") for book in new_books[:5]],
            "reading_top_books": [book.get("title") for book in reading_books[:5]],
            "interpretation": {
                "verified": "两榜都高频，属于已被市场验证且新书仍在跟进的方向。",
                "emerging": "新书榜更集中，可能是新风向，也可能是作者扎堆，需要继续观察。",
                "mature": "阅读榜更集中，说明存量需求成熟，但新书供给相对较少。",
            },
        })

    output = {
        "date": max(new_data.get("date", ""), reading_data.get("date", "")),
        "new_rank_date": new_data.get("date", ""),
        "reading_rank_date": reading_data.get("date", ""),
        "method": "按分类比较新书榜与阅读榜前20本的标题和简介关键词；结论用于选题假设，不代表留存或收入。",
        "categories": categories,
    }
    write_json(os.path.join(DATA_DIR, "cross_analysis.json"), output)
    write_json(os.path.join(BASE_DIR, "api", "cross", "lastest", "all.json"), output)
    write_json(os.path.join(BASE_DIR, "api", "cross", "lastest.json"), {
        "date": output["date"],
        "url": "api/cross/lastest/all.json",
        "category_count": len(categories),
    })
    print(f"交叉分析已生成：{len(categories)}个分类")


if __name__ == "__main__":
    main()
