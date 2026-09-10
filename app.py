import os
import time
from datetime import datetime
import streamlit as st
import feedparser
from google import genai

# Page configuration
st.set_page_config(
    page_title="Stock News & Disclosure AI Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar UI
st.sidebar.title("📈 Stock News AI Config")
st.sidebar.write("Configure RSS sources for media & disclosures.")

# Streamlit Secrets에서 API Key 자동 로드 시도
secrets_key = st.secrets.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Gemini API Key", 
    value=secrets_key, 
    type="password", 
    help="Enter your Google Gemini API Key"
)

if api_key_input:
    st.sidebar.success("🔑 Gemini API Key configured")
else:
    st.sidebar.warning("⚠️ No Gemini API Key provided. AI analysis will be disabled until a key is added.")

st.sidebar.subheader("RSS Feed Sources")

# 이미지 및 국내 주요 증권/경제 매체/공시 피드 전체 반영
categories = {
    "공시 및 증시 이슈 (DART/KRX/키움)": "https://news.google.com/rss/search?q=%EB%8B%A4%ED%8A%B8+%EA%B8%88%EC%9C%B5%EA%B0%90%EB%8F%85%EC%9B%90+%EA%B3%B0%EC%8B%9C+OR+%ED%95%9C%EA%B5%AD%EA%B1%B0%EB%9E%98%EC%86%8C&hl=ko&gl=KR&ceid=KR:ko",
    "인포스탁 / IR GO (증시재료)": "https://news.google.com/rss/search?q=site:infostock.co.kr+OR+site:irgo.co.kr&hl=ko&gl=KR&ceid=KR:ko",
    "한경뉴스 (한국경제)": "https://www.hankyung.com/feed/all-news",
    "이데일리": "https://news.google.com/rss/search?q=site:edaily.co.kr&hl=ko&gl=KR&ceid=KR:ko",
    "연합뉴스": "https://www.yna.co.kr/rss/news.xml",
    "머니투데이": "https://news.google.com/rss/search?q=site:mt.co.kr&hl=ko&gl=KR&ceid=KR:ko",
    "이투데이": "https://news.google.com/rss/search?q=site:etoday.co.kr&hl=ko&gl=KR&ceid=KR:ko",
    "뉴스핌": "https://news.google.com/rss/search?q=site:newspim.com&hl=ko&gl=KR&ceid=KR:ko",
    "아시아경제": "https://news.google.com/rss/search?q=site:asiae.co.kr&hl=ko&gl=KR&ceid=KR:ko",
    "뉴스토마토": "https://news.google.com/rss/search?q=site:newstomato.com&hl=ko&gl=KR&ceid=KR:ko",
    "매일경제": "https://www.mk.co.kr/rss/30000001/",
    "헤럴드경제": "https://news.google.com/rss/search?q=site:biz.heraldcorp.com&hl=ko&gl=KR&ceid=KR:ko",
    "조선비즈": "https://news.google.com/rss/search?q=site:biz.chosun.com&hl=ko&gl=KR&ceid=KR:ko",
    "서울경제": "https://www.sedaily.com/rss/",
    "파이낸셜뉴스": "https://news.google.com/rss/search?q=site:fnnews.com&hl=ko&gl=KR&ceid=KR:ko",
    "조세일보 / 딜사이트 / 컨슈머타임스": "https://news.google.com/rss/search?q=site:joseilbo.com+OR+site:dealsite.co.kr+OR+site:cstimes.com&hl=ko&gl=KR&ceid=KR:ko",
    "해외투자정보 (글로벌 증시)": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"
}

selected_categories = st.sidebar.multiselect(
    "Select Feeds",
    options=list(categories.keys()),
    default=list(categories.keys())
)

articles_per_feed = st.sidebar.slider("Articles per feed", 1, 10, 5)

# Main UI
st.title("📈 증권/경제 전 매체 통합 상장사 파급력 AI 분석기")
st.caption("공시, 인포스탁, 이데일리, 머니투데이, 한경, 매경 등 전 증권 매체 뉴스를 수집하여 국내 상장사 연관성을 심층 분석합니다.")

col1, col2 = st.columns([1, 2])

with col1:
    fetch_button = st.button("🔄 증권 전 매체 뉴스/공시 수집 및 AI 분석", type="primary", use_container_width=True)

if fetch_button or 'news_data' in st.session_state:
    if fetch_button:
        all_articles = []
        for cat in selected_categories:
            feed_url = categories[cat]
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:articles_per_feed]:
                all_articles.append({
                    "category": cat,
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link", "#"),
                    "published": entry.get("published", "No Date"),
                    "source": entry.get("source", {}).get("title", cat)
                })
        st.session_state['news_data'] = all_articles

    articles = st.session_state.get('news_data', [])

    if api_key_input and fetch_button:
        try:
            client = genai.Client(api_key=api_key_input)
            
            prompt = f"""
            아래는 증권 전문 매체(인포스탁, 이데일리, 머니투데이, 한경, 매경, 조선비즈, 딜사이트 등) 및 공시 피드에서 수집된 실시간 뉴스 목록입니다:
            {articles}

            이 뉴스 및 공시 데이터를 종합 분석하여 **한국 증시(KOSPI/KOSDAQ) 상장 기업 및 테마주** 관점에서 심층 리포트를 작성해 주세요:

            1. **🔥 핵심 증시 재료/공시 및 연관 한국 상장사 (TOP 5)**
               - 수집된 정보 중 주가 변동성이 클 것으로 예상되는 핵심 이슈 5가지를 선별해 주세요.
               - 각 항목별로 **[포착된 뉴스/공시 출처]**, **[관련 한국 상장 기업명 및 테마주]**, **[재료 성격: 호재(긍정) / 악재(부정) / 중립]**을 구체적으로 명시해 주세요.

            2. **⏱️ 재료 지속성 및 영향 기간 예측**
               - 포착된 이슈들이 시장에 파급력을 줄 기간을 추정해 주세요.
               - **단기 재료(1~3일)**, **중기 모멘텀(1~4주)**, **장기 구조적 변수(수개월 이상)** 구분을 명확히 하고 논리적 근거를 작성해 주세요.

            3. **📊 산업 섹터별 연관 종목 및 예상 영향 상세**
               - [반도체/IT/전자], [2차전지/친환경], [바이오/제약], [금융/원자재/건설/기타] 등 주요 산업 섹터별로 영향 분석을 정리해 주세요.

            4. **⚠️ 리스크 요인 및 투자 주의사항**
               - 공시 변동, 단기 수급과열, 글로벌 변동성 등 주의해야 할 핵심 투자 리스크를 정리해 주세요.

            보고서는 증권사 리서치 센터의 최신 데일리 투자 전략 보고서 형식으로 작성해 주세요.
            """
            
            with st.spinner("Gemini AI가 증권 전 매체 뉴스를 바탕으로 상장사 파급력을 심층 분석 중입니다..."):
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt
                )
                
                st.subheader("🤖 AI 증권 전 매체 뉴스 & 공시 상장사 영향 분석 보고서")
                st.markdown(response.text)
                st.divider()

        except Exception as e:
            st.error(f"Gemini API Error: {e}")

    # Display Raw News Items
    st.subheader("📰 수집된 증권 매체 및 공시 헤드라인")
    st.write(f"총 {len(articles)}건의 기사 수집 완료 ({len(selected_categories)}개 카테고리).")

    for cat in selected_categories:
        cat_articles = [a for a in articles if a["category"] == cat]
        if cat_articles:
            with st.expander(f"📁 {cat} ({len(cat_articles)}건)", expanded=True):
                for item in cat_articles:
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.caption(f"🏛️ 출처: {item['source']} | 🕒 수집 시각: {item['published']}")
                    st.markdown("---")
