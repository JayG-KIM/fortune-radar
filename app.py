__version__ = "2.0.0"
__release_date__ = "2025-02-23"

import streamlit as st
import datetime
import requests
import random
import os
from dotenv import load_dotenv
from korean_lunar_calendar import KoreanLunarCalendar
import holidays

# --- 1. 환경 변수 및 설정 ---
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

st.set_page_config(page_title="오늘의 눈치 레이더", page_icon="📡", layout="wide")

# CSS 스타일
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E; padding: 10px; border-radius: 8px; text-align: center;
        border: 1px solid #333; margin-bottom: 5px; height: 120px;
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
    .special-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px; padding: 15px; margin: 10px 0; text-align: center;
    }
    .special-banner-title { font-size: 16px; font-weight: bold; color: #FFFFFF; }
    .special-banner-desc { font-size: 13px; color: #E0E0E0; margin-top: 5px; }
    .variable-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px dashed #FFD93D; border-radius: 12px; padding: 15px; margin: 15px 0; text-align: center;
    }
    .variable-title { font-size: 12px; color: #FFD93D; margin-bottom: 5px; }
    .variable-content { font-size: 16px; color: #FFFFFF; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- 2. 업무지구 설정 ---
BUSINESS_DISTRICTS = {
    "CBD (종로/을지로)": {"nx": 60, "ny": 127, "name": "종로"},
    "YBD (여의도)": {"nx": 58, "ny": 126, "name": "여의도"},
    "GBD (강남/테헤란로)": {"nx": 61, "ny": 126, "name": "강남"},
    "BBD (판교)": {"nx": 62, "ny": 123, "name": "판교"},
    "MBD (마곡)": {"nx": 58, "ny": 125, "name": "마곡"},
}

# --- 3. 아이콘 데이터 ---
ZODIAC_ICONS = {"물병자리": "🏺", "물고기자리": "🐟", "양자리": "🐏", "황소자리": "🐂", "쌍둥이자리": "👯", "게자리": "🦀", "사자자리": "🦁", "처녀자리": "🧚", "천칭자리": "⚖️", "전갈자리": "🦂", "사수자리": "🏹", "염소자리": "🐐"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

# --- 4. 운세 템플릿 데이터 ---
TEMPLATES = {
    # MBTI별 한줄운세
    "mbti_fortune": {
        "ISTJ": ["체계적으로 움직이면 승리", "오늘은 원칙대로 가는 게 답", "꼼꼼함이 빛나는 날", "루틴을 지키면 복이 온다", "조용히 실력 발휘하는 날"],
        "ISFJ": ["배려가 돌아오는 날", "묵묵히 하던 일이 인정받음", "팀원 덕에 웃는 날", "성실함이 보상받는다", "서포터 역할이 빛나는 날"],
        "INFJ": ["직감을 믿어도 되는 날", "조용히 관찰하면 기회 보임", "혼자만의 시간이 필요해", "깊은 생각이 해답을 준다", "공감 능력이 빛나는 날"],
        "INTJ": ["전략대로 움직이면 성공", "장기적 관점이 승리하는 날", "분석이 맞아떨어지는 날", "계획 수정은 내일로 미뤄", "논리로 설득하기 좋은 날"],
        "ISTP": ["문제 해결 능력 폭발하는 날", "손 대면 다 고쳐지는 날", "효율 최고인 날", "군더더기 없이 깔끔하게", "실용적 판단이 빛남"],
        "ISFP": ["감성이 통하는 날", "작은 것에서 행복 발견", "자기만의 속도로 가면 됨", "억지로 맞추지 마", "여유가 답인 날"],
        "INFP": ["창의력 터지는 날", "영감이 찾아오는 시간", "마음 가는 대로 해도 됨", "진정성이 통하는 날", "감정에 솔직하면 좋은 일 생김"],
        "INTP": ["호기심이 기회 만드는 날", "분석 모드 풀가동", "새로운 방법 시도 OK", "질문이 답을 만든다", "논리적 접근이 승리"],
        "ESTP": ["행동력이 빛나는 날", "일단 저지르면 되는 날", "순발력으로 해결 가능", "현장에서 답 찾는다", "에너지 넘치는 하루"],
        "ESFP": ["분위기 메이커 역할 추천", "사람 만나면 좋은 일 생김", "즉흥적 결정이 좋아", "재미를 찾으면 일도 술술", "웃으면 복이 와"],
        "ENFP": ["아이디어 폭발 예정", "열정이 전염되는 날", "새로운 시도 대환영", "가능성을 보면 기회", "에너지 조절만 잘 하면 됨"],
        "ENTP": ["토론하면 이기는 날", "창의적 해결책 떠오름", "도전이 기회 되는 날", "말빨이 통하는 날", "새로운 관점이 승리"],
        "ESTJ": ["리더십 발휘하기 좋은 날", "추진력으로 밀어붙여", "체계 잡으면 성공", "원칙 지키면 인정받음", "결단력이 빛나는 날"],
        "ESFJ": ["팀워크 최고인 날", "화합을 이끌면 좋은 일", "배려가 돌아오는 날", "사람 관계에서 행운", "분위기 띄우면 일도 술술"],
        "ENFJ": ["영향력이 커지는 날", "리드하면 따라오는 날", "공감으로 설득 성공", "비전 제시하면 통함", "사람들이 믿어주는 날"],
        "ENTJ": ["통솔력 최고인 날", "큰 그림 그리기 좋은 날", "결정하면 밀어붙여", "목표 향해 직진", "카리스마가 빛나는 날"],
    },
    
    # MBTI별 주의사항
    "mbti_warning": {
        "ISTJ": ["융통성 부족으로 충돌 주의", "너무 원칙만 고집하지 마", "변화에 열린 마음 필요", "완벽주의 내려놓기"],
        "ISFJ": ["남 일에 너무 신경 쓰지 마", "거절할 건 거절해", "자기 일 먼저 챙겨", "번아웃 주의"],
        "INFJ": ["혼자 끙끙대지 마", "오버 생각 주의", "완벽주의 내려놔", "현실 직시 필요"],
        "INTJ": ["고집 부리면 손해", "다른 의견도 들어봐", "감정 표현 필요할 수도", "융통성 발휘해"],
        "ISTP": ["무뚝뚝함 오해받기 쉬움", "팀워크도 신경 써", "혼자 처리하려 하지 마", "소통 한 번 더"],
        "ISFP": ["결정 미루지 마", "눈치 너무 보지 마", "의견 표현 필요해", "자기주장도 중요"],
        "INFP": ["현실 직시 필요", "감정에 휩쓸리지 마", "마감 시간 체크", "구체적 실행 필요"],
        "INTP": ["설명 길어지면 손해", "실행력 필요한 날", "딴 생각 주의", "결론부터 말해"],
        "ESTP": ["충동 결정 주의", "말 실수 조심", "디테일 놓치기 쉬움", "한 박자 쉬어가"],
        "ESFP": ["집중력 흐트러지기 쉬움", "수다 시간 조절", "중요한 거 놓치지 마", "우선순위 체크"],
        "ENFP": ["산만해지기 쉬운 날", "하나에 집중해", "약속 잊지 마", "마무리까지 신경 써"],
        "ENTP": ["논쟁 피해", "말 많으면 탈", "실행이 중요한 날", "끝까지 마무리해"],
        "ESTJ": ["너무 밀어붙이지 마", "팀원 감정도 챙겨", "독단적 결정 주의", "유연하게 대처"],
        "ESFJ": ["남 일에 너무 개입 말고", "자기 감정도 챙겨", "오지랖 주의", "에너지 분배 필요"],
        "ENFJ": ["다 책임지려 하지 마", "번아웃 주의", "거절도 필요해", "자기 시간 확보"],
        "ENTJ": ["강압적으로 보일 수 있음", "피드백 수용해", "팀원 의견도 들어", "속도 조절 필요"],
    },
    
    # 띠별 오늘의 기운
    "animal_energy": {
        "쥐": ["재빠른 판단력이 빛나는 날", "기회 포착 능력 상승", "정보력이 힘이 되는 날", "눈치 백단 발동", "작은 기회도 놓치지 마"],
        "소": ["우직한 추진력이 빛나는 날", "꾸준함이 결실 맺는 날", "인내가 보상받는 날", "묵묵히 가면 길이 열림", "끈기가 무기"],
        "호랑이": ["용맹함이 필요한 날", "과감한 결정 OK", "리더십 발휘 적기", "도전하면 성과", "당당하게 밀어붙여"],
        "토끼": ["재치가 빛나는 날", "위기 모면 능력 상승", "사교성으로 기회 잡아", "유연하게 대처", "부드러움이 강함"],
        "용": ["카리스마 폭발하는 날", "큰 일 도모하기 좋아", "주목받는 날", "스케일 크게 생각해", "자신감 충만"],
        "뱀": ["직감이 예리해지는 날", "통찰력으로 승부", "조용히 관찰하면 보임", "지혜가 빛나는 날", "신중함이 무기"],
        "말": ["열정 폭발하는 날", "활동적으로 움직여", "속도감 있게 처리", "에너지 넘치는 하루", "달리면 따라옴"],
        "양": ["온화함이 힘이 되는 날", "협력하면 시너지", "평화롭게 해결 가능", "조화가 답", "부드러움으로 승부"],
        "원숭이": ["재치와 유머가 통하는 날", "임기응변 능력 상승", "창의력 발휘 적기", "영리하게 대처", "유연함이 무기"],
        "닭": ["부지런함이 빛나는 날", "세심함으로 승부", "완벽주의가 통하는 날", "디테일이 차이 만듦", "성실함이 인정받음"],
        "개": ["신뢰가 쌓이는 날", "의리가 빛나는 날", "충직함이 인정받음", "믿음직한 모습 보여", "진심이 통함"],
        "돼지": ["복이 들어오는 날", "여유가 기회 만듦", "인복 터지는 날", "넉넉한 마음이 답", "행운이 따르는 날"],
    },
    
    # 띠별 주의사항
    "animal_warning": {
        "쥐": ["너무 계산적으로 보일 수 있음", "욕심 과하면 탈", "작은 이익에 큰 거 놓칠 수도"],
        "소": ["고집 피우면 손해", "융통성 필요한 날", "속도 조절 필요"],
        "호랑이": ["독단적 결정 주의", "성질 급하면 탈", "한 발 물러서기 필요"],
        "토끼": ["우유부단함 주의", "결단력 필요한 순간", "도망가지 말고 맞서"],
        "용": ["오만해 보일 수 있음", "팀워크 신경 써", "겸손함 필요"],
        "뱀": ["의심 과하면 기회 놓침", "너무 숨기지 마", "소통 한 번 더"],
        "말": ["급하면 실수", "끝까지 마무리 필요", "산만해지기 쉬움"],
        "양": ["우유부단함 주의", "자기주장도 필요해", "의존하지 마"],
        "원숭이": ["잔꾀 부리면 탈", "진정성 필요", "가벼워 보일 수 있음"],
        "닭": ["까다로워 보일 수 있음", "비판 줄이기", "완벽주의 내려놔"],
        "개": ["고지식해 보일 수 있음", "유연함 필요", "너무 직설적이면 탈"],
        "돼지": ["게을러 보일 수 있음", "결단력 필요", "우선순위 정해"],
    },
    
    # 별자리별 오전운
    "zodiac_morning": {
        "물병자리": ["창의적 아이디어 떠오르는 오전", "독특한 관점이 빛남", "혁신적 사고 발휘", "자유롭게 생각해도 OK"],
        "물고기자리": ["감성 충만한 오전", "직감이 잘 맞는 시간", "공감 능력 상승", "부드럽게 시작하면 좋아"],
        "양자리": ["에너지 충만한 오전", "첫 단추 잘 꿰는 시간", "주도적으로 시작해", "선제 행동 추천"],
        "황소자리": ["안정적으로 시작하는 오전", "차분하게 정리하기 좋아", "기초 작업 추천", "서두르지 마"],
        "쌍둥이자리": ["소통이 잘 되는 오전", "미팅하기 좋은 시간", "정보 수집 적기", "대화로 풀어가"],
        "게자리": ["팀 케어하기 좋은 오전", "분위기 파악 잘 됨", "배려가 돌아옴", "감정 교류 추천"],
        "사자자리": ["존재감 빛나는 오전", "발표/프레젠 적기", "주목받는 시간", "자신감 있게 나서"],
        "처녀자리": ["꼼꼼함이 빛나는 오전", "분석/검토 추천", "디테일 체크 적기", "완벽주의 발휘"],
        "천칭자리": ["균형 잡힌 판단의 오전", "조율하기 좋은 시간", "공정한 결정 가능", "중재 역할 추천"],
        "전갈자리": ["집중력 최고인 오전", "깊이 파고들기 좋아", "핵심 파악 적기", "몰입 추천"],
        "사수자리": ["긍정 에너지 충만한 오전", "새로운 도전 적기", "확장적 사고 OK", "낙관적으로 시작"],
        "염소자리": ["생산성 최고인 오전", "계획대로 실행 적기", "체계적 접근 추천", "목표 향해 집중"],
    },
    
    # 별자리별 오후운
    "zodiac_afternoon": {
        "물병자리": ["협업에서 시너지 나는 오후", "다른 관점 수용하면 좋아", "네트워킹 추천"],
        "물고기자리": ["마무리가 잘 되는 오후", "감성적 마무리 추천", "여운 남기는 시간"],
        "양자리": ["추진력 발휘하는 오후", "밀어붙이면 성과", "결단의 시간"],
        "황소자리": ["완성도 높이는 오후", "퀄리티 체크 적기", "마감 작업 추천"],
        "쌍둥이자리": ["정보 정리하는 오후", "보고/공유 추천", "멀티태스킹 OK"],
        "게자리": ["관계 다지는 오후", "1:1 대화 추천", "감사 표현 적기"],
        "사자자리": ["성과 정리하는 오후", "인정받는 시간", "셀프 PR 추천"],
        "처녀자리": ["최종 검토의 오후", "실수 잡아내는 시간", "꼼꼼 체크 추천"],
        "천칭자리": ["합의 이끄는 오후", "협상 추천", "윈윈 만들기 좋아"],
        "전갈자리": ["결론 내리는 오후", "핵심만 정리", "결단력 발휘"],
        "사수자리": ["계획 세우는 오후", "내일을 위한 준비", "큰 그림 그리기"],
        "염소자리": ["실적 정리하는 오후", "데이터 체크 추천", "보고 준비 적기"],
    },
    
    # 띠×별자리 궁합 (좋음/보통/주의 + 한줄 코멘트)
    "compatibility": {
        # 쥐
        ("쥐", "물병자리"): ("좋음", "영리함과 창의성의 시너지"),
        ("쥐", "물고기자리"): ("보통", "감성과 이성의 균형 필요"),
        ("쥐", "양자리"): ("좋음", "빠른 판단력 시너지"),
        ("쥐", "황소자리"): ("보통", "속도 차이 조절 필요"),
        ("쥐", "쌍둥이자리"): ("좋음", "정보력 최강 조합"),
        ("쥐", "게자리"): ("보통", "감정 교류 더 필요"),
        ("쥐", "사자자리"): ("주의", "주도권 충돌 가능"),
        ("쥐", "처녀자리"): ("좋음", "디테일 완벽 조합"),
        ("쥐", "천칭자리"): ("보통", "결정 속도 차이"),
        ("쥐", "전갈자리"): ("좋음", "통찰력 시너지"),
        ("쥐", "사수자리"): ("보통", "방향성 조율 필요"),
        ("쥐", "염소자리"): ("좋음", "목표 지향 완벽 조합"),
        # 소
        ("소", "물병자리"): ("주의", "고집 vs 자유 충돌"),
        ("소", "물고기자리"): ("보통", "속도 맞추면 OK"),
        ("소", "양자리"): ("주의", "추진 방식 차이"),
        ("소", "황소자리"): ("좋음", "안정감 최강 조합"),
        ("소", "쌍둥이자리"): ("주의", "변화 vs 고정 충돌"),
        ("소", "게자리"): ("좋음", "신뢰 기반 조합"),
        ("소", "사자자리"): ("보통", "리더십 조율 필요"),
        ("소", "처녀자리"): ("좋음", "꼼꼼함 시너지"),
        ("소", "천칭자리"): ("보통", "결정 방식 차이"),
        ("소", "전갈자리"): ("좋음", "끈기 시너지"),
        ("소", "사수자리"): ("주의", "속도 차이 큼"),
        ("소", "염소자리"): ("좋음", "실용주의 완벽 조합"),
        # 호랑이
        ("호랑이", "물병자리"): ("좋음", "혁신적 리더십"),
        ("호랑이", "물고기자리"): ("보통", "강함과 부드러움 균형"),
        ("호랑이", "양자리"): ("좋음", "용맹함 시너지"),
        ("호랑이", "황소자리"): ("주의", "주도권 충돌 가능"),
        ("호랑이", "쌍둥이자리"): ("보통", "방향성 맞추면 OK"),
        ("호랑이", "게자리"): ("보통", "보호 vs 독립 균형"),
        ("호랑이", "사자자리"): ("주의", "리더십 충돌 주의"),
        ("호랑이", "처녀자리"): ("보통", "디테일 보완 필요"),
        ("호랑이", "천칭자리"): ("좋음", "결단+균형 조합"),
        ("호랑이", "전갈자리"): ("좋음", "강인함 시너지"),
        ("호랑이", "사수자리"): ("좋음", "도전 정신 폭발"),
        ("호랑이", "염소자리"): ("보통", "목표 맞추면 강력"),
        # 토끼
        ("토끼", "물병자리"): ("좋음", "창의적 유연함"),
        ("토끼", "물고기자리"): ("좋음", "감성 시너지"),
        ("토끼", "양자리"): ("보통", "속도 조절 필요"),
        ("토끼", "황소자리"): ("좋음", "안정적 조화"),
        ("토끼", "쌍둥이자리"): ("좋음", "사교성 폭발"),
        ("토끼", "게자리"): ("좋음", "정서적 교감"),
        ("토끼", "사자자리"): ("보통", "자기주장 필요"),
        ("토끼", "처녀자리"): ("보통", "완벽주의 조절"),
        ("토끼", "천칭자리"): ("좋음", "조화로운 조합"),
        ("토끼", "전갈자리"): ("주의", "깊이 차이 조율"),
        ("토끼", "사수자리"): ("보통", "방향성 맞추기"),
        ("토끼", "염소자리"): ("보통", "목표 공유하면 OK"),
        # 용
        ("용", "물병자리"): ("좋음", "비전 시너지"),
        ("용", "물고기자리"): ("보통", "이상과 감성 균형"),
        ("용", "양자리"): ("좋음", "파워풀 조합"),
        ("용", "황소자리"): ("주의", "속도 차이 큼"),
        ("용", "쌍둥이자리"): ("좋음", "다재다능 시너지"),
        ("용", "게자리"): ("보통", "감정 교류 필요"),
        ("용", "사자자리"): ("주의", "주도권 경쟁"),
        ("용", "처녀자리"): ("보통", "디테일 보완 가능"),
        ("용", "천칭자리"): ("좋음", "균형 잡힌 리더십"),
        ("용", "전갈자리"): ("좋음", "카리스마 폭발"),
        ("용", "사수자리"): ("좋음", "확장 지향 완벽"),
        ("용", "염소자리"): ("보통", "목표 맞추면 강력"),
        # 뱀
        ("뱀", "물병자리"): ("보통", "독립성 충돌 가능"),
        ("뱀", "물고기자리"): ("좋음", "직감 시너지"),
        ("뱀", "양자리"): ("주의", "방식 차이 큼"),
        ("뱀", "황소자리"): ("좋음", "신중함 조합"),
        ("뱀", "쌍둥이자리"): ("주의", "소통 방식 차이"),
        ("뱀", "게자리"): ("보통", "감정 공유 필요"),
        ("뱀", "사자자리"): ("보통", "표현 방식 차이"),
        ("뱀", "처녀자리"): ("좋음", "분석력 시너지"),
        ("뱀", "천칭자리"): ("보통", "결정 방식 조율"),
        ("뱀", "전갈자리"): ("좋음", "통찰력 최강"),
        ("뱀", "사수자리"): ("주의", "깊이 vs 넓이"),
        ("뱀", "염소자리"): ("좋음", "전략적 조합"),
        # 말
        ("말", "물병자리"): ("좋음", "자유로운 에너지"),
        ("말", "물고기자리"): ("보통", "감성 균형 필요"),
        ("말", "양자리"): ("좋음", "열정 폭발"),
        ("말", "황소자리"): ("주의", "속도 차이 큼"),
        ("말", "쌍둥이자리"): ("좋음", "활발한 시너지"),
        ("말", "게자리"): ("보통", "안정 vs 자유"),
        ("말", "사자자리"): ("좋음", "에너지 시너지"),
        ("말", "처녀자리"): ("주의", "디테일 충돌"),
        ("말", "천칭자리"): ("보통", "균형 맞추기"),
        ("말", "전갈자리"): ("보통", "깊이 차이 조율"),
        ("말", "사수자리"): ("좋음", "모험 최강 조합"),
        ("말", "염소자리"): ("주의", "방식 차이 큼"),
        # 양
        ("양", "물병자리"): ("보통", "독립성 조율"),
        ("양", "물고기자리"): ("좋음", "감성 교감"),
        ("양", "양자리"): ("보통", "주도권 명확히"),
        ("양", "황소자리"): ("좋음", "평화로운 조합"),
        ("양", "쌍둥이자리"): ("보통", "소통 노력 필요"),
        ("양", "게자리"): ("좋음", "정서적 안정"),
        ("양", "사자자리"): ("보통", "지지 역할 명확히"),
        ("양", "처녀자리"): ("좋음", "섬세함 시너지"),
        ("양", "천칭자리"): ("좋음", "조화로운 균형"),
        ("양", "전갈자리"): ("주의", "깊이 차이"),
        ("양", "사수자리"): ("보통", "방향성 맞추기"),
        ("양", "염소자리"): ("보통", "실용성 공유"),
        # 원숭이
        ("원숭이", "물병자리"): ("좋음", "창의력 폭발"),
        ("원숭이", "물고기자리"): ("보통", "진정성 필요"),
        ("원숭이", "양자리"): ("좋음", "활력 시너지"),
        ("원숭이", "황소자리"): ("주의", "방식 차이"),
        ("원숭이", "쌍둥이자리"): ("좋음", "재치 최강 조합"),
        ("원숭이", "게자리"): ("보통", "감정 교류 필요"),
        ("원숭이", "사자자리"): ("좋음", "무대 장악 시너지"),
        ("원숭이", "처녀자리"): ("주의", "꼼꼼함 충돌"),
        ("원숭이", "천칭자리"): ("좋음", "사교성 폭발"),
        ("원숭이", "전갈자리"): ("주의", "진정성 의심"),
        ("원숭이", "사수자리"): ("좋음", "모험 시너지"),
        ("원숭이", "염소자리"): ("보통", "실용성 맞추기"),
        # 닭
        ("닭", "물병자리"): ("주의", "방식 차이 큼"),
        ("닭", "물고기자리"): ("보통", "감성 보완 필요"),
        ("닭", "양자리"): ("보통", "속도 조절"),
        ("닭", "황소자리"): ("좋음", "성실함 시너지"),
        ("닭", "쌍둥이자리"): ("주의", "디테일 충돌"),
        ("닭", "게자리"): ("보통", "감정 표현 필요"),
        ("닭", "사자자리"): ("보통", "인정 욕구 조율"),
        ("닭", "처녀자리"): ("좋음", "완벽주의 시너지"),
        ("닭", "천칭자리"): ("보통", "기준 맞추기"),
        ("닭", "전갈자리"): ("좋음", "집중력 시너지"),
        ("닭", "사수자리"): ("주의", "디테일 vs 큰그림"),
        ("닭", "염소자리"): ("좋음", "목표 지향 완벽"),
        # 개
        ("개", "물병자리"): ("보통", "가치관 맞추기"),
        ("개", "물고기자리"): ("좋음", "진심 교감"),
        ("개", "양자리"): ("보통", "충성 방향 명확히"),
        ("개", "황소자리"): ("좋음", "신뢰 기반 조합"),
        ("개", "쌍둥이자리"): ("주의", "진정성 의문"),
        ("개", "게자리"): ("좋음", "정서적 유대"),
        ("개", "사자자리"): ("좋음", "충성심 시너지"),
        ("개", "처녀자리"): ("좋음", "꼼꼼함 신뢰"),
        ("개", "천칭자리"): ("보통", "공정함 맞추기"),
        ("개", "전갈자리"): ("좋음", "깊은 신뢰"),
        ("개", "사수자리"): ("보통", "자유 vs 충성"),
        ("개", "염소자리"): ("좋음", "책임감 시너지"),
        # 돼지
        ("돼지", "물병자리"): ("보통", "방식 조율 필요"),
        ("돼지", "물고기자리"): ("좋음", "감성 충만"),
        ("돼지", "양자리"): ("보통", "에너지 맞추기"),
        ("돼지", "황소자리"): ("좋음", "여유 시너지"),
        ("돼지", "쌍둥이자리"): ("보통", "깊이 차이"),
        ("돼지", "게자리"): ("좋음", "편안한 조합"),
        ("돼지", "사자자리"): ("보통", "주도권 명확히"),
        ("돼지", "처녀자리"): ("보통", "완벽주의 조절"),
        ("돼지", "천칭자리"): ("좋음", "평화로운 조합"),
        ("돼지", "전갈자리"): ("보통", "깊이 맞추기"),
        ("돼지", "사수자리"): ("좋음", "낙관 시너지"),
        ("돼지", "염소자리"): ("보통", "실용성 공유"),
    },
    
    # 요일유형별 전략
    "day_type_morning": {
        "월요일": ["월요병 이겨내는 게 첫 미션", "천천히 워밍업 OK", "급한 일부터 체크만", "커피 한 잔의 여유 필수", "페이스 천천히 올려"],
        "평일": ["루틴대로 움직이면 돼", "오전에 중요한 것 먼저", "미팅 있으면 준비 철저히", "집중 업무 몰아서", "페이스 유지가 핵심"],
        "금요일": ["주말 앞두고 의욕 상승", "오전에 급한 거 처리해", "마감 체크 필수", "밀린 거 정리 적기", "오늘만 버티면 주말"],
        "연휴전날": ["들뜬 마음 진정시키고", "필수만 처리하고 정리", "인수인계 체크", "급한 불 먼저 꺼", "내일부터 쉰다 생각하며 버텨"],
        "주말": ["늦잠 OK 여유롭게", "하고 싶은 거 먼저", "평일 스트레스 해소", "리프레시 타임", "충전이 목표"],
        "공휴일": ["평일인데 쉬는 행운", "푹 쉬어도 되는 날", "죄책감 없이 여유", "재충전 적기", "다음을 위한 휴식"],
    },
    "day_type_afternoon": {
        "월요일": ["점심 후 늘어지기 쉬움", "오후 회의 집중", "내일 위한 세팅", "퇴근 시간 노려", "무리하지 마"],
        "평일": ["오후 3시가 고비", "루틴 업무 처리", "보고는 4시 전에", "마무리 준비", "페이스 유지"],
        "금요일": ["오후는 정리 모드", "주간 마무리 필수", "일찍 퇴근 노려봐", "다음 주 세팅", "주말 계획 세워"],
        "연휴전날": ["인수인계 마무리", "급한 것만 처리", "정리하고 퇴근", "연휴 모드 ON 준비", "마음은 이미 연휴"],
        "주말": ["하고 싶은 거 해", "약속 있으면 즐겨", "충분히 쉬어", "에너지 충전", "내일 걱정은 내일"],
        "공휴일": ["여유롭게 보내", "특별한 거 안 해도 OK", "쉬는 게 일", "다음 주 준비는 나중에", "오늘은 오늘만"],
    },
    "day_type_evening": {
        "월요일": ["일찍 퇴근해서 푹 쉬어", "무리한 약속 패스", "집에서 충전", "일찍 자는 게 승리", "내일을 위해 아껴"],
        "평일": ["적당한 저녁 약속 OK", "취미 활동 추천", "가벼운 운동", "내일 준비 가볍게", "충전과 활력 균형"],
        "금요일": ["불금 즐겨!", "약속 적극 추천", "주말 시작을 만끽", "스트레스 해소", "맘껏 놀아도 됨"],
        "연휴전날": ["연휴 시작 축하", "설렘 안고 귀가", "여행이면 출발 준비", "푹 쉴 준비", "내일부터 자유"],
        "주말": ["시간 마음대로", "늦게까지 OK", "하고 싶은 거 다 해", "푹 쉬어도 됨", "죄책감 없이"],
        "공휴일": ["공짜 휴일 만끽", "내일 출근이지만 괜찮아", "오늘 하루 선물", "재충전 완료", "감사한 하루"],
    },
    
    # 시간대별 인트로 메시지
    "time_intro": {
        "출근길": ["오늘 하루 미리보기", "출근길 운세 도착", "오늘의 작전 브리핑"],
        "오전": ["오전 집중 모드 ON", "지금 뭐 하면 좋을까", "오전 전략 체크"],
        "점심": ["점심시간 잠깐 쉬며", "오후를 위한 충전", "반환점 돌았다"],
        "오후": ["오후 전략 수정", "남은 시간 공략법", "마무리 준비 시작"],
        "퇴근후": ["오늘 하루 수고했어", "퇴근 후 힐링 타임", "내일을 위한 충전"],
    },
    
    # 계절/월별 감성
    "season_vibe": {
        "신년": ["새해 기운 충만! 새 출발 적기", "올해는 다를 거야", "새로운 다짐 세우기 좋은 때"],
        "봄": ["봄기운 솔솔, 새로운 시작 에너지", "설렘 가득한 시즌", "움츠렸던 기운 펼칠 때"],
        "초여름": ["활기찬 에너지 시즌", "야외 활동 추천", "열정 불태우기 좋은 때"],
        "장마": ["눅눅한 기운 주의", "실내 집중 추천", "우울함 날려버려"],
        "한여름": ["더위와의 전쟁", "에너지 관리 필수", "시원한 곳에서 충전"],
        "가을": ["결실의 계절", "마무리 짓기 좋은 때", "차분하게 정리하는 시즌"],
        "연말": ["한 해 마무리 시즌", "정산과 회고의 때", "송년 감성 물씬"],
    },
    
    # 날씨별 점심 팁
    "weather_lunch": {
        "맑음": ["야외 점심 추천! 햇살 충전", "산책 겸 멀리 가서 먹어", "기분 좋은 날씨 만끽"],
        "흐림": ["실내에서 든든하게", "따뜻한 메뉴 추천", "커피 한 잔 여유롭게"],
        "비": ["우산 챙겨서 가까운 데서", "따뜻한 국물이 진리", "비 오는 날 감성 점심"],
        "눈": ["미끄럼 주의하며 가까이서", "따뜻한 거 먹어야 해", "눈 구경하며 여유롭게"],
    },
    
    # 행운템 리스트
    "lucky_items": [
        "빨간 포스트잇", "파란 포스트잇", "노란 형광펜", "3색 볼펜", "검정 볼펜",
        "미니 선인장 화분", "작은 화분", "탕비실 종이컵", "머그컵", "텀블러 뚜껑",
        "모니터 스티커", "캐릭터 피규어", "손목 쿠션", "마우스 패드", "키보드 브러쉬",
        "블루라이트 안경", "안경닦이", "이어폰 케이스", "에어팟 케이스", "보조 배터리",
        "명함 지갑", "사원증 목걸이", "차키 고리", "손거울", "핸드크림",
        "립밤", "책상 달력", "포켓 수첩", "클립 홀더", "스테이플러",
    ],
    
    # 띠별 행운템 연결 이유
    "lucky_item_reason": {
        "쥐": "재빠른 {animal}띠에게 민첩함을 더해줄",
        "소": "우직한 {animal}띠의 끈기를 상징하는",
        "호랑이": "용맹한 {animal}띠의 기운을 북돋울",
        "토끼": "재치있는 {animal}띠의 행운을 부르는",
        "용": "강력한 {animal}띠의 카리스마를 높여줄",
        "뱀": "지혜로운 {animal}띠의 통찰력을 키워줄",
        "말": "열정적인 {animal}띠의 에너지를 채워줄",
        "양": "온화한 {animal}띠의 평화를 지켜줄",
        "원숭이": "영리한 {animal}띠의 재치를 살려줄",
        "닭": "부지런한 {animal}띠의 성실함을 빛내줄",
        "개": "충직한 {animal}띠의 신뢰를 높여줄",
        "돼지": "복 많은 {animal}띠의 행운을 배로 만들",
    },
    
    # 오늘의 변수 (랜덤 요소)
    "random_variable": [
        "엘리베이터에서 만나는 사람이 오늘의 키맨",
        "오후 3시에 뜻밖의 연락이 올 수도",
        "빨간색 보이면 일단 멈춰봐",
        "오늘 첫 번째로 마주친 동료가 힌트",
        "점심 메뉴 선택이 오후를 좌우함",
        "갑자기 떠오르는 아이디어 메모해둬",
        "창밖을 한 번 보면 영감이 올지도",
        "오늘 들은 노래 가사에 답이 있을 수도",
        "커피 마시는 타이밍이 중요한 날",
        "회의실 자리 선택이 운명을 가름",
        "오후에 예상치 못한 칭찬이 올지도",
        "복도에서 스치는 인연 주목",
        "오늘 받는 첫 메일에 힌트가",
        "탕비실에서 좋은 정보 들을 수도",
        "계단 이용하면 좋은 기운",
        "오른쪽에서 오는 기회 잡아",
        "점심 후 5분 명상이 오후를 바꿈",
        "오늘은 질문을 많이 하면 좋아",
        "메모장 첫 페이지에 행운이",
        "화분에 물 주면 좋은 일 생김",
        "오늘 처음 본 숫자가 행운의 숫자",
        "웃는 얼굴이 기회를 부름",
        "오후에 자리 정리하면 운 상승",
        "동료의 농담에 진짜 힌트가 숨어있음",
        "오늘은 먼저 인사하는 사람이 이김",
        "컴퓨터 바탕화면 바꾸면 기분 전환",
        "오래된 파일에서 필요한 거 발견할 수도",
        "의외의 사람에게서 도움 받을 날",
        "모니터 밝기 조절이 집중력 높임",
        "오늘은 왼손으로 뭔가 해보는 건?",
        "책상 위 물건 위치가 운을 바꿈",
        "오후 간식이 에너지를 좌우함",
        "오늘 신는 양말 색깔이 포인트",
        "예상 못한 회의가 기회될 수도",
        "퇴근길 평소와 다른 길로 가봐",
        "SNS에서 본 글이 힌트일 수도",
        "오늘은 고민 말고 바로 실행",
        "책상 서랍 정리하면 잃어버린 거 나옴",
        "동기와 대화에서 인사이트 얻을 날",
        "오늘 점심값 누가 내면 둘 다 행운",
    ],
    
    # 특수일 메시지
    "special_day": {
        "양력생일": ["🎂 오늘 양력 생일! 특별한 하루 되길", "생일 축하해! 오늘은 네가 주인공", "1년 중 가장 특별한 날, 행운 가득"],
        "음력생일": ["🎂 오늘 음력 생일! 전통적 행운의 날", "음력 생일 축하! 어른들 축복 가득", "진짜 생일 기운 충만한 날"],
        "공휴일": ["🎉 공휴일! 평일인데 쉬는 행운", "쉬는 날 만끽해!", "재충전의 날, 푹 쉬어"],
        "연휴전날": ["🌴 내일부터 연휴! 오늘만 버텨", "설렘 안고 마무리하는 날", "연휴 직전 특별한 기운"],
        "월초": ["📅 새 달의 시작! 이번 달 목표 세워봐", "월초 기운으로 새출발", "리셋하고 다시 시작"],
        "월말": ["📊 월말 정산 시즌! 마무리 잘 하자", "한 달 마무리하는 날", "정리하고 다음 달 준비"],
        "분기말": ["📈 분기 마감! 실적 정리 필수", "3개월 성과 점검 시기", "다음 분기 준비 시작"],
        "연초": ["🎊 새해 시작! 올해는 다를 거야", "1년 계획 세우기 최적기", "새해 기운 물씬"],
        "연말": ["🎄 한 해 마무리! 수고했어", "올해 회고하기 좋은 때", "내년을 위한 정리"],
    },
}

# --- 5. 유틸리티 함수 ---
@st.cache_data(ttl=1800)
def get_weather(nx, ny, district_name):
    try:
        base_date = datetime.datetime.now().strftime("%Y%m%d")
        base_time = (datetime.datetime.now() - datetime.timedelta(minutes=40)).strftime("%H00")
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {"serviceKey": WEATHER_API_KEY, "dataType": "JSON", "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny}
        res = requests.get(url, params=params, timeout=3).json()
        items = res['response']['body']['items']['item']
        data = {i['category']: i['obsrValue'] for i in items}
        pty, temp = int(data.get('PTY', 0)), data.get('T1H', '?')
        if pty == 0:
            icon, condition = "☀️", "맑음"
        elif pty in [1, 5]:
            icon, condition = "☔", "비"
        elif pty in [2, 6]:
            icon, condition = "🌨️", "눈"
        else:
            icon, condition = "☁️", "흐림"
        return icon, f"{temp}℃", condition
    except:
        return "📡", "수신불가", "흐림"

def get_lunar_date(date_obj):
    cal = KoreanLunarCalendar()
    cal.setSolarDate(date_obj.year, date_obj.month, date_obj.day)
    return cal.LunarIsoFormat()

def get_today_lunar():
    """오늘 날짜를 음력으로 변환"""
    today = datetime.date.today()
    cal = KoreanLunarCalendar()
    cal.setSolarDate(today.year, today.month, today.day)
    return (cal.lunarMonth, cal.lunarDay)

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
    target_year = year if date_obj >= get_ipchun_date(year) else year - 1
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[target_year % 12]

def get_day_type(date_obj):
    """요일 유형 반환: 월요일/금요일/평일/주말/공휴일/연휴전날"""
    kr_holidays = holidays.KR()
    tomorrow = date_obj + datetime.timedelta(days=1)
    
    # 공휴일 체크
    if date_obj in kr_holidays:
        return "공휴일", kr_holidays.get(date_obj)
    
    # 연휴 전날 체크 (내일이 공휴일이거나 주말)
    if tomorrow in kr_holidays or tomorrow.weekday() >= 5:
        if date_obj.weekday() < 5:  # 평일인 경우만
            return "연휴전날", None
    
    # 주말 체크
    if date_obj.weekday() >= 5:
        return "주말", None
    
    # 월요일/금요일 특별 취급
    if date_obj.weekday() == 0:
        return "월요일", None
    elif date_obj.weekday() == 4:
        return "금요일", None
    
    return "평일", None

def get_time_slot():
    """현재 시간대 반환"""
    hour = datetime.datetime.now().hour
    if 6 <= hour < 9:
        return "출근길"
    elif 9 <= hour < 12:
        return "오전"
    elif 12 <= hour < 14:
        return "점심"
    elif 14 <= hour < 18:
        return "오후"
    else:
        return "퇴근후"

def get_season(date_obj):
    """계절/시즌 반환"""
    month = date_obj.month
    day = date_obj.day
    
    # 연초 (1월 1-7일)
    if month == 1 and day <= 7:
        return "신년"
    # 연말 (12월 20-31일)
    elif month == 12 and day >= 20:
        return "연말"
    # 봄 (3-5월)
    elif 3 <= month <= 5:
        return "봄"
    # 장마 (6월 중순 - 7월 중순)
    elif (month == 6 and day >= 15) or (month == 7 and day <= 20):
        return "장마"
    # 초여름 (6월 초)
    elif month == 6 and day < 15:
        return "초여름"
    # 한여름 (7월 중순 - 8월)
    elif (month == 7 and day > 20) or month == 8:
        return "한여름"
    # 가을 (9-11월)
    elif 9 <= month <= 11:
        return "가을"
    # 기본
    else:
        return "봄"

def get_special_days(birth_date, today):
    """특수일 체크"""
    special = []
    
    # 양력 생일
    if birth_date.month == today.month and birth_date.day == today.day:
        special.append("양력생일")
    
    # 음력 생일 체크
    birth_lunar = get_lunar_date(birth_date)  # 생일의 음력 변환
    today_lunar_month, today_lunar_day = get_today_lunar()
    
    # 음력 생일에서 월/일 추출 (형식: YYYY-MM-DD)
    birth_lunar_parts = birth_lunar.split('-')
    if len(birth_lunar_parts) >= 3:
        birth_lunar_month = int(birth_lunar_parts[1])
        birth_lunar_day = int(birth_lunar_parts[2])
        if birth_lunar_month == today_lunar_month and birth_lunar_day == today_lunar_day:
            special.append("음력생일")
    
    # 공휴일
    kr_holidays = holidays.KR()
    if today in kr_holidays:
        special.append("공휴일")
    
    # 연휴 전날
    tomorrow = today + datetime.timedelta(days=1)
    if (tomorrow in kr_holidays or tomorrow.weekday() >= 5) and today.weekday() < 5:
        if "공휴일" not in special:
            special.append("연휴전날")
    
    # 월초 (1-3일)
    if today.day <= 3:
        special.append("월초")
    
    # 월말 (28-31일)
    if today.day >= 28:
        special.append("월말")
    
    # 분기말 (3, 6, 9, 12월의 마지막 주)
    if today.month in [3, 6, 9, 12] and today.day >= 25:
        special.append("분기말")
    
    # 연초 (1월 1-7일)
    if today.month == 1 and today.day <= 7:
        special.append("연초")
    
    # 연말 (12월 20-31일)
    if today.month == 12 and today.day >= 20:
        special.append("연말")
    
    return special

def display_card(column, icon, title, value):
    with column:
        st.markdown(f'<div class="info-card"><div class="big-icon">{icon}</div><div class="card-title">{title}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

def generate_fortune(mbti, zodiac, animal, birth_date, weather_condition, today):
    """템플릿 기반 운세 생성"""
    
    # 시드 설정 (같은 날 + 같은 조합 = 같은 결과)
    time_slot = get_time_slot()
    seed = hash(f"{today.strftime('%Y-%m-%d')}-{mbti}-{zodiac}-{animal}-{time_slot}") % (2**32)
    random.seed(seed)
    
    # 요일 유형
    day_type, holiday_name = get_day_type(today)
    
    # 계절
    season = get_season(today)
    
    # 특수일
    special_days = get_special_days(birth_date, today)
    
    # 띠×별자리 궁합
    compat_key = (animal, zodiac)
    compatibility = TEMPLATES["compatibility"].get(compat_key, ("보통", "균형 잡힌 하루"))
    compat_level, compat_comment = compatibility
    
    # === 운세 조합 시작 ===
    
    # 1. 한줄운세 (MBTI 기본 + 띠 기운 + 궁합 보정)
    mbti_fortune = random.choice(TEMPLATES["mbti_fortune"][mbti])
    animal_energy = random.choice(TEMPLATES["animal_energy"][animal])
    
    if compat_level == "좋음":
        main_fortune = f"{mbti_fortune}, {animal_energy}"
    elif compat_level == "주의":
        main_fortune = f"{mbti_fortune} (단, 오늘은 신중하게)"
    else:
        main_fortune = mbti_fortune
    
    # 2. 오전 팁 (요일유형 + 별자리 오전운)
    morning_day = random.choice(TEMPLATES["day_type_morning"][day_type])
    morning_zodiac = random.choice(TEMPLATES["zodiac_morning"][zodiac])
    
    # 3. 오후 팁 (요일유형 + 별자리 오후운)
    afternoon_day = random.choice(TEMPLATES["day_type_afternoon"][day_type])
    afternoon_zodiac = random.choice(TEMPLATES["zodiac_afternoon"][zodiac])
    
    # 4. 퇴근 팁 (요일유형)
    evening_tip = random.choice(TEMPLATES["day_type_evening"][day_type])
    
    # 5. 주의보 (MBTI + 띠 + 궁합)
    mbti_warning = random.choice(TEMPLATES["mbti_warning"][mbti])
    animal_warning = random.choice(TEMPLATES["animal_warning"][animal])
    
    if compat_level == "주의":
        warning = f"{mbti_warning}. 특히 오늘은 {compat_comment}"
    else:
        warning = f"{mbti_warning}. 또한 {animal_warning}"
    
    # 6. 점심 팁 (날씨)
    lunch_tip = random.choice(TEMPLATES["weather_lunch"].get(weather_condition, TEMPLATES["weather_lunch"]["흐림"]))
    
    # 7. 행운템
    lucky_item = random.choice(TEMPLATES["lucky_items"])
    lucky_reason = TEMPLATES["lucky_item_reason"][animal].format(animal=animal)
    
    # 8. 계절 감성
    season_vibe = random.choice(TEMPLATES["season_vibe"][season])
    
    # 9. 오늘의 변수 (완전 랜덤)
    random.seed()  # 시드 리셋해서 진짜 랜덤
    random_var = random.choice(TEMPLATES["random_variable"])
    
    # 10. 시간대별 인트로
    time_intro = random.choice(TEMPLATES["time_intro"][time_slot])
    
    # 11. 특수일 메시지
    special_messages = []
    for sp in special_days:
        if sp in TEMPLATES["special_day"]:
            special_messages.append(random.choice(TEMPLATES["special_day"][sp]))
    
    return {
        "main": main_fortune,
        "morning_day": morning_day,
        "morning_zodiac": morning_zodiac,
        "afternoon_day": afternoon_day,
        "afternoon_zodiac": afternoon_zodiac,
        "evening": evening_tip,
        "warning": warning,
        "lunch": lunch_tip,
        "lucky_item": lucky_item,
        "lucky_reason": lucky_reason,
        "season_vibe": season_vibe,
        "random_var": random_var,
        "time_intro": time_intro,
        "time_slot": time_slot,
        "day_type": day_type,
        "holiday_name": holiday_name,
        "compatibility": (compat_level, compat_comment),
        "special_days": special_days,
        "special_messages": special_messages,
    }

# --- 6. 메인 UI ---
with st.sidebar:
    st.header("📍 내 업무지구")
    selected_district = st.selectbox(
        "출근하는 곳",
        list(BUSINESS_DISTRICTS.keys()),
        index=4,
        help="날씨 정보를 가져올 업무지구를 선택하세요"
    )

district_info = BUSINESS_DISTRICTS[selected_district]
weather_icon, weather_text, weather_condition = get_weather(
    district_info["nx"], 
    district_info["ny"], 
    district_info["name"]
)

subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
weather_html = f"<span class='weather-badge'>{weather_icon} {district_info['name']} {weather_text}</span>"

st.markdown(f'<div class="title-container"><span class="main-title">오늘의 눈치 레이더</span>{weather_html}<div class="sub-title">{subtitle_text}</div><div class="engine-tag">Powered by Fortune Template Engine v3</div></div><hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

# 사용자 정보 입력
st.subheader("👤 내 정보")
c1, c2, c3 = st.columns([2, 1, 1])
mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]

with c1: 
    user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
with c2: 
    user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
with c3: 
    user_mbti = st.selectbox("내 MBTI", mbti_list)

# 카드 데이터 계산
u_l = get_lunar_date(user_birth)
u_z = get_zodiac_sign(user_birth.day, user_birth.month)
u_a = get_korean_zodiac(user_birth)

c1, c2, c3, c4 = st.columns(4)
display_card(c1, ZODIAC_ICONS.get(u_z), "내 별자리", u_z)
display_card(c2, ANIMAL_ICONS.get(u_a), "내 띠", f"{u_a}띠")
display_card(c3, "🌕", "음력 생일", u_l)
display_card(c4, weather_icon, f"{district_info['name']} 날씨", weather_text)

st.write("")
st.markdown("---")

# --- 7. 분석 버튼 ---
if st.button("🚀 전략 분석 시작", type="primary", use_container_width=True):
    
    today = datetime.date.today()
    now = datetime.datetime.now()
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]
    
    # 운세 생성
    fortune = generate_fortune(
        mbti=user_mbti,
        zodiac=u_z,
        animal=u_a,
        birth_date=user_birth,
        weather_condition=weather_condition,
        today=today
    )
    
    # 특수일 배너 (있을 경우)
    if fortune["special_messages"]:
        for msg in fortune["special_messages"]:
            st.markdown(f"""
            <div class="special-banner">
                <div class="special-banner-title">{msg}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 결과 표시
    st.success(f"✅ {fortune['time_intro']}")
    
    # 궁합 표시
    compat_level, compat_comment = fortune["compatibility"]
    compat_color = {"좋음": "🟢", "보통": "🟡", "주의": "🔴"}[compat_level]
    
    # 메인 카드
    r1, r2, r3, r4 = st.columns(4)
    display_card(r1, "🔮", "오늘 한줄", fortune["main"][:20] + "..." if len(fortune["main"]) > 20 else fortune["main"])
    display_card(r2, "🌅", "오전", fortune["morning_day"])
    display_card(r3, "🌆", "오후", fortune["afternoon_day"])
    display_card(r4, "🍀", "행운템", fortune["lucky_item"])
    
    # 오늘의 변수 박스
    st.markdown(f"""
    <div class="variable-box">
        <div class="variable-title">🎲 오늘의 변수</div>
        <div class="variable-content">"{fortune['random_var']}"</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 상세 분석
    st.markdown("---")
    st.markdown("### 📋 상세 전략 리포트")
    
    st.markdown(f"""
**🌤️ 오늘의 컨디션**: {fortune['season_vibe']}

**{compat_color} 띠×별자리 궁합**: {compat_level} - {compat_comment}

---

#### ⏰ 타임라인 전략

**🌅 오전 (출근~점심)**
> {fortune['morning_day']}

{u_z} 오전 기운: {fortune['morning_zodiac']}

**🍱 점심시간**
> {fortune['lunch']}

**🌆 오후 (점심 후~퇴근)**
> {fortune['afternoon_day']}

{u_z} 오후 기운: {fortune['afternoon_zodiac']}

**🌙 퇴근 후**
> {fortune['evening']}

---

#### ⚠️ 오늘의 주의보

> {fortune['warning']}

---

#### 🍀 행운템: {fortune['lucky_item']}

{fortune['lucky_reason']} 아이템이야.  
책상 위에 두거나, 오늘 하루 가까이 두면 좋은 기운이 올 거야!
""")
    
    # 공유하기
    st.markdown("---")
    st.subheader("📋 친구에게 공유하기")
    
    share_text = f"""[오늘의 눈치 레이더] {today.strftime('%m/%d')} ({weekday_kr}) {fortune['day_type']}

🔮 한줄: {fortune['main'][:30]}
🌅 오전: {fortune['morning_day']}
🌆 오후: {fortune['afternoon_day']}
🎲 변수: {fortune['random_var']}
🍀 행운템: {fortune['lucky_item']}

👉 나도 해보기: https://nunchi-radar.streamlit.app"""

    st.code(share_text, language="text")
    st.caption("👆 위 박스 오른쪽의 '복사(Copy)' 아이콘을 누르면 결과가 복사됩니다!")
