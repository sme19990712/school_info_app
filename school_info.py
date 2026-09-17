import requests
from datetime import datetime

# #1. 나이스 API 및 기본 설정
API_KEY = "7968eb7f4f50450183706894e58f8961"
ATPT_CODE = "R10"  # 경상북도교육청

# 학교명으로 정확한 SD_SCHUL_CODE 자동 가져오기
search_url = "https://open.neis.go.kr/hub/schoolInfo"
search_params = {
    "KEY": API_KEY,
    "Type": "json",
    "ATPT_OFCDC_SC_CODE": ATPT_CODE,
    "SCHUL_NM": "김천고등학교"
}

res = requests.get(search_url, params=search_params).json()
SCHOOL_CODE = res['schoolInfo'][1]['row'][0]['SD_SCHUL_CODE']


# #2. 데이터 수집 함수 (target_date 매개변수 받도록 설정)
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
        response = requests.get(url, params=params)
        data = response.json()
        
        if "hisTimetable" in data:
            row = data["hisTimetable"][1]["row"]
            timetable = [{"perio": item["PERIO"], "subject": item["ITRT_CNTNT"]} for item in row]
            return timetable
        return None
    except Exception as e:
        return f"에러 발생: {e}"

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
        response = requests.get(url, params=params)
        data = response.json()
        
        if "mealServiceDietInfo" in data:
            row = data["mealServiceDietInfo"][1]["row"]
            return row
        return None
    except Exception as e:
        return f"에러 발생: {e}"

# #3. 결과 출력 실행 (실행 시점 날짜 자동 생성)
if __name__ == "__main__":
    # 실행하는 시점의 실시간 날짜를 생성 (매번 새로 바뀜)
    now = datetime.now()
    today_raw = now.strftime("%Y-%m-%d")
    today = now.strftime("%Y%m%d")

    print("==========================================")
    print(f"🏫 학교 생활 정보 알림이 [{today_raw}]")
    print("==========================================")
    
    # 시간표 조회
    timetable = fetch_timetable_data(today)
    print("\n[ 📅 오늘의 시간표 (1학년 8반) ]")
    if timetable and isinstance(timetable, list):
        for item in timetable:
            print(f"  {item['perio']}교시: {item['subject']}")
    else:
        print(" ※ 등록된 시간표 정보가 없습니다 (주말/휴일).")
        
    # 급식 조회
    meal = fetch_meal_data(today)
    print("\n[ 🍱 오늘의 급식 메뉴 ]")
    if meal and isinstance(meal, list):
        for item in meal:
            dish_name = item['DDISH_NM'].replace("<br/>", "\n  - ")
            print(f"▶ {item['MMEAL_SC_NM']} ({item['CAL_INFO']})")
            print(f"  - {dish_name}\n")
    else:
        print(" ※ 등록된 급식 정보가 없습니다.")
    print("==========================================")
