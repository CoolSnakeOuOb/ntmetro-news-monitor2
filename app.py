import streamlit as st
import collections
import textwrap
from serpapi import GoogleSearch
import streamlit.components.v1 as components
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
import pytz # 用於處理時區

# --- 1. 常數設定與金鑰讀取 ---
st.set_page_config(page_title="捷運輿情監測", page_icon="🚇", layout="wide")

SERPAPI_KEYS_TABLE = st.secrets.get("serpapi_keys", {})
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_KEYWORDS = "捷運, 輕軌, 環狀線, 新北, 軌道, 鐵路"
CATEGORIES = ["【新北】", "【同業】", "【其他】"]
DEFAULT_AI_PROMPT = """
你是新北捷運公司的輿情觀測員，你的任務是從每日新聞中，挑選出與公司業務最相關、或可能需要高層注意的事件。
請從以下新聞標題列表中，挑選出 3-5 則與「新北市」、「捷運工程」、「列車狀況」、「民眾抱怨」或「重大意外」最相關的新聞。
避免選擇標題內容相似的新聞。
"""

if 'filtered_news' not in st.session_state:
    st.session_state.filtered_news = collections.defaultdict(list)

# --- 2. 後端核心函式 ---

@st.cache_data(ttl=60)
def get_serpapi_account_info(api_key):
    if not api_key: return None
    try:
        r = requests.get(f"https://serpapi.com/account?api_key={api_key}")
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

def is_fresh_news(date_str):
    """
    聰明的日期過濾器：
    1. 保留相對時間 (ago, hour, min)
    2. 保留日期是「今天」或「昨天」的新聞
    3. 踢除更早以前的
    """
    if not date_str: return True # 沒有日期的通常是廣告或置頂，先保留或視情況過濾
    
    # 1. 檢查相對時間關鍵字 (最優先保留)
    relative_keywords = ["ago", "hour", "min", "sec", "前", "小時", "分", "秒", "Just now"]
    if any(k in date_str.lower() for k in relative_keywords):
        return True

    # 2. 檢查絕對日期 (處理如 12/22/2025)
    try:
        # 取得台灣現在時間
        tw_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(tw_tz)
        today_str = now.strftime("%m/%d")      # 例如 12/23
        yesterday_str = (now - timedelta(days=1)).strftime("%m/%d") # 例如 12/22
        
        # Google News 標準版回傳格式通常包含 "MM/DD/YYYY"
        # 我們簡單檢查字串裡有沒有包含「今天」或「昨天」的日期
        if today_str in date_str or yesterday_str in date_str:
            return True
            
        # 額外檢查：有時候是 "Dec 23" 這種格式
        today_str_b = now.strftime("%b %d") # Dec 23
        yesterday_str_b = (now - timedelta(days=1)).strftime("%b %d") # Dec 22
        if today_str_b in date_str or yesterday_str_b in date_str:
            return True

        return False # 如果有日期顯示，但既不是相對時間，也不是今昨兩天，那就過濾掉
    except:
        return True # 解析失敗的話，為了不誤殺，選擇保留

def fetch_news_from_api(api_key, keywords: list):
    raw_results = collections.defaultdict(list)
    for kw in keywords:
        params = {
            "engine": "google_news", 
            "q": kw, 
            "api_key": api_key, 
            "hl": "zh-tw", 
            "gl": "tw", 
            "num": 100, 
            "tbs": "qdr:d" 
        }
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            if "news_results" in data:
                for item in data["news_results"]:
                    title = item.get("title")
                    link = item.get("link")
                    date_str = item.get("date", "")
                    
                    # ✅ 雙重過濾：既要有標題連結，也要通過日期新鮮度檢查
                    if title and link and is_fresh_news(date_str):
                        raw_results[kw].append(item)
        except Exception as e:
            st.error(f"搜尋關鍵字 '{kw}' 時發生錯誤: {e}")
    return raw_results

@st.cache_data(ttl=86400)
def shorten_url(long_url: str):
    API_ENDPOINT = "http://tinyurl.com/api-create.php"
    try:
        response = requests.get(API_ENDPOINT, params={'url': long_url}, timeout=5)
        response.raise_for_status()
        shortened = response.text
        if shortened.startswith("http"):
            return shortened
        else:
            return long_url
    except requests.RequestException:
        return long_url

@st.cache_data(ttl=600)
def get_ai_recommendations(_articles_dict, prompt_template):
    if not GEMINI_API_KEY:
        st.error("尚未設定 Gemini API Key！")
        return []
    all_titles = [item['title'] for items in _articles_dict.values() for item in items]
    if not all_titles: return []
    full_prompt = (f"{prompt_template}\n\n以下是新聞標題列表：\n" + "\n".join(f"- {title}" for title in all_titles) + "\n\n請只回傳你挑選出的新聞標題，每個標題一行，不要有其他多餘的文字或編號。")
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(full_prompt)
        cleaned_titles = [title.strip().lstrip('- ') for title in response.text.strip().split('\n')]
        return cleaned_titles
    except Exception as e:
        st.error(f"請求 AI 推薦時發生錯誤: {e}")
        return []

# --- 3. Streamlit UI 介面 ---
left_margin, main_col, right_margin = st.columns([0.15, 0.7, 0.15])

with main_col:
    st.title("🚇 新北捷運輿情監測 (智能過濾版)")
    st.info("📢 **系統更新**：已啟用智能日期過濾，精準鎖定 24-48 小時內新聞，並修復來源顯示問題。", icon="✨")

    if not SERPAPI_KEYS_TABLE:
        st.error("錯誤：請在 .streamlit/secrets.toml 中設定 [serpapi_keys] 表格")
        st.stop()
    
    key_options = list(SERPAPI_KEYS_TABLE.keys())
    selected_account_name = st.selectbox("選擇要使用的 SerpApi 帳號", options=key_options)
    SERPAPI_API_KEY = SERPAPI_KEYS_TABLE[selected_account_name]

    account_info = get_serpapi_account_info(SERPAPI_API_KEY)
    if account_info and 'plan_searches_left' in account_info:
        searches_used = account_info['searches_per_month'] - account_info['plan_searches_left']
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("本月總額度", f"{account_info['searches_per_month']:,}")
        m_col2.metric("已用額度", f"{searches_used:,}")
        m_col3.metric("剩餘額度", f"{account_info['plan_searches_left']:,}", delta_color="inverse")
    
    with st.expander("📖 使用說明"):
        st.markdown("""
        1.  **抓取新聞**：抓取標準版 Google News，並自動過濾舊聞。
        2.  **AI 推薦**：AI 自動分析並勾選重要新聞。
        3.  **確認與匯出**：確認內容後產生 LINE 訊息。
        """)

    st.divider()
    st.header("Step 1: 設定與搜尋", anchor=False, divider="rainbow")
    keywords_input = st.text_input("🔍 輸入關鍵字（逗號分隔）", DEFAULT_KEYWORDS)
    
    b1_left, b1_mid, b1_right = st.columns([2.5, 1, 2.5])
    with b1_mid:
        fetch_button_pressed = st.button("📥 抓取新聞")

    if 'fetch_success_message' in st.session_state:
        st.success(st.session_state.fetch_success_message)
        del st.session_state.fetch_success_message

    if fetch_button_pressed:
        with st.spinner("正在抓取並進行智能過濾..."):
            keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
            if not keyword_list:
                st.warning("請輸入有效的關鍵字。")
            else:
                all_news = fetch_news_from_api(SERPAPI_API_KEY, keyword_list)
                st.session_state.filtered_news = all_news
                total_found = sum(len(v) for v in all_news.values())
                st.session_state.fetch_success_message = f"✅ 抓取完成！經智能過濾後共保留 {total_found} 則新聞。"
        st.rerun()

    if st.session_state.filtered_news:
        st.divider()
        st.header("Step 2: (可選) AI 智慧推薦", anchor=False, divider="rainbow")
        
        with st.expander("✍️ 編輯 AI 指令 (進階)"):
            st.text_area("您可以修改下方的 AI 指令：", value=DEFAULT_AI_PROMPT, key="ai_prompt_input", height=250)
        
        b2_left, b2_mid, b2_right = st.columns([2.5, 1, 2.5])
        with b2_mid:
            if st.button("🤖 AI 推薦"):
                raw_prompt = st.session_state.ai_prompt_input
                cleaned_prompt = textwrap.dedent(raw_prompt).strip()
                with st.spinner("🧠 AI 正在分析新聞重要性..."):
                    recommended = get_ai_recommendations(st.session_state.filtered_news, cleaned_prompt)
                    st.session_state.recommended_titles = recommended
                    
                    for kw, items in st.session_state.filtered_news.items():
                        for i, article in enumerate(items):
                            key_name = f"item_{kw}_{i}_select"
                            if article.get('title') in recommended:
                                st.session_state[key_name] = True

                    st.toast(f"AI 已推薦 {len(recommended)} 則新聞！", icon="💡")
        
        st.divider()
        st.header("Step 3: 勾選並分類您需要的新聞", anchor=False, divider="green")
        
        with st.form("news_selection_form"):
            selected_articles_data = []
            recommended_titles = st.session_state.get('recommended_titles', [])
            keyword_list_in_scope = [k.strip() for k in keywords_input.split(",") if k.strip()]
            
            for kw in keyword_list_in_scope:
                items = st.session_state.filtered_news.get(kw, [])
                if items:
                    st.subheader(f"🔸 {kw}")
                    for i, article in enumerate(items):
                        title = article.get('title', "無標題")
                        url = article.get('link', "#")
                        date = article.get('date', '未知時間')
                        
                        # ✅ 修正：解決未知來源問題
                        raw_source = article.get('source')
                        if isinstance(raw_source, dict):
                            source = raw_source.get('title') or raw_source.get('name') or "未知來源"
                        elif isinstance(raw_source, str):
                            source = raw_source
                        else:
                            source = "未知來源"

                        key_prefix = f"item_{kw}_{i}"
                        checkbox_key = f"{key_prefix}_select"
                        is_recommended = title in recommended_titles
                        
                        if checkbox_key not in st.session_state:
                            st.session_state[checkbox_key] = is_recommended

                        with st.container(border=True):
                            c1, c2, c3 = st.columns([0.08, 0.62, 0.3])
                            with c1:
                                is_selected = st.checkbox("", key=checkbox_key, label_visibility="collapsed")
                            with c2:
                                st.markdown(f"**{title}**")
                                st.caption(f"🔗 [{source}]({url}) | 🕒 {date}")
                            with c3:
                                category = st.radio("分類", options=CATEGORIES, key=f"{key_prefix}_cat", horizontal=True, label_visibility="collapsed")
                        
                        if is_selected:
                            article['category'] = category
                            selected_articles_data.append(article)
            
            submitted = st.form_submit_button("✅ 產生 Line 訊息", use_container_width=True)
            if submitted:
                st.session_state.report_data = selected_articles_data
                st.rerun()

    if 'report_data' in st.session_state:
        st.divider()
        st.header("Step 4: 複製以下訊息", anchor=False, divider="violet")
        
        report_articles = st.session_state.report_data
        if not report_articles:
            st.warning("⚠️ 您尚未勾選任何新聞。")
        else:
            grouped_news = collections.defaultdict(list)
            for item in report_articles:
                grouped_news[item.get('category', "【其他】")].append(item)
            
            result_msg = "各位長官、同仁早安，\n今日新聞輿情連結如下：\n\n"
            for category in CATEGORIES:
                if category in grouped_news:
                    result_msg += f"{category}\n"
                    for item in grouped_news[category]:
                        short_url = shorten_url(item['link'])
                        result_msg += f"{item['title']}\n{short_url}\n\n"

            st.text_area("📋 LINE 訊息內容", result_msg.strip(), height=400)
            
            js_safe_msg = result_msg.strip().replace('`','\\`').replace('\\','\\\\').replace('$', '\\$')
            components.html(f"""
                <div style="text-align: center;">
                    <button onclick="copyText()">📋 複製到剪貼簿</button>
                </div>
                <script>
                function copyText() {{
                    navigator.clipboard.writeText(`{js_safe_msg}`).then(
                        () => alert("✅ 已複製！"),
                        () => alert("❌ 複製失敗")
                    );
                }}
                </script>
                <style> 
                    button {{ font-size:16px; padding:8px 16px; margin-top:10px; border-radius: 5px; border: 1px solid #ccc; cursor: pointer; background-color: #f0f2f6;}} 
                    button:hover {{ background-color: #e0e2e6; }}
                </style>
            """, height=80)
        

        








