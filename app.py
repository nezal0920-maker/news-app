import os
import time
from datetime import datetime
import streamlit as st
import feedparser
from google import genai

# Page configuration
st.set_page_config(
    page_title="Global News AI Analyst",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar UI
st.sidebar.title("🌐 News AI Config")
st.sidebar.write("Configure RSS ingestion & Gemini AI parameters.")

api_key_input = st.sidebar.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API Key")

if api_key_input:
    st.sidebar.success("🔑 Gemini API Key configured")
else:
    st.sidebar.warning("⚠️ No Gemini API Key provided. AI analysis will be disabled until a key is added.")

st.sidebar.subheader("RSS Feed Categories")
categories = {
    "US Top News": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "Global Economy": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "World Tech": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "South Korea Top News": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
}

selected_categories = st.sidebar.multiselect(
    "Select Feeds",
    options=list(categories.keys()),
    default=list(categories.keys())
)

articles_per_feed = st.sidebar.slider("Articles per feed", 1, 10, 5)

# Main UI
st.title("🌐 Real-time Global News AI Analyst")
st.caption("Automated Google News RSS ingestion & Gemini Intelligence briefing in Korean.")

col1, col2 = st.columns([1, 2])

with col1:
    fetch_button = st.button("🔄 Fetch & Analyze News", type="primary", use_container_width=True)

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
            아래는 실시간 수집된 주요 글로벌 뉴스 헤드라인 목록입니다:
            {articles}

            다음 요구사항에 맞추어 한국어로 핵심 뉴스 브리핑을 작성해 주세요:
            1. **글로벌 TOP 3 핫이슈**: 가장 중요한 주요 이슈 3가지를 선정하고 각각 2문장 내외로 배경과 함께 설명해 주세요.
            2. **카테고리별 요약**: [정치/외교], [경제/경영], [IT/기술], [사회/일반] 카테고리로 분류하여 핵심 기사를 1문장씩 한국어로 요약해 주세요.
            3. 매끄럽고 명확한 어조의 보고서 형식으로 작성해 주세요.
            """
            
            with st.spinner("Gemini AI가 실시간 뉴스를 분석 중입니다..."):
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
                
                st.subheader("🤖 AI 실시간 글로벌 뉴스 브리핑")
                st.markdown(response.text)
                st.divider()

        except Exception as e:
            st.error(f"Gemini API Error: {e}")

    # Display Raw News Items
    st.subheader("📰 Collected RSS News Headlines")
    st.write(f"Total {len(articles)} articles ingested across {len(selected_categories)} feeds.")

    for cat in selected_categories:
        cat_articles = [a for a in articles if a["category"] == cat]
        if cat_articles:
            with st.expander(f"📁 {cat} ({len(cat_articles)} items)", expanded=True):
                for item in cat_articles:
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.caption(f"🏛️ Source: {item['source']} | 🕒 Published: {item['published']}")
                    st.markdown("---")
