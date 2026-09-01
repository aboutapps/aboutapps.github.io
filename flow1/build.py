import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone


res = requests.get("http://otl.pe.kr/welcome.php", timeout=20,
                   headers={"User-Agent": "Mozilla/5.0 (compatible; scraper)"})

res.encoding = "euc-kr"

# ↓ 이 두 줄 추가 (디버그용)
with open("flow1/raw.html", "w", encoding="utf-8") as f:
    f.write(res.text)
    
res.raise_for_status()
res.encoding = "euc-kr"
soup = BeautifulSoup(res.text, "html.parser")

titles = []
for box in soup.select("div.xboxcontent"):      # > 제거, 넓게 잡기
    date_el = box.select_one("span.date")
    date = date_el.get_text(strip=True) if date_el else ""
    if date_el:
        date_el.extract()
    title = box.get_text(strip=True)
    if title:
        titles.append((title, date))

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
items = "\n".join(f"<li>{t} <small>({d})</small></li>" for t, d in titles)
html = f"""<!doctype html>
<html lang="ko"><meta charset="utf-8">
<title>수집 결과</title>
<body>
<h1>수집 결과</h1>
<p>업데이트: {now} · 총 {len(titles)}건</p>
<ul>{items}</ul>
</body></html>"""

with open("flow1/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"수집 완료 · {len(titles)}건")
