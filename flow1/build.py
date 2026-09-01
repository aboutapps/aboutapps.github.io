import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# 대상 사이트 요청
res = requests.get("http://otl.pe.kr", timeout=20,
                   headers={"User-Agent": "my-scraper (contact: me@example.com)"})
res.raise_for_status()
res.encoding = "euc-kr"   # 이 사이트는 euc-kr → 한글 깨짐 방지
soup = BeautifulSoup(res.text, "html.parser")

# 게시물만 추출 (.xboxcontent 가 있는 wrdLatest 만 = 카테고리 select 제외)
titles = []
for box in soup.select("div.wrdLatest > div.xboxcontent"):
    date_el = box.select_one("span.date")
    date = date_el.get_text(strip=True) if date_el else ""
    if date_el:
        date_el.extract()               # 날짜 떼고
    title = box.get_text(strip=True)    # 남은 게 제목
    if title:
        titles.append((title, date))

# HTML 생성
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

print(f"index.html 생성 완료 · {len(titles)}건")
