from datetime import datetime, timedelta
from flask import Flask
import requests

app = Flask(__name__)

API_KEY = "7968eb7f4f50450183706894e58f8961"
ATPT_CODE = "R10"


@app.route("/")
def home():
    # 1. 학교 코드 동적 조회
    s_url = "https://open.neis.go.kr/hub/schoolInfo"
    s_res = requests.get(
        s_url,
        params={
            "KEY": API_KEY,
            "Type": "json",
            "ATPT_OFCDC_SC_CODE": ATPT_CODE,
            "SCHUL_NM": "김천고등학교",
        },
    ).json()
    school_code = s_res["schoolInfo"][1]["row"][0]["SD_SCHUL_CODE"]

    today_dt = datetime.now()
    today_ymd = today_dt.strftime("%Y%m%d")
    end_ymd = (today_dt + timedelta(days=6)).strftime("%Y%m%d")

    # 2. 오늘의 시간표 (1학년 8반)
    t_url = "https://open.neis.go.kr/hub/hisTimetable"
    t_res = requests.get(
        t_url,
        params={
            "KEY": API_KEY,
            "Type": "json",
            "ATPT_OFCDC_SC_CODE": ATPT_CODE,
            "SD_SCHUL_CODE": school_code,
            "ALL_TI_YMD": today_ymd,
            "GRADE": "1",
            "CLASS_NM": "8",
        },
    ).json()

    timetable_html = ""
    if "hisTimetable" in t_res:
        rows = sorted(
            t_res["hisTimetable"][1]["row"], key=lambda x: int(x["PERIO"])
        )
        for r in rows:
            timetable_html += f"<li><b>{r['PERIO']}교시:</b> {r['ITRT_CNTNT']}</li>"
    else:
        timetable_html = "<li>등록된 시간표 정보가 없습니다.</li>"

    # 3. 7일치 급식 조회 후 날짜별로 그룹화
    m_url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    m_res = requests.get(
        m_url,
        params={
            "KEY": API_KEY,
            "Type": "json",
            "ATPT_OFCDC_SC_CODE": ATPT_CODE,
            "SD_SCHUL_CODE": school_code,
            "MLSV_FROM_YMD": today_ymd,
            "MLSV_TO_YMD": end_ymd,
        },
    ).json()

    meals_by_date = {}
    if "mealServiceDietInfo" in m_res:
        for m in m_res["mealServiceDietInfo"][1]["row"]:
            ymd = m["MLSV_YMD"]
            if ymd not in meals_by_date:
                meals_by_date[ymd] = []
            meals_by_date[ymd].append(m)

    # 4. 선택형 HTML(접기/펼치기) 생성
    weekly_meals_html = ""

    # 7일간 반복
    for i in range(7):
        target_date = today_dt + timedelta(days=i)
        ymd_str = target_date.strftime("%Y%m%d")
        date_display = target_date.strftime("%Y년 %m월 %d일 (%a)")

        # 오늘은 기본으로 펼쳐놓기(open), 나머지는 닫힘 상태
        is_open = "open" if i == 0 else ""

        if ymd_str in meals_by_date:
            daily_content = ""
            for m in meals_by_date[ymd_str]:
                dishes = m["DDISH_NM"].replace("<br/>", "<br>")
                daily_content += (
                    f"<div style='margin-bottom:10px;'>"
                    f"<b>[{m['MMEAL_SC_NM']}]</b> <small>({m['CAL_INFO']})</small>"
                    f"<p style='margin: 5px 0 10px 0; line-height:1.5;'>{dishes}</p>"
                    f"</div>"
                )

            weekly_meals_html += f"""
            <details {is_open} style="margin-bottom: 12px; border: 1px solid #ddd; border-radius: 8px; padding: 10px;">
                <summary style="font-weight: bold; font-size: 1.1em; cursor: pointer; color: #2c3e50;">
                    📆 {date_display} {"(오늘)" if i==0 else ""}
                </summary>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                    {daily_content}
                </div>
            </details>
            """
        else:
            weekly_meals_html += f"""
            <details style="margin-bottom: 12px; border: 1px solid #ddd; border-radius: 8px; padding: 10px; color: #888;">
                <summary style="font-weight: bold; cursor: pointer;">📆 {date_display}</summary>
                <p style="margin-top: 10px;">등록된 급식 정보가 없습니다.</p>
            </details>
            """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>김천고등학교 1학년 8반 정보</title>
</head>
<body style="padding: 15px; font-family: sans-serif; max-width:600px; margin:auto; background-color: #fafafa;">
    <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h2>📅 1학년 8반 오늘의 시간표</h2>
        <ul style="line-height: 1.8;">{timetable_html}</ul>
        
        <hr style="margin: 25px 0; border: 0; border-top: 1px solid #eee;">
        
        <h2>🍱 주간 급식 선택 조회</h2>
        {weekly_meals_html}
    </div>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
