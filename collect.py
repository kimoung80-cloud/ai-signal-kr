"""AI Signal KR - 뉴스 수집"""
import feedparser, requests, json
from datetime import datetime, timezone
from pathlib import Path

NEWS_QUERIES = [
    "OpenAI GPT", "NVIDIA AI chip", "Google Gemini AI",
    "Meta AI Llama", "Samsung AI semiconductor",
    "SK Hynix HBM", "AI startup Korea", "artificial intelligence CEO",
]

def fetch_google_news(query, max_items=4):
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:max_items]:
        results.append({
            "source": "google_news", "query": query,
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": entry.get("summary", "")[:300],
        })
    return results

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    all_news = []
    for q in NEWS_QUERIES:
        articles = fetch_google_news(q)
        all_news.extend(articles)
        print(f"  ✓ '{q}' — {len(articles)}건")
    Path("data").mkdir(exist_ok=True)
    data = {"date": today, "collected_at": datetime.now(timezone.utc).isoformat(),
            "google_news": all_news, "youtube": [], "x_manual": []}
    Path(f"data/{today}_raw.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 수집 완료 — {len(all_news)}건")

if __name__ == "__main__":
    main()
