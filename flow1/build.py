import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# 대상 사이트 요청
res = requests.get("http://otl.pe.kr", timeout=20,
                   headers={"User-Agent": "my-scraper (contact: me@example.com)"})
res.raise_for_status()
soup = BeautifulSoup(res.text, "html.parser")

# 원하는 내용 추출 (예: 제목들)
titles = [h.get_text(strip=True) for h in soup.select("title")]

# HTML 생성
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
items = "\n".join(f"<li>{t}</li>" for t in titles)
html = f"""<!doctype html>
<html lang="ko"><meta charset="utf-8">
<title>수집 결과</title>
<body>
<h1>수집 결과</h1>
<p>업데이트: {now}</p>
<ul>{items}</ul>
</body></html>"""

with open("flow1/index.html", "w", encoding="utf-8") as f:
    f.write(html)
