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

# Custom CSS for Streamlit dashboard styling
st.markdown("""
<style>
    .reportview-container {
        margin-top: -2em;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .hot-issue-badge {
        background-color: #ef4444;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .source-tag {
        color: #64748b;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Google News RSS Feeds definition
RSS_FEEDS = {
    "US Top News": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "Global Economy": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "World Tech": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "South Korea Top News": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
}

# Sidebar settings
st.sidebar.title("🌐 News AI Config")
st.sidebar.markdown("Configure RSS ingestion & Gemini AI parameters.")

# 1. API Key handling
default_api_key = os.environ.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Gemini API Key",
    value=default_api_key,
    type="password",
    help="Enter your Google Gemini API key. Defaults to GEMINI_API_KEY environment variable if present."
)

active_api_key = api_key_input.strip() or default_api_key

if not active_api_key:
    st.sidebar.warning("⚠️ No Gemini API Key provided. AI analysis will be disabled until a key is added.")
else:
    st.sidebar.success("🔑 Gemini API Key configured")

# 2. Category selection
selected_categories = st.sidebar.multiselect(
    "RSS Feed Categories",
    options=list(RSS_FEEDS.keys()),
    default=list(RSS_FEEDS.keys()),
    help="Select which Google News RSS streams to monitor."
)

# 3. Refresh Interval
refresh_interval = st.sidebar.selectbox(
    "Auto-Refresh Interval",
    options=["Manual only", "1 minute", "5 minutes", "15 minutes"],
    index=0,
    help="Automated real-time background polling interval."
)

articles_per_feed = st.sidebar.slider(
    "Articles per feed (max 5 recommended)",
    min_value=3,
    max_value=10,
    value=5
)

# Main layout header
st.title("🌐 Real-time Global News AI Analyst")
st.caption("Automated Google News RSS ingestion & Gemini 2.5 Flash intelligence briefing in Korean.")

# Fetch & parse RSS news
def fetch_news_feed(feed_name, url, limit=5):
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return {"error": f"Failed to parse RSS feed from {url}"}
        
        articles = []
        for entry in feed.entries[:limit]:
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '#')
            published = getattr(entry, 'published', getattr(entry, 'updated', 'Recent'))
            
            # Extract source
            source = "Google News"
            if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                source = entry.source.title
            elif ' - ' in title:
                parts = title.rsplit(' - ', 1)
                title = parts[0].strip()
                source = parts[1].strip()
                
            articles.append({
                "feed": feed_name,
                "title": title,
                "link": link,
                "published": published,
                "source": source
            })
        return articles
    except Exception as e:
        return {"error": str(e)}

# Analyze news with Gemini
def analyze_with_gemini(all_articles, api_key):
    if not api_key:
        return None, "Gemini API key is required to perform AI analysis."
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Prepare text payload
        articles_text = ""
        for idx, art in enumerate(all_articles, 1):
            articles_text += f"[{idx}] Feed: {art['feed']} | Source: {art['source']} | Date: {art['published']}\nTitle: {art['title']}\nLink: {art['link']}\n\n"

        prompt = f"""
당신은 실시간 글로벌 뉴스 분석 및 정보 브리핑을 담당하는 수석 국제 전문 AI 분석가입니다.
다음은 Google News RSS 피드에서 방금 수집된 최신 글로벌 뉴스 헤드라인 목록입니다:

{articles_text}

다음 3가지 요구사항에 따라 명확하고 가독성 높은 한국어 마크다운(Markdown) 보고서를 작성해주세요:

### 1. 🔥 글로벌 TOP 3 핫이슈 (TOP 3 Global Hot Issues)
- 수집된 기사들 전체에서 지금 전 세계가 가장 주목해야 할 핵심 이슈 3가지를 선정하세요.
- 각 이슈마다:
  - 이슈 제목 (한국어 요약)
  - 발생 맥락 및 선정 이유 (2~3문장)
  - 영향권 및 관련 분야 (예: 정치, 글로벌 공급망, IT 빅테크 등)

### 2. 🗂️ 4대 핵심 분야별 브리핑 (Categorized Briefings)
헤드라인들을 아래 4가지 분야로 분류하고, 각 분야의 핵심 기사별로 정확히 '한 줄 한국어 요약(1-sentence Korean summary)'을 제공하세요:
- 🏛️ **정치 (Politics)**: 외교, 안보, 정부 정책 및 국제 관계
- 📈 **경제 (Economy)**: 금융, 증시, 환율, 무역, 원자재, 기업 실적
- 💻 **기술 (Tech)**: AI, 반도체, IT 빅테크, 차세대 혁신 기술
- 🌍 **일반 / 사회 (General)**: 환경, 문화, 사건사고, 기타 주요 소식

### 3. 🌐 외신 주요 헤드라인 한국어 번역 (Accurate Korean Translations)
- 수집된 영문/외국어 헤드라인 중 중요도가 높은 주요 기사들의 원문 제목과 자연스럽고 정확한 한국어 번역본을 매칭하여 표(Table) 또는 리스트로 제시하세요.
  - 형식: 원문 헤드라인 | 한국어 번역 | 언론사

모든 결과는 전문적이면서도 빠르고 직관적으로 파악할 수 있도록 볼드체, 불릿, 이모지, 마크다운 표를 활용하여 정갈하게 포맷팅해주세요.
"""

        # Attempt gemini-2.5-flash, with automatic fallback to gemini-3.8-flash if retired
        try:
            response = client.models.generateContent(
                model="gemini-2.5-flash",
                contents=prompt
            )
        except Exception as model_err:
            if "gemini-2.5-flash" in str(model_err) or "NOT_FOUND" in str(model_err):
                response = client.models.generateContent(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
            else:
                raise model_err

        return response.text, None
    except Exception as e:
        return None, f"Gemini API Error: {str(e)}"

# Manual trigger button
col1, col2 = st.columns([2, 5])
with col1:
    fetch_btn = st.button("🔄 Fetch & Analyze News", type="primary", use_container_width=True)

with col2:
    if "last_updated" in st.session_state:
        st.info(f"Last updated: {st.session_state['last_updated']}")

# Execute fetch & analyze
if fetch_btn or ("news_data" not in st.session_state and selected_categories):
    if not selected_categories:
        st.warning("Please select at least one RSS feed category from the sidebar.")
    else:
        with st.spinner("Fetching latest Google News RSS feeds..."):
            collected_articles = []
            errors = []
            for cat in selected_categories:
                feed_url = RSS_FEEDS[cat]
                res = fetch_news_feed(cat, feed_url, limit=articles_per_feed)
                if isinstance(res, dict) and "error" in res:
                    errors.append(f"{cat}: {res['error']}")
                else:
                    collected_articles.extend(res)
            
            st.session_state["articles"] = collected_articles
            st.session_state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if errors:
                for err in errors:
                    st.error(f"RSS Ingestion Warning: {err}")

        # Gemini Analysis
        if collected_articles and active_api_key:
            with st.spinner("Analyzing news with Gemini 2.5 Flash..."):
                analysis_text, err = analyze_with_gemini(collected_articles, active_api_key)
                if err:
                    st.error(err)
                    st.session_state["analysis"] = None
                else:
                    st.session_state["analysis"] = analysis_text
        elif not active_api_key:
            st.warning("Gemini API Key is not set. Showing collected RSS feeds without AI analysis.")

# Display AI Analysis Results (Top Markdown Cards)
if "analysis" in st.session_state and st.session_state["analysis"]:
    st.markdown("## 📊 Gemini Intelligence Briefing")
    st.markdown(st.session_state["analysis"])
    st.divider()

# Display Raw Collected RSS News Items (Collapsible Expanders)
if "articles" in st.session_state and st.session_state["articles"]:
    st.markdown("## 📰 Collected RSS News Headlines")
    st.caption(f"Total {len(st.session_state['articles'])} articles ingested across {len(selected_categories)} feeds.")

    # Group by category
    for cat in selected_categories:
        cat_articles = [a for a in st.session_state["articles"] if a["feed"] == cat]
        with st.expander(f"📁 {cat} ({len(cat_articles)} items)", expanded=True):
            if not cat_articles:
                st.write("No articles retrieved for this category.")
            else:
                for item in cat_articles:
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.markdown(f"<span class='source-tag'>🏛️ Source: {item['source']} | 🕒 Published: {item['published']}</span>", unsafe_allow_html=True)
                    st.markdown(f"[🔗 Read original article]({item['link']})")
                    st.markdown("---")
