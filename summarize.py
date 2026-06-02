"""AI Signal KR - Claude API 요약 생성"""
import json, sys, os
from datetime import datetime
from pathlib import Path
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-5"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """당신은 AI Signal KR 뉴스레터 에디터입니다.
글로벌 AI 빅테크 뉴스를 한국 독자에게 맞게 번역·요약합니다.
규칙: 모든 출력은 한국어로, 숫자·수치는 반드시 유지,
한국 기업(삼성, SK하이닉스, 네이버, 카카오) 연관성이 있으면 언급."""

FREE_PROMPT = """다음 뉴스에서 가장 중요한 3건을 골라 요약하세요.
JSON만 반환 (마크다운 없이):
{{"top3":[{{"title_kr":"...","summary":["줄1","줄2","줄3"],"url":"...","source":"..."}}]}}
뉴스: {news_text}"""

PRO_PROMPT = """다음 뉴스 전체를 분석해 심층 뉴스레터를 작성하세요.
JSON만 반환 (마크다운 없이):
{{"headline_summary":["줄1","줄2","줄3"],
"top5":[{{"title_kr":"...","summary":["줄1","줄2","줄3","줄4","줄5"],"investment_note":"...","url":"..."}}],
"ceo_quotes":[{{"ceo":"...","original":"...","translation":"...","context":"..."}}],
"korea_stocks":"...","tomorrow_watch":"..."}}
뉴스: {news_text}"""

def build_news_text(raw):
    lines = []
    for item in raw.get("google_news", []):
        lines.append(f"[NEWS] {item['title']}\n  URL: {item['url']}\n  요약: {item['summary']}")
    return "\n\n".join(lines)

def call_claude(prompt):
    response = client.messages.create(
        model=MODEL, max_tokens=8192, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = response.content[0].text.strip()
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0].strip()
    return json.loads(raw_text)

def render_html(date, free_data, pro_data):
    date_kr = datetime.strptime(date, "%Y-%m-%d").strftime("%Y년 %m월 %d일")

    summary_items = ""
    for i, h in enumerate(pro_data.get("headline_summary", []), 1):
        summary_items += f'<div class="summary-card__item"><span class="summary-card__num">0{i}</span><span>{h}</span></div>'

    free_html = ""
    for item in free_data.get("top3", []):
        bullets = "".join(f"<li>{s}</li>" for s in item["summary"])
        src = item.get("source", "NEWS").upper()[:10]
        free_html += f"""<div class="news-card">
          <div class="news-card__header"><span class="news-card__source source--news">{src}</span></div>
          <div class="news-card__title"><a href="{item['url']}" target="_blank">{item['title_kr']}</a></div>
          <ul class="news-card__bullets">{bullets}</ul></div>"""

    pro_news_html = ""
    for item in pro_data.get("top5", []):
        bullets = "".join(f"<li>{s}</li>" for s in item["summary"])
        pro_news_html += f"""<div class="news-card">
          <div class="news-card__header"><span class="news-card__source source--pro">PRO</span></div>
          <div class="news-card__title"><a href="{item['url']}" target="_blank">{item['title_kr']}</a></div>
          <ul class="news-card__bullets">{bullets}</ul>
          <div class="news-card__invest"><strong>💡 투자 포인트</strong>{item.get('investment_note','')}</div></div>"""

    ceo_html = ""
    for q in pro_data.get("ceo_quotes", []):
        ceo_html += f"""<div class="quote-card">
          <div class="quote-card__who"><div class="quote-card__avatar">💬</div>
          <div><div class="quote-card__name">{q['ceo']}</div><div class="quote-card__role">공식 발언</div></div></div>
          <div class="quote-card__original">"{q['original']}"</div>
          <div class="quote-card__translation">🇰🇷 {q['translation']}</div>
          <div class="quote-card__context">💬 맥락: {q['context']}</div></div>"""

    if not ceo_html:
        ceo_html = '<div class="quote-card"><div class="quote-card__translation">오늘은 주목할 CEO 발언이 없습니다.</div></div>'

    return f"""<!DOCTYPE html><html lang="ko"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Signal KR — {date_kr}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}
:root{{--bg:#f0f2f5;--surface:#fff;--surface2:#f8f9fb;--border:#e4e8ef;--ink:#0f1419;--ink-sub:#536471;--ink-dim:#8899a6;--blue:#1d9bf0;--blue-bg:#e8f5fe;--green:#00ba7c;--green-bg:#e6f7f1;--purple:#7856ff;--purple-bg:#f0ecff;--gold:#f59e0b;--gold-bg:#fef3c7;--shadow:0 1px 3px rgba(0,0,0,0.08),0 4px 12px rgba(0,0,0,0.04);}}
body{{background:var(--bg);color:var(--ink);font-family:'Noto Sans KR',sans-serif;font-size:15px;line-height:1.6;max-width:680px;margin:0 auto;padding:0 16px 48px;}}
.header{{background:var(--ink);border-radius:0 0 20px 20px;padding:32px 28px 28px;margin-bottom:20px;position:relative;overflow:hidden;}}
.header::before{{content:'';position:absolute;top:-60px;right:-60px;width:200px;height:200px;background:radial-gradient(circle,rgba(29,155,240,0.15) 0%,transparent 70%);border-radius:50%;}}
.header__top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;}}
.header__logo{{font-family:'Space Mono',monospace;font-size:18px;font-weight:700;color:#fff;}}
.header__logo span{{color:var(--blue);}}
.header__badge{{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:0.15em;color:var(--green);background:rgba(0,186,124,0.12);border:1px solid rgba(0,186,124,0.3);padding:4px 10px;border-radius:20px;display:flex;align-items:center;gap:5px;}}
.live-dot{{width:5px;height:5px;background:var(--green);border-radius:50%;animation:blink 1.4s infinite;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
.header__title{{font-size:26px;font-weight:800;color:#fff;line-height:1.3;margin-bottom:8px;}}
.header__date{{font-size:12px;color:rgba(255,255,255,0.5);font-family:'Space Mono',monospace;}}
.section-title{{display:flex;align-items:center;gap:8px;margin:24px 0 12px;}}
.section-title__label{{font-size:11px;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:var(--ink-sub);}}
.section-title__line{{flex:1;height:1px;background:var(--border);}}
.tier-badge{{font-family:'Space Mono',monospace;font-size:9px;font-weight:700;letter-spacing:0.1em;padding:2px 8px;border-radius:4px;}}
.tier-badge--free{{background:var(--blue-bg);color:var(--blue);}}
.tier-badge--pro{{background:var(--gold-bg);color:var(--gold);}}
.summary-card{{background:var(--surface);border-radius:16px;padding:20px;box-shadow:var(--shadow);margin-bottom:12px;border-left:4px solid var(--blue);}}
.summary-card__item{{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);font-size:14px;color:var(--ink-sub);line-height:1.5;}}
.summary-card__item:last-child{{border-bottom:none;}}
.summary-card__num{{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;color:var(--blue);min-width:20px;margin-top:2px;}}
.news-card{{background:var(--surface);border-radius:16px;padding:20px;box-shadow:var(--shadow);margin-bottom:12px;}}
.news-card__header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;}}
.news-card__source{{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;padding:3px 8px;border-radius:6px;font-weight:700;}}
.source--news{{background:#e8f5e9;color:#2e7d32;}}
.source--pro{{background:var(--gold-bg);color:var(--gold);}}
.news-card__title{{font-size:17px;font-weight:700;line-height:1.4;color:var(--ink);margin-bottom:8px;}}
.news-card__title a{{color:inherit;text-decoration:none;}}
.news-card__bullets{{list-style:none;margin-bottom:12px;}}
.news-card__bullets li{{font-size:13px;color:var(--ink-sub);line-height:1.6;padding:3px 0 3px 14px;position:relative;}}
.news-card__bullets li::before{{content:'·';position:absolute;left:0;color:var(--blue);font-weight:700;}}
.news-card__invest{{background:var(--blue-bg);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--blue);line-height:1.5;}}
.news-card__invest strong{{display:block;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;opacity:0.7;}}
.quote-card{{background:var(--surface);border-radius:16px;padding:20px;box-shadow:var(--shadow);margin-bottom:12px;border-top:3px solid var(--purple);}}
.quote-card__who{{display:flex;align-items:center;gap:10px;margin-bottom:12px;}}
.quote-card__avatar{{width:36px;height:36px;border-radius:50%;background:var(--purple-bg);display:flex;align-items:center;justify-content:center;font-size:16px;}}
.quote-card__name{{font-size:14px;font-weight:700;color:var(--ink);}}
.quote-card__role{{font-size:12px;color:var(--ink-dim);}}
.quote-card__original{{background:var(--surface2);border-left:3px solid var(--purple);border-radius:0 8px 8px 0;padding:12px 14px;font-size:14px;font-style:italic;color:var(--ink);margin-bottom:10px;line-height:1.6;}}
.quote-card__translation{{font-size:13px;color:var(--ink-sub);line-height:1.7;margin-bottom:8px;}}
.quote-card__context{{background:var(--purple-bg);border-radius:8px;padding:8px 12px;font-size:12px;color:var(--purple);line-height:1.5;}}
.korea-card{{background:var(--surface);border-radius:16px;padding:20px;box-shadow:var(--shadow);margin-bottom:12px;border-top:3px solid var(--green);}}
.korea-card__body{{font-size:13px;color:var(--ink-sub);line-height:1.8;}}
.tomorrow-card{{background:linear-gradient(135deg,#1d9bf0 0%,#7856ff 100%);border-radius:16px;padding:20px;margin-bottom:12px;}}
.tomorrow-card__label{{font-size:11px;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:rgba(255,255,255,0.7);margin-bottom:8px;}}
.tomorrow-card__body{{font-size:13px;color:rgba(255,255,255,0.9);line-height:1.8;}}
.footer{{text-align:center;padding:20px;font-size:11px;color:var(--ink-dim);font-family:'Space Mono',monospace;line-height:2;}}
</style></head><body>
<div class="header">
  <div class="header__top"><div class="header__logo">AI <span>Signal</span> KR</div>
  <div class="header__badge"><div class="live-dot"></div>DAILY</div></div>
  <div class="header__title">오늘의 AI 인사이트 ✦</div>
  <div class="header__date">{date_kr} · Powered by Claude API</div>
</div>
<div class="section-title"><span class="section-title__label">오늘의 핵심</span><div class="section-title__line"></div><span class="tier-badge tier-badge--free">FREE</span></div>
<div class="summary-card">{summary_items}</div>
<div class="section-title"><span class="section-title__label">뉴스 3선</span><div class="section-title__line"></div><span class="tier-badge tier-badge--free">FREE</span></div>
{free_html}
<div class="section-title"><span class="section-title__label">심층 분석 5선</span><div class="section-title__line"></div><span class="tier-badge tier-badge--pro">PRO</span></div>
{pro_news_html}
<div class="section-title"><span class="section-title__label">CEO 발언 원문 번역</span><div class="section-title__line"></div><span class="tier-badge tier-badge--pro">PRO</span></div>
{ceo_html}
<div class="section-title"><span class="section-title__label">한국 주식 연계 분석</span><div class="section-title__line"></div><span class="tier-badge tier-badge--pro">PRO</span></div>
<div class="korea-card"><div class="korea-card__body">{pro_data.get('korea_stocks','오늘 연계 분석 없음')}</div></div>
<div class="tomorrow-card"><div class="tomorrow-card__label">👀 내일 주목할 이슈</div>
<div class="tomorrow-card__body">{pro_data.get('tomorrow_watch','')}</div></div>
<div class="footer">AI SIGNAL KR · {date_kr}<br>Powered by Claude API · 매일 오전 8시 발행<br>무료 구독 · 스팸 없음 · 언제든 해지 가능</div>
</body></html>"""

def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    raw_path = Path(f"data/{date}_raw.json")
    if not raw_path.exists():
        print(f"데이터 없음: {raw_path}")
        return
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    news_text = build_news_text(raw)
    print("Claude API 호출 중 (Free)...")
    free_data = call_claude(FREE_PROMPT.format(news_text=news_text))
    print("Claude API 호출 중 (Pro)...")
    pro_data = call_claude(PRO_PROMPT.format(news_text=news_text))
    html = render_html(date, free_data, pro_data)
    Path("drafts").mkdir(exist_ok=True)
    Path(f"drafts/{date}_newsletter.html").write_text(html, encoding="utf-8")
    print(f"✅ 초안 생성 완료: drafts/{date}_newsletter.html")

if __name__ == "__main__":
    main()
