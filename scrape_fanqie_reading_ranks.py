import json
import os
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

from scrape_fanqie_ranks import decode_text

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INIT_URL = "https://fanqienovel.com/rank/0_0_1139"
ROUTE_PREFIX = "/rank/0_0_"


def _extract_books(page):
    return page.evaluate(
        """
        () => {
            const bookMap = new Map();
            document.querySelectorAll('a[href^="/page/"]').forEach(link => {
                let container = link.parentElement;
                let depth = 0;
                while (container && depth < 7) {
                    if (container.querySelector('img') && container.innerText.includes('在读')) {
                        const href = link.getAttribute('href');
                        if (!bookMap.has(href)) bookMap.set(href, container);
                        break;
                    }
                    container = container.parentElement;
                    depth += 1;
                }
            });

            return Array.from(bookMap.values()).map(item => {
                const pageLink = item.querySelector('a[href^="/page/"]');
                const img = item.querySelector('img');
                let title = img?.getAttribute('alt')?.trim() || '';
                if (!title) {
                    const titleNode = item.querySelector('h4, h3, .title') || pageLink;
                    title = titleNode?.innerText?.trim() || '未知';
                }
                const authorNode = item.querySelector('.author, .author-name') || item.querySelector('a[href^="/author-page/"]');
                const lines = item.innerText.split('\n').map(s => s.trim()).filter(Boolean);
                const reads = lines.find(line => line.includes('在读')) || '未知';
                const introNode = item.querySelector('.intro, .abstract, .desc');
                return {
                    title,
                    author: authorNode?.innerText?.trim() || '未知',
                    reads,
                    intro: introNode?.innerText?.trim() || '暂无简介',
                    cover: img?.getAttribute('src') || '',
                    url: pageLink?.getAttribute('href') || ''
                };
            }).filter(book => book.url && !book.title.includes('榜单说明'));
        }
        """
    )


def _clean_reads(raw):
    text = decode_text(raw or "")
    if "在读" not in text:
        return text.strip() or "未知"
    return text.split("在读", 1)[1].replace(":", "").replace("：", "").strip() or "未知"


def run_scraper(limit=20, sleep_sec=4):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_key = datetime.now().strftime("%Y%m%d")
    output_file = os.path.join(OUTPUT_DIR, f"fanqie_female_reading_ranks_{date_key}.json")
    state_file = os.path.join(OUTPUT_DIR, f"reading_task_state_{date_key}.json")

    completed = []
    categories_output = []
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                completed = json.load(f).get("completed", [])
        except (OSError, ValueError):
            completed = []
    if completed and os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                categories_output = json.load(f).get("categories", [])
        except (OSError, ValueError):
            categories_output = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) if os.environ.get("GITHUB_ACTIONS") else p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(INIT_URL, wait_until="load", timeout=30000)
        page.wait_for_selector('a[href^="/page/"]', timeout=10000)

        categories = page.evaluate(
            f"""
            () => Array.from(document.querySelectorAll('a'))
                .filter(a => (a.getAttribute('href') || '').includes('{ROUTE_PREFIX}'))
                .map(a => ({{name: a.innerText.trim(), href: a.getAttribute('href')}}))
                .filter((item, index, arr) => item.name && arr.findIndex(x => x.href === item.href) === index)
            """
        )
        if not categories:
            raise RuntimeError("未发现阅读榜分类，请检查番茄榜单路由或页面结构")

        for category in categories:
            name = decode_text(category["name"])
            if name in completed:
                continue

            href = category["href"]
            target = href if href.startswith("http") else f"https://fanqienovel.com{href}"
            print(f"抓取阅读榜分类：{name} -> {target}")
            page.goto(target, wait_until="load", timeout=30000)
            page.wait_for_selector('a[href^="/page/"]', timeout=10000)
            for _ in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(1.2)

            raw_books = _extract_books(page)
            books = []
            for book in raw_books[:limit]:
                books.append({
                    "title": decode_text(book.get("title", "")),
                    "author": decode_text(book.get("author", "")),
                    "reads": _clean_reads(book.get("reads", "")),
                    "intro": decode_text(book.get("intro", "")).replace("\n", " "),
                    "cover": book.get("cover", ""),
                    "url": book["url"] if book["url"].startswith("http") else f"https://fanqienovel.com{book['url']}",
                })

            categories_output.append({"name": name, "books": books})
            snapshot = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "rank_type": "reading",
                "categories": categories_output,
            }
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)

            completed.append(name)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({"completed": completed}, f, ensure_ascii=False)
            time.sleep(sleep_sec)

        browser.close()

    if os.path.exists(state_file):
        os.remove(state_file)
    print(f"阅读榜抓取完成：{output_file}")


if __name__ == "__main__":
    run_scraper(limit=20, sleep_sec=4)
