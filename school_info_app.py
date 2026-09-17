import requests
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template_string

app = Flask(__name__)

# 한국 표준시(KST = UTC + 9시간) 설정
KST = timezone(timedelta(hours=9))

# #1. 나이스 API 설정
API_KEY = "7968eb7f4f50450183706894e58f8961"
ATPT_CODE = "R10"  # 경상북도교육청

def get_school_code(school_name="김천고등학교"):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": ATPT_CODE,
        "SCHUL_NM": school_name
    }
    try:
        res = requests.get(url, params=params).json()
        return res['schoolInfo'][1]['row'][0]['SD_SCHUL_CODE']
    except Exception:
        return None

SCHOOL_CODE = get_school_code()

# #2. 데이터 수집 함수
def fetch_timetable_data(target_date, grade="1", class_nm="8"):
    url = "https://open.neis.go.kr/hub/hisTimetable"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": ATPT_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "ALL_TI_YMD": target_date,
        "GRADE": grade,
        "CLASS_NM": class_nm
    }
    try:
        response = requests.get(url, params=params).json()
        if "hisTimetable" in response:
            rows = response["hisTimetable"][1]["row"]
            rows = sorted(rows, key=lambda x: int(x["PERIO"]))
            return [{"perio": r["PERIO"], "subject": r["ITRT_CNTNT"]} for r in rows]
        return None
    except Exception:
        return None

def fetch_weekly_meal_data(start_date, end_date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": ATPT_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MLSV_FROM_YMD": start_date,
        "MLSV_TO_YMD": end_date
    }
    try:
        response = requests.get(url, params=params).json()
        if "mealServiceDietInfo" in response:
            return response["mealServiceDietInfo"][1]["row"]
        return []
    except Exception:
        return []

# #3. HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>김천고등학교 생활 알림이</title>
    <style>
        body { font-family: sans-serif; padding: 20px; line-height: 1.6; max-width: 600px; margin: auto; background-color: #f8f9fa; }
        .card { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        h1 { color: #2c3e50; font-size: 1.5rem; text-align: center; }
        h2 { color: #34495e; font-size: 1.2rem; border-bottom: 2px solid #eee; padding-bottom: 8px; }
        ul { padding-left: 20px; }
        .today-badge { background-color: #27ae60; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-left: 5px; }
        .meal-date { font-weight: bold; font-size: 1.05rem; margin-top: 15px; color: #2980b9; }
        .meal-type { font-weight: bold; color: #e67e22; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🏫 김천고등학교 1학년 8반</h1>

    <div class="card">
        <h2>📅 오늘의 시간표 ({{ today_display }})</h2>
        {% if timetable and timetable is list %}
            <ul>
            {% for item in timetable %}
                <li><strong>{{ item.perio }}교시:</strong> {{ item.subject }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>※ 등록된 시간표 정보가 없습니다 (주말/휴일).</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>🍱 주간 급식 조회</h2>
        {% if meal_list %}
            {% for item in meal_list %}
                <div class="meal-date">
                    📆 {{ item.MLSV_YMD[:4] }}년 {{ item.MLSV_YMD[4:6] }}월 {{ item.MLSV_YMD[6:] }}일
                    {% if item.MLSV_YMD == today_ymd %}
                        <span class="today-badge">(오늘)</span>
                    {% endif %}
                </div>
                <div class="meal-type">[{{ item.MMEAL_SC_NM }}] <small>({{ item.CAL_INFO }})</small></div>
                <div>{{ item.DDISH_NM | safe }}</div>
            {% endfor %}
        {% else %}
            <p>※ 급식 정보가 없습니다.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# #4. 접속할 때마다 동적 실행
@app.route("/")
def home():
    now = datetime.now(KST)
    today_ymd = now.strftime("%Y%m%d")
    today_display = now.strftime("%Y-%m-%d")

    end_dt = now + timedelta(days=6)
    end_ymd = end_dt.strftime("%Y%m%d")

    timetable = fetch_timetable_data(today_ymd)
    raw_meals = fetch_weekly_meal_data(today_ymd, end_ymd)

    if raw_meals:
        for m in raw_meals:
            m['DDISH_NM'] = m['DDISH_NM'].replace("<br/>", "<br/>• ")

    return render_template_string(
        HTML_TEMPLATE,
        today_display=today_display,
        today_ymd=today_ymd,
        timetable=timetable,
        meal_list=raw_meals
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
