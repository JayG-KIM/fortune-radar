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

# CSS: 스타일 정의
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #333;
        margin-bottom: 5px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .big-icon { font-size: 24px; margin-bottom: 5px; }
    .card-title {
        font-size: 12px;
        font-weight: 600;
        color: #A0A0A0;
        margin-bottom: 2px;
        text-transform: uppercase;
    }
    .card-value {
        font-size: 14px;
        color: #FFFFFF;
        font-weight: 500;
        word-break: keep-all;
    }
    .title-container {
        text-align: left;
        margin-bottom: 10px;
    }
    .main-title { 
        font-size: 28px; 
        font-weight: bold; 
        color: #FFFFFF; 
        margin-bottom: 5px;
        line-height: 1.2;
    }
    .sub-title { 
        font-size: 14px; 
        color: #CCCCCC; 
        margin-bottom: 5px; 
        line-height: 1.5;
    }
    .highlight { color: #00D4FF; font-weight: bold; }
    
    /* 날씨 뱃지 (관계 모드용) */
    .weather-badge {
        background-color: #333;
        color: #fff;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        margin-left: 10px;
        vertical-align: middle;
    }
    
    /* Powered by 태그 */
    .engine-tag { 
        display: inline-block;
        font-size: 11px; 
        color: #00D4FF; 
        border: 1px solid #00D4FF; 
        padding: 4px 10px; 
        border-radius: 15px; 
        background-color: rgba(0, 212, 255, 0.05);
        margin-top: 5px;
    }

    /* 에러 메시지 */
    .quota-error {
        background-color: #2b1c1c;
        border: 1px solid #ff4b4b;
        color: #ffcccc;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-size: 15px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 모델 설정 ---
SYSTEM_PROMPT = """
당신은 'AI 처세술 전략 엔진'입니다. 
사용자와 상대방의 기질, 환경(날씨)을 분석하여 구체적인 행동 전략을 제시합니다.
"""

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. 데이터 매핑 및 함수 ---
ZODIAC_ICONS = {
    "염소자리": "🐐", "물병자리": "🏺", "물고기자리": "🐟", "양자리": "🐏",
    "황소자리": "🐂", "쌍둥이자리": "👯", "게자리": "🦀", "사자자리": "🦁",
    "처녀자리": "🧚", "천칭자리": "⚖️", "전갈자리": "🦂", "사수자리": "🏹"
}

ANIMAL_ICONS = {
    "쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍",
    "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"
}

@st.cache_data(ttl=1800)
def get_real_kma_weather():
    nx, ny = 58, 126
    now = datetime.datetime.now()
    base_time_obj = now - datetime.timedelta(minutes=40)
    base_date = base_time_obj.strftime("%Y%m%d")
    base_time = base_time_obj.strftime("%H00")
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": WEATHER_API_KEY, "pageNo": "1", "numOfRows": "1000", 
        "dataType": "JSON", "base_date": base_date, "base_time": base_time, 
        "nx": nx, "ny": ny
    }
    try:
        response = requests.get(url, params=params, timeout=3)
        data = response.json()
        items = data['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items}
        
        pty = int(weather_data.get('PTY', 0))
        temp = weather_data.get('T1H', '?')
        icon, status = "☀️", "맑음"
        
        if pty in [1, 5]: icon, status = "☔", "비"
        elif pty in [2, 6]: icon, status = "🌨️", "비/눈"
        elif pty in [3, 7]: icon, status = "☃️", "눈"
        
        return icon, f"{status} {temp}℃"
    except:
        return "📡 수신불가"

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
    if year in [2021, 2025]:
        return datetime.date(year, 2, 3)
    if 1920 <= year <= 1984 and (year % 4 == 0):
        return datetime.date(year, 2, 5)
    return datetime.date(year, 2, 4)

def get_korean_zodiac(date_obj):
    year = date_obj.year
    ipchun = get_ipchun_date(year)
    
    if date_obj < ipchun:
        target_year = year - 1
    else:
        target_year = year
        
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[target_year % 12]

def display_card(column, icon, title, value):
    with column:
        st.markdown(f"""
        <div class="info-card">
            <div class="big-icon">{icon}</div>
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# --- 4. 메인 UI ---

with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio(
        "전략 모드",
        ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"],
        index=0
    )
    st.markdown("---")
    st.caption(f"Ver 2.3.0 (Macbook First Edition)")

# 날씨 정보
weather_icon, weather_text = get_real_kma_weather()

# [수정] 나 혼자 모드에서도 하이라이트 적용!
subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
weather_html = "" 

if "나 혼자" in mode:
    pass 
else:
    weather_html = f"<span class='weather-badge'>{weather_icon} 마곡 {weather_text}</span>"
    if "가족" in mode:
        subtitle_text = "평화로운 관계를 위한 <span class='highlight'>로맨스/가족 전략</span>"
    elif "상사" in mode:
        subtitle_text = "성공적인 사회생활을 위한 <span class='highlight'>관계 공략법</span>"

st.markdown(f"""
<div class="title-container">
    <span class="main-title">오늘의 눈치 레이더</span>{weather_html}
    <div class="sub-title">{subtitle_text}</div>
    <div class="engine-tag">Powered by AI Work Strategy Engine</div>
</div>
<hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">
""", unsafe_allow_html=True)

if DEBUG_MODE:
    st.caption("🛠️ 현재 [개발자 테스트 모드]가 켜져 있습니다. API가 차감되지 않습니다.")

# --- 입력 폼 및 레이아웃 분기 ---
mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]

user_birth, user_gender, user_mbti = None, None, None
target_birth, target_gender, target_mbti = None, None, "정보 없음"
target_zodiac_name, target_animal_name, target_lunar_date = None, None, None

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
        target_birth = st.date_input("상대 생년월일", value=datetime.date(2024, 3, 5), min_value=datetime.date(1920, 1, 1), help="정확한 날짜를 모르면 대략적인 연도만 맞춰주세요.")
        r1, r2 = st.columns(2)
        with r1: target_gender = st.radio("상대 성별", ["남성", "여성"], horizontal=True)
        with r2: 
            target_mbti_opt = ["모름/선택안함"] + mbti_list
            target_mbti = st.selectbox("상대 MBTI", target_mbti_opt, help="MBTI를 입력하면 성격 궁합 기반의 전략을 제공합니다.")

# --- 데이터 계산 ---
user_lunar = get_lunar_date(user_birth)
user_zodiac_name = get_zodiac_sign(user_birth.day, user_birth.month)
user_animal_name = get_korean_zodiac(user_birth)
user_z_icon = ZODIAC_ICONS.get(user_zodiac_name, "⭐")
user_a_icon = ANIMAL_ICONS.get(user_animal_name, "🐾")

if target_birth:
    target_lunar = get_lunar_date(target_birth)
    target_zodiac_name = get_zodiac_sign(target_birth.day, target_birth.month)
    target_animal_name = get_korean_zodiac(target_birth)
    target_z_icon = ZODIAC_ICONS.get(target_zodiac_name, "⭐")
    target_a_icon = ANIMAL_ICONS.get(target_animal_name, "🐾")

# --- 카드 디스플레이 ---
if "나 혼자" in mode:
    c1, c2, c3, c4 = st.columns(4)
    display_card(c1, user_z_icon, "내 별자리", user_zodiac_name)
    display_card(c2, user_a_icon, "내 띠", f"{user_animal_name}띠")
    display_card(c3, "🌕", "음력 생일", user_lunar)
    # [수정] 양력 생일 제거하고 다시 마곡 날씨로 복구 완료!
    display_card(c4, weather_icon, "마곡 날씨", weather_text)
else:
    c_left, c_right = st.columns(2)
    with c_left:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, user_z_icon, "별자리", user_zodiac_name)
        display_card(sc2, user_a_icon, "띠", f"{user_animal_name}띠")
        display_card(sc3, "🌕", "음력", user_lunar)
    with c_right:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, target_z_icon, "별자리", target_zodiac_name)
        display_card(sc2, target_a_icon, "띠", f"{target_animal_name}띠")
        display_card(sc3, "🌕", "음력", target_lunar)

st.write("")
st.markdown("---")

# --- 5. 전략 분석 로직 ---
btn_label = "🚀 전략 분석 시작"
if "가족" in mode: btn_label = "💕 평화/사랑 전략 수립"
elif "상사" in mode: btn_label = "🤝 사회생활 공략법 분석"

if st.button(btn_label, type="primary", use_container_width=True):
    
    if "가족" in mode:
        loading_texts = ["💕 상대방의 기분을 살피는 중...", "🌪️ 데이트/가정의 평화 확률 계산 중...", "🎁 감동 포인트 시뮬레이션 중..."]
    elif "상사" in mode:
        loading_texts = ["🤝 상사의 심리 상태 스캔 중...", "🍽️ 최적의 점심 메뉴 탐색 중...", "💼 결재 타이밍 시뮬레이션 중..."]
    else:
        loading_texts = ["📡 사무실 공기 읽는 중...", "📉 업무 효율 패턴 분석 중...", "☁️ 날씨 변수 대입 중..."]

    with st.spinner(random.choice(loading_texts)):
        
        target_info_str = f"Target: {target_mbti}, Zodiac: {target_zodiac_name}, Animal: {target_animal_name}" if target_birth else "Target: Info Not Available"
        
        base_prompt = f"""
        Analyze today's strategy based on the context.
        [Input] Date: {datetime.date.today()}, Weather: {weather_text}
        [User Info] MBTI: {user_mbti}, Zodiac: {user_zodiac_name}
        [Target Info] {target_info_str}
        
        IMPORTANT: First line MUST be 4 keywords separated by '|'.
        Format: KEYWORD1|KEYWORD2|KEYWORD3|KEYWORD4
        """
        
        if "가족" in mode:
            specific_prompt = f"""
            Context: 'Family/Lover Mode'. Focus on maintaining peace, love, dating, and conflict resolution.
            
            [Summary Keywords]
            1. Love/Peace Vibe (e.g. 로맨틱, 평화 유지)
            2. Relationship Strategy (e.g. 무조건 공감, 경청)
            3. Action Item (e.g. 산책 제안, 설거지)
            4. Lucky Gesture (e.g. 꽃 한 송이, 디저트)
            
            [Detailed Section]
            - **💕 오늘의 애정/가정 기상도**: Overall atmosphere.
            - **❤️ 상대방 공략법 (Target MBTI: {target_mbti})**: How to handle lover/family today considering their Zodiac({target_zodiac_name}).
            - **🎁 추천 데이트/활동**: Activity/Menu based on weather({weather_text}).
            - **🛡️ 주의사항**: Words to avoid.
            - **💎 오늘의 치트키**: Small gift/action.
            """
        elif "상사" in mode:
            specific_prompt = f"""
            Context: 'Boss/Colleague Mode'. Focus on networking, reporting timing, office politics.
            
            [Summary Keywords]
            1. Social Luck (e.g. 의전 성공)
            2. Reporting Timing (e.g. 오후 3시)
            3. Lunch Menu (e.g. 뜨끈한 국밥)
            4. Lucky Topic (e.g. 주식 이야기)
            
            [Detailed Section]
            - **🤝 오늘의 의전/관계 운**: Overall social vibe.
            - **👔 상사/동료 공략법 (Target MBTI: {target_mbti})**: Approach strategy considering target's Zodiac({target_zodiac_name}).
            - **🍽️ 점심/회식 메뉴**: Menu fitting weather({weather_text}).
            - **🛡️ 말실수 주의보**: Topics to avoid.
            - **💎 스몰 토크 주제**: Good conversation starters.
            """
        else:
            specific_prompt = f"""
            Context: 'Solo Work Mode'. Focus on individual performance, efficiency.
            
            [Summary Keywords]
            1. Total Luck (e.g. 기회 포착)
            2. Relation Strategy (e.g. 상사 눈치 조심)
            3. Work Performance (e.g. 성과 달성)
            4. Lucky Item (e.g. 따뜻한 라떼)
            
            [Detailed Section]
            - **⚡ 오늘의 총운**: Overall vibe.
            - **🤝 상사/동료 전략**: Actionable advice.
            - **📈 업무 및 성과**: Efficiency focus.
            - **🛡️ 주의사항**: Risk management.
            - **🍀 행운의 요소**: Color, Item.
            """

        final_prompt = base_prompt + specific_prompt
        
        try:
            if DEBUG_MODE:
                time.sleep(1.5)
                full_text = f"""테스트|UI/기능 완벽 복구|{mode}|DEBUG
                
                ### 🛠️ 개발자 테스트 모드 ({mode})
                - 서브타이틀 하이라이트 복구 완료
                - 양력 생일 -> 마곡 날씨 롤백 완료
                - 공유 기능 포함
                """
            else:
                response = model.generate_content(final_prompt)
                full_text = response.text.strip()
            
            lines = full_text.split('\n')
            summary_line = None
            detail_lines = []
            
            found_summary = False
            for i, line in enumerate(lines):
                if "|" in line and not found_summary:
                    summary_line = line
                    found_summary = True
                else:
                    detail_lines.append(line)
            
            detail_text = "\n".join(detail_lines).strip()

            if summary_line:
                parts = summary_line.split('|')
            else:
                parts = ["분석 완료", "전략 수립", "기회 포착", "행운 가득"]
            while len(parts) < 4: parts.append("-")

            st.success(f"✅ {mode} 전략이 수립되었습니다.")
            
            t1, t2, t3, t4 = "오늘의 총운", "관계 전략", "핵심 미션", "행운템"
            if "가족" in mode:
                t1, t2, t3, t4 = "애정/가정운", "상대 공략", "추천 활동", "치트키"
            elif "상사" in mode:
                t1, t2, t3, t4 = "의전 운세", "보고 타이밍", "점심 추천", "대화 주제"

            r1, r2, r3, r4 = st.columns(4)
            display_card(r1, "⚡", t1, parts[0].strip())
            display_card(r2, "🎯", t2, parts[1].strip())
            display_card(r3, "🔥", t3, parts[2].strip())
            display_card(r4, "🍀", t4, parts[3].strip())
            
            st.markdown("---")
            st.markdown(detail_text)
            
            # [공유하기 기능 부활]
            st.markdown("---")
            st.subheader("📋 친구에게 공유하기")
            
            share_text = f"""[오늘의 눈치 레이더]
            
⚡ {t1}: {parts[0].strip()}
🎯 {t2}: {parts[1].strip()}
🔥 {t3}: {parts[2].strip()}
🍀 {t4}: {parts[3].strip()}

👉 전략 확인하기: https://nunchi-radar.streamlit.app"""
            
            st.code(share_text, language="text")
            st.caption("👆 위 박스 오른쪽의 '복사(Copy)' 아이콘을 누르면 결과가 복사됩니다!")

        except Exception as e:
            error_msg = str(e)
            st.markdown(f"""
            <div class="quota-error">
                <strong>📢 아쉽네요! 오늘의 선착순 분석이 마감되었습니다.</strong><br><br>
                본 서비스는 하루 <strong>선착순 20명</strong>에게만 무료로 제공하고 있어요.<br>
                <strong>매일 오후 4시(16시)</strong>에 선착순 인원이 <strong>초기화</strong>되니, 그때 꼭 다시 도전해보세요!<br>
                (팁: 알람을 맞춰두시면 놓치지 않을 거예요 😉)
            </div>
            """, unsafe_allow_html=True)
            
            if DEBUG_MODE:
                 with st.expander("개발자용 에러 상세 확인"):
                    st.error(f"실제 에러 내용: {error_msg}")
