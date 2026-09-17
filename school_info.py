import requests
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

# #1. 나이스 API 및 기본 설정
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
    except Exception as e:
        return f"에러: {e}"

def fetch_meal_data(target_date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": ATPT_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MLSV_YMD": target_date
    }
    try:
        response = requests.get(url, params=params).json()
        if "mealServiceDietInfo" in response:
            return response["mealServiceDietInfo"][1]["row"]
        return None
    except Exception as e:
        return f"에러: {e}"

# Simple HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>학교 생활 정보 알림이</title>
    <style>
        body { font-family: sans-serif; padding: 20px; line-height: 1.6; max-width: 600px; margin: auto; }
        .card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        h1, h2 { color: #333; }
        ul { padding-left: 20px; }
    </style>
</head>
<body>
    <h1>🏫 학교 생활 정보 알림이</h1>
    <p><strong>조회 일자:</strong> {{ today_raw }}</p>

    <div class="card">
        <h2>📅 오늘의 시간표 (1학년 8반)</h2>
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
        <h2>🍱 오늘의 급식 메뉴</h2>
        {% if meal and meal is list %}
            {% for item in meal %}
                <h3>▶ {{ item.MMEAL_SC_NM }} ({{ item.CAL_INFO }})</h3>
                <p>{{ item.DDISH_NM | safe }}</p>
            {% endfor %}
        {% else %}
            <p>※ 등록된 급식 정보가 없습니다.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# #3. 웹 라우트 (사용자 접속 시마다 작동)
@app.route("/")
def home():
    # 💡 사용자가 웹에 들어올 때마다 접속 시점의 날짜를 매번 계산
    now = datetime.now()
    today_raw = now.strftime("%Y-%m-%d")
    today = now.strftime("%Y%m%d")

    timetable = fetch_timetable_data(today)
    meal = fetch_meal_data(today)

    # 급식 메뉴 줄바꿈(<br/>) 처리
    if meal and isinstance(meal, list):
        for item in meal:
            item['DDISH_NM'] = item['DDISH_NM'].replace("<br/>", "<br/>- ")

    return render_template_string(
        HTML_TEMPLATE,
        today_raw=today_raw,
        timetable=timetable,
        meal=meal
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
