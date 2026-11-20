"""금주의 로또 결과 데이터 빌드.

동행복권 회차 조회 API에서 당첨 결과를 수집해
  - lotto_result/data.js : 화면(index.html)이 읽는 데이터 (최근 한 달 회차 + 출현 통계)
를 생성한다. 최신 회차 기준 한 달(28일) 이내 회차만 담으며, API 요청은 1회. GitHub Actions(.github/workflows/lotto-result.yml)에서 매주 월요일 실행.

사용: python lotto_result/build.py
"""
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
OUT_JS = BASE / "data.js"

API = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; lotto-result-bot)",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.dhlottery.co.kr/lt645/result",
}
KST = timezone(timedelta(hours=9))
FIRST_DRAW = date(2002, 12, 7)  # 1회 추첨일
RECENT_DAYS = 28                # 최신 회차 포함 최근 한 달(5회차)


def fetch(params, retries=3):
    for i in range(retries):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return (r.json().get("data") or {}).get("list") or []
        except Exception as e:  # noqa: BLE001
            print(f"  요청 실패({i + 1}/{retries}) {params}: {e}", file=sys.stderr)
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"API 요청 실패: {params}")


def compact(x):
    """API 레코드 → 저장용 축약 레코드."""
    ymd = x["ltRflYmd"]
    return {
        "round": int(x["ltEpsd"]),
        "date": f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}",
        "nums": [int(x[f"tm{i}WnNo"]) for i in range(1, 7)],
        "bonus": int(x["bnsWnNo"]),
        # 순위별 [당첨자수, 1인당 금액, 총 당첨금]
        "ranks": [
            [int(x[f"rnk{i}WnNope"] or 0), int(x[f"rnk{i}WnAmt"] or 0), int(x[f"rnk{i}SumWnAmt"] or 0)]
            for i in range(1, 6)
        ],
        # 1등 선택 유형: 자동 / 수동 / 반자동
        "firstType": [int(x.get("winType1") or 0), int(x.get("winType2") or 0), int(x.get("winType3") or 0)],
        "sales": int(x.get("rlvtEpsdSumNtslAmt") or 0),
    }


def estimate_round(now):
    """KST 기준 현재까지 추첨이 끝났을 것으로 예상되는 최신 회차."""
    days = (now.date() - FIRST_DRAW).days
    r = days // 7 + 1
    if now.weekday() == 5 and (now.hour, now.minute) < (20, 50):
        r -= 1  # 토요일 추첨 전
    return r


def main():
    now = datetime.now(KST)

    # 최신 회차 포함 10개 회차 (요청 1회)
    est = estimate_round(now)
    batch = fetch({"srchDir": "latest", "srchCursorLtEpsd": str(max(1, est - 20))})
    if not batch:
        raise RuntimeError("최신 회차 응답이 비어 있음")
    draws = sorted((compact(x) for x in batch), key=lambda d: d["round"], reverse=True)  # 최신순

    # 최근 한 달만 남김
    cutoff = date.fromisoformat(draws[0]["date"]) - timedelta(days=RECENT_DAYS)
    draws = [d for d in draws if date.fromisoformat(d["date"]) >= cutoff]
    print(f"최신 {draws[0]['round']}회 ({draws[0]['date']}) · 최근 한 달 {len(draws)}개 회차")

    # 한 달간 번호별 출현 횟수 (보너스 제외)
    freq = [0] * 46
    for d in draws:
        for n in d["nums"]:
            freq[n] += 1

    payload = {
        "updated": now.strftime("%Y-%m-%d %H:%M KST"),
        "draws": draws,
        "stats": {"total": len(draws), "freq": freq[1:]},  # freq[0] → 1번
    }
    OUT_JS.write_text(
        "/* 자동 생성 파일 — lotto_result/build.py 로 갱신. 직접 수정하지 마세요. */\n"
        "window.LOTTO_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print("data.js 생성 완료")


if __name__ == "__main__":
    main()
