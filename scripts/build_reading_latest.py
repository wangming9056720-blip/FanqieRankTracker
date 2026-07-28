import glob
import json
import os
import re
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
API_DIR = os.path.join(BASE_DIR, "api", "reading", "lastest")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def parse_reads(value):
    text = str(value or "").replace(",", "").strip()
    try:
        if "万" in text:
            return float(text.replace("万", "")) * 10000
        return float(text)
    except ValueError:
        return 0


def format_growth(value):
    if abs(value) >= 10000:
        return f"{'+' if value > 0 else ''}{value / 10000:.1f}万"
    return f"{'+' if value > 0 else ''}{int(value)}"


def compare(today_categories, previous_categories):
    previous = {
        cat.get("name"): {
            book.get("url"): {"rank": index + 1, **book}
            for index, book in enumerate(cat.get("books", []))
        }
        for cat in previous_categories
    }
    result = {}
    for cat in today_categories:
        name = cat.get("name", "未知")
        old = previous.get(name, {})
        current_urls = set()
        new_books, dropped_books, risers, fallers, growth = [], [], [], [], []
        for index, book in enumerate(cat.get("books", [])):
            url = book.get("url", "")
            current_urls.add(url)
            rank = index + 1
            if url not in old:
                new_books.append(book.get("title", "未知"))
                continue
            old_rank = old[url]["rank"]
            delta = old_rank - rank
            if delta > 0:
                risers.append({"title": book.get("title", "未知"), "change": f"+{delta}"})
            elif delta < 0:
                fallers.append({"title": book.get("title", "未知"), "change": str(delta)})
            read_delta = parse_reads(book.get("reads")) - parse_reads(old[url].get("reads"))
            if read_delta:
                growth.append({"title": book.get("title", "未知"), "growth": format_growth(read_delta), "value": read_delta})

        for url, book in old.items():
            if url not in current_urls:
                dropped_books.append(book.get("title", "未知"))

        risers.sort(key=lambda x: int(x["change"].replace("+", "")), reverse=True)
        fallers.sort(key=lambda x: int(x["change"]))
        growth.sort(key=lambda x: x["value"], reverse=True)
        for item in growth:
            item.pop("value", None)

        summary_parts = []
        if new_books:
            summary_parts.append(f"新增{len(new_books)}本上榜")
        if dropped_books:
            summary_parts.append(f"{len(dropped_books)}本掉榜")
        if growth:
            summary_parts.append(f"《{growth[0]['title']}》在读增长{growth[0]['growth']}")
        result[name] = {
            "new_count": len(new_books),
            "dropped_count": len(dropped_books),
            "new_books": new_books[:5],
            "dropped_books": dropped_books[:5],
            "top_risers": risers[:3],
            "top_fallers": fallers[:3],
            "reads_growth": growth[:3],
            "summary": "；".join(summary_parts) + "。" if summary_parts else "榜单暂无明显变化。",
        }
    return result


def safe_filename(name):
    value = re.sub(r"[\\/]+", "_", str(name or "").strip())
    value = re.sub(r"[^\w\u4e00-\u9fff\s-]", "_", value)
    return re.sub(r"\s+", "_", value).strip("._") or "unknown"


def build_api(output):
    os.makedirs(API_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(API_DIR, "*.json")):
        os.remove(old)

    categories = output.get("categories", [])
    write_json(os.path.join(API_DIR, "all.json"), {"type": "all", **output})
    types = [{
        "type": "all",
        "url": "api/reading/lastest/all.json",
        "category_count": len(categories),
        "book_count": sum(len(cat.get("books", [])) for cat in categories),
    }]
    used = {"all"}
    for cat in categories:
        filename = safe_filename(cat.get("name"))
        base = filename
        counter = 2
        while filename in used:
            filename = f"{base}_{counter}"
            counter += 1
        used.add(filename)
        write_json(os.path.join(API_DIR, f"{filename}.json"), {
            "type": cat.get("name"),
            "date": output.get("date"),
            "prev_date": output.get("prev_date"),
            "category": cat,
            "categories": [cat],
        })
        types.append({
            "type": cat.get("name"),
            "url": f"api/reading/lastest/{quote(filename)}.json",
            "book_count": len(cat.get("books", [])),
        })
    index = {"date": output.get("date"), "prev_date": output.get("prev_date"), "types": types}
    write_json(os.path.join(BASE_DIR, "api", "reading", "lastest.json"), index)
    write_json(os.path.join(API_DIR, "index.json"), index)


def main():
    snapshots = sorted(glob.glob(os.path.join(DATA_DIR, "fanqie_female_reading_ranks_*.json")))
    if not snapshots:
        raise SystemExit("没有阅读榜快照，先运行 scrape_fanqie_reading_ranks.py")

    today = load_json(snapshots[-1])
    previous = load_json(snapshots[-2]) if len(snapshots) >= 2 else {"date": "", "categories": []}
    trends = compare(today.get("categories", []), previous.get("categories", []))
    categories = []
    for cat in today.get("categories", []):
        categories.append({
            "name": cat.get("name"),
            "trend": trends.get(cat.get("name"), {}),
            "books": cat.get("books", []),
        })

    output = {
        "date": today.get("date", ""),
        "prev_date": previous.get("date", ""),
        "rank_type": "reading",
        "categories": categories,
    }
    write_json(os.path.join(DATA_DIR, "reading_latest_ranks.json"), output)
    dates = [load_json(path).get("date") for path in snapshots]
    write_json(os.path.join(DATA_DIR, "reading_dates.json"), {"dates": sorted(set(filter(None, dates)))})
    write_json(os.path.join(DATA_DIR, "reading_trends", f"{today.get('date')}.json"), {
        "date": today.get("date", ""),
        "prev_date": previous.get("date", ""),
        "trends": trends,
    })
    build_api(output)
    print(f"阅读榜数据已构建：{today.get('date')}，{len(categories)}个分类")


if __name__ == "__main__":
    main()
