import streamlit as st
import google.generativeai as genai
import datetime
import requests
import json
import random
import os
import time
from dotenv import load_dotenv
from korean_lunar_calendar import KoreanLunarCalendar

# --- 1. 환경 변수 및 설정 로드 ---
load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    st.error("🚨 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# 디버그 모드 확인
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

st.set_page_config(
    page_title="오늘의 눈치 레이더",
    page_icon="📡",
    layout="wide"
)

# CSS: 원본 스타일 유지
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E; padding: 10px; border-radius: 8px; text-align: center;
        border: 1px solid #333; margin-bottom: 5px; height: 110px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .big-icon { font-size: 24px; margin-bottom: 5px; }
    .card-title { font-size: 12px; font-weight: 600; color: #A0A0A0; margin-bottom: 2px; text-transform: uppercase; }
    .card-value { font-size: 14px; color: #FFFFFF; font-weight: 500; word-break: keep-all; }
    .title-container { text-align: left; margin-bottom: 10px; }
    .main-title { font-size: 28px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px; line-height: 1.2; }
    .sub-title { font-size: 14px; color: #CCCCCC; margin-bottom: 5px; line-height: 1.5; }
    .highlight { color: #00D4FF; font-weight: bold; }
    .weather-badge { background-color: #333; color: #fff; padding: 5px 10px; border-radius: 15px; font-size: 12px; margin-left: 10px; vertical-align: middle; }
    .engine-tag { display: inline-block; font-size: 11px; color: #00D4FF; border: 1px solid #00D4FF; padding: 4px 10px; border-radius: 15px; background-color: rgba(0, 212, 255, 0.05); margin-top: 5px; }
    .quota-error { background-color: #2b1c1c; border: 1px solid #ff4b4b; color: #ffcccc; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 15px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 모델 설정 ---
SYSTEM_PROMPT = "당신은 'AI 처세술 전략 엔진'입니다. 사용자와 상대방의 기질, 환경(날씨)을 분석하여 구체적인 행동 전략을 제시합니다."

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. 데이터 매핑 및 함수 ---
ZODIAC_ICONS = {"염소자리": "🐐", "물병자리": "🏺", "물고기자리": "🐟", "양자리": "🐏", "황소자리": "🐂", "쌍둥이자리": "👯", "게자리": "🦀", "사자자리": "🦁", "처녀자리": "🧚", "천칭자리": "⚖️", "전갈자리": "🦂", "사수자리": "🏹"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

@st.cache_data(ttl=1800)
def get_real_kma_weather():
    nx, ny = 58, 126
    now = datetime.datetime.now()
    base_time_obj = now - datetime.timedelta(minutes=40)
    base_date, base_time = base_time_obj.strftime("%Y%m%d"), base_time_obj.strftime("%H00")
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {"serviceKey": WEATHER_API_KEY, "pageNo": "1", "numOfRows": "1000", "dataType": "JSON", "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny}
    try:
        response = requests.get(url, params=params, timeout=3)
        data = response.json()
        items = data['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items}
        pty, temp = int(weather_data.get('PTY', 0)), weather_data.get('T1H', '?')
        icon, status = "☀️", "맑음"
        if pty in [1, 5]: icon, status = "☔", "비"
        elif pty in [2, 6]: icon, status = "🌨️", "비/눈"
        elif pty in [3, 7]: icon, status = "☃️", "눈"
        return icon, f"{status} {temp}℃"
    except: return "📡", "수신불가"

def get_lunar_date(date_obj):
    calendar = KoreanLunarCalendar()
    calendar.setSolarDate(date_obj.year, date_obj.month, date_obj.day)
    return calendar.LunarIsoFormat()

def get_zodiac_sign(day, month):
    md = month * 100 + day
    if 120 <= md <= 218: return "물병자리"
    elif 219 <= md <= 320: return "물고기자리"
    elif 321 <= md <= 419: return "양자리"
    elif 420 <= md <= 520: return "황소자리"
    elif 521 <= md <= 621: return "쌍둥이자리"
    elif 622 <= md <= 722: return "게자리"
    elif 723 <= md <= 822: return "사자자리"
    elif 823 <= md <= 922: return "처녀자리"
    elif 923 <= md <= 1022: return "천칭자리"
    elif 1023 <= md <= 1122: return "전갈자리"
    elif 1123 <= md <= 1224: return "사수자리"
    else: return "염소자리"

def get_ipchun_date(year):
    if year in [2021, 2025]: return datetime.date(year, 2, 3)
    if 1920 <= year <= 1984 and (year % 4 == 0): return datetime.date(year, 2, 5)
    return datetime.date(year, 2, 4)

def get_korean_zodiac(date_obj):
    year = date_obj.year
    ipchun = get_ipchun_date(year)
    target_year = year if date_obj >= ipchun else year - 1
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[target_year % 12]

def display_card(column, icon, title, value):
    with column:
        st.markdown(f'<div class="info-card"><div class="big-icon">{icon}</div><div class="card-title">{title}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

# --- 4. 메인 UI ---
with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio("전략 모드", ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"], index=0)
    st.markdown("---")
    st.caption(f"Ver 2.3.0 (Macbook First Edition)")

weather_icon, weather_text = get_real_kma_weather()
subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
weather_html = ""

if "나 혼자" not in mode:
    weather_html = f"<span class='weather-badge'>{weather_icon} 마곡 {weather_text}</span>"
    if "가족" in mode: subtitle_text = "평화로운 관계를 위한 <span class='highlight'>로맨스/가족 전략</span>"
    elif "상사" in mode: subtitle_text = "성공적인 사회생활을 위한 <span class='highlight'>관계 공략법</span>"

st.markdown(f'<div class="title-container"><span class="main-title">오늘의 눈치 레이더</span>{weather_html}<div class="sub-title">{subtitle_text}</div><div class="engine-tag">Powered by AI Work Strategy Engine</div></div><hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

if DEBUG_MODE: st.caption("🛠️ 현재 [개발자 테스트 모드]가 켜져 있습니다.")

mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]
user_birth, target_birth = None, None
target_mbti = "정보 없음"

if "나 혼자" in mode:
    st.subheader("👤 내 정보")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: user_birth = st.date_input("내 생년월일", value=datetime.date(2024, 3, 5), min_value=datetime.date(1920, 1, 1))
    with c2: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
    with c3: user_mbti = st.selectbox("내 MBTI", mbti_list)
else:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("👤 나 (User)")
        user_birth = st.date_input("내 생년월일", value=datetime.date(2024, 3, 5), min_value=datetime.date(1920, 1, 1))
        r1, r2 = st.columns(2)
        with r1: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
        with r2: user_mbti = st.selectbox("내 MBTI", mbti_list)
    with col_right:
        label = "🏠 가족/애인" if "가족" in mode else "🤝 상사/동료"
        st.subheader(f"{label} (Target)")
        target_birth = st.date_input("상대 생년월일", value=datetime.date(2024, 3, 5), min_value=datetime.date(1920, 1, 1))
        r1, r2 = st.columns(2)
        with r1: target_gender = st.radio("상대 성별", ["남성", "여성"], horizontal=True)
        with r2: target_mbti = st.selectbox("상대 MBTI", ["모름/선택안함"] + mbti_list)

user_lunar, user_zodiac, user_animal = get_lunar_date(user_birth), get_zodiac_sign(user_birth.day, user_birth.month), get_korean_zodiac(user_birth)
if "나 혼자" in mode:
    c1, c2, c3, c4 = st.columns(4)
    display_card(c1, ZODIAC_ICONS.get(user_zodiac, "⭐"), "내 별자리", user_zodiac)
    display_card(c2, ANIMAL_ICONS.get(user_animal, "🐾"), "내 띠", f"{user_animal}띠")
    display_card(c3, "🌕", "음력 생일", user_lunar)
    display_card(c4, weather_icon, "마곡 날씨", weather_text)
else:
    target_lunar, target_zodiac, target_animal = get_lunar_date(target_birth), get_zodiac_sign(target_birth.day, target_birth.month), get_korean_zodiac(target_birth)
    cl, cr = st.columns(2)
    with cl:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, ZODIAC_ICONS.get(user_zodiac, "⭐"), "별자리", user_zodiac)
        display_card(sc2, ANIMAL_ICONS.get(user_animal, "🐾"), "띠", f"{user_animal}띠")
        display_card(sc3, "🌕", "음력", user_lunar)
    with cr:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, ZODIAC_ICONS.get(target_zodiac, "⭐"), "별자리", target_zodiac)
        display_card(sc2, ANIMAL_ICONS.get(target_animal, "🐾"), "띠", f"{target_animal}띠")
        display_card(sc3, "🌕", "음력", target_lunar)

st.write("")
st.markdown("---")

# --- 5. 전략 분석 로직 ---
btn_label = "🚀 전략 분석 시작"
if "가족" in mode: btn_label = "💕 평화/사랑 전략 수립"
elif "상사" in mode: btn_label = "🤝 사회생활 공략법 분석"

if st.button(btn_label, type="primary", use_container_width=True):
    loading_texts = ["📡 사무실 공기 읽는 중...", "📉 업무 효율 패턴 분석 중...", "☁️ 날씨 변수 대입 중..."]
    if "가족" in mode: loading_texts = ["💕 상대 기분 살피는 중...", "🌪️ 평화 확률 계산 중...", "🎁 감동 포인트 시뮬레이션 중..."]
    elif "상사" in mode: loading_texts = ["🤝 상사 심리 스캔 중...", "🍽️ 최적 메뉴 탐색 중...", "💼 결재 타이밍 분석 중..."]

    with st.spinner(random.choice(loading_texts)):
        target_info = f"Target: {target_mbti}, {target_zodiac}, {target_animal}" if target_birth else "Solo"
        
        # [행운템 다양성 보강 지시어 포함]
        base_prompt = f"""
        Analyze today's strategy. KEYWORD4 (Lucky Item) MUST be a specific, quirky physical item (e.g. Bamboo wife(죽부인), noise-canceling headphones, red socks, 90s stickers). NEVER only suggest drinks.
        Input: {datetime.date.today()}, {weather_text}, User: {user_mbti}, {user_zodiac}. {target_info}
        Format: KEY1|KEY2|KEY3|KEY4
        """
        
        if "가족" in mode:
            specific_prompt = f"Context: Family/Lover. KEYWORDS: 1.Love Vibe, 2.Strategy, 3.Action, 4.Lucky Item (Quirky!)"
        elif "상사" in mode:
            specific_prompt = f"Context: Boss/Colleague. KEYWORDS: 1.Social Luck, 2.Timing, 3.Lunch, 4.Lucky Item (Office quirk!)"
        else:
            specific_prompt = f"Context: Solo Work. KEYWORDS: 1.Total Luck, 2.Survival, 3.Performance, 4.Lucky Item (Fun quirk!)"

        try:
            if DEBUG_MODE:
                full_text = f"기회 포착|상사 눈치 조심|보고서 마무리|죽부인\n\n### 상세분석\n테스트 중입니다."
            else:
                response = model.generate_content(base_prompt + specific_prompt)
                full_text = response.text.strip()
            
            lines = full_text.split('\n')
            parts = lines[0].split('|') if '|' in lines[0] else ["분석완료", "전략수립", "기회포착", "행운템"]
            while len(parts) < 4: parts.append("-")

            st.success(f"✅ {mode} 전략 수립 완료")
            t1, t2, t3, t4 = "오늘의 총운", "관계 전략", "핵심 미션", "행운템"
            if "가족" in mode: t1, t2, t3, t4 = "애정운", "상대 공략", "추천 활동", "치트키"
            elif "상사" in mode: t1, t2, t3, t4 = "의전 운세", "보고 타이밍", "점심 추천", "대화 주제"

            r1, r2, r3, r4 = st.columns(4)
            display_card(r1, "⚡", t1, parts[0])
            display_card(r2, "🎯", t2, parts[1])
            display_card(r3, "🔥", t3, parts[2])
            display_card(r4, "🍀", t4, parts[3])
            
            st.markdown("---")
            st.markdown("\n".join(lines[1:]))
            
            st.markdown("---")
            st.subheader("📋 친구에게 공유하기")
            share_text = f"[오늘의 눈치 레이더]\n⚡ {t1}: {parts[0].strip()}\n🎯 {t2}: {parts[1].strip()}\n🔥 {t3}: {parts[2].strip()}\n🍀 {t4}: {parts[3].strip()}\n\n👉 확인하기: https://nunchi-radar.streamlit.app"
            st.code(share_text, language="text")
            st.caption("👆 위 박스 오른쪽의 '복사(Copy)' 아이콘을 누르세요!")

        except Exception as e:
            st.markdown(f'<div class="quota-error">📢 선착순 마감되었습니다. 내일 다시 시도해주세요!</div>', unsafe_allow_html=True)
            if DEBUG_MODE: st.error(str(e))
