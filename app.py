import streamlit as st
import collections
from serpapi import GoogleSearch
import streamlit.components.v1 as components
import requests # 新增 import

# --- Setup: API Key & Core Functions ---
SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY")

# 【全新】查詢 SerpApi 帳戶剩餘額度的函數
@st.cache_data(ttl=600) # 使用快取，每 10 分鐘(600秒)才重新抓取一次
def get_serpapi_account_info(api_key):
    """呼叫 SerpApi 的帳戶 API，並回傳帳戶資訊。"""
    if not api_key:
        return None
    try:
        response = requests.get(f"https://serpapi.com/account?api_key={api_key}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def fetch_news_from_serpapi(keywords: list):
    """為每個關鍵字呼叫 google_news API，並回傳格式統一的結果。"""
    # ... (此函數與前一版完全相同，此處省略以節省篇幅)
    results = collections.defaultdict(list)
    if not SERPAPI_API_KEY:
        st.error("錯誤：請在 .streamlit/secrets.toml 中設定您的 SERPAPI_API_KEY")
        return results
    for kw in keywords:
        params = { "engine": "google_news", "q": kw, "api_key": SERPAPI_API_KEY, "hl": "zh-tw", "gl": "tw", "tbs": "qdr:d", "num": 20 }
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            if "news_results" in data:
                for item in data["news_results"]:
                    if item.get("title") and item.get("link"):
                        results[kw].append({
                            "title": item.get("title"), "url": item.get("link"), "source": item.get("source"), "date": item.get("date")
                        })
        except Exception as e:
            st.error(f"搜尋關鍵字 '{kw}' 時發生錯誤: {e}")
    return results


# --- Streamlit UI ---
st.set_page_config(page_title="捷運輿情工具", page_icon="🚇", layout="wide")
st.title("📰 新北捷運輿情工具")

# 【核心修改】在標題下方顯示 API 額度資訊
if SERPAPI_API_KEY:
    account_info = get_serpapi_account_info(SERPAPI_API_KEY)
    if account_info and 'plan_searches_left' in account_info:
        st.info(f"本月剩餘搜尋額度： {account_info['plan_searches_left']} / {account_info['searches_per_month']}")
    else:
        st.warning("無法獲取 API 額度資訊，請確認您的 API 金鑰是否正確。")

with st.expander("📖 使用說明"):
    st.markdown("""
    1.  **輸入關鍵字**：用逗號分隔。
    2.  **抓取新聞**：點擊按鈕後，程式會抓取過去一天內的相關新聞。
    3.  **勾選與分類**：從結果中挑選您需要的文章。
    4.  **產生報表**：產生最終的 LINE 格式訊息。
    """)

# ... (以下所有程式碼與前一版完全相同，為求完整故全部提供)
if 'news_results' not in st.session_state:
    st.session_state.news_results = collections.defaultdict(list)
if 'submitted_data' not in st.session_state:
    st.session_state.submitted_data = None

default_keywords = "捷運, 輕軌, 環狀線, 新北, 軌道, 鐵路"
keywords_input = st.text_input("🔍 輸入關鍵字（逗號分隔）", default_keywords)

if st.button("📥 抓取 24 小時內新聞"):
    keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
    if not keyword_list:
        st.warning("請輸入有效的關鍵字。")
    elif not SERPAPI_API_KEY:
        st.error("請先在 .streamlit/secrets.toml 中設定您的 SERPAPI_API_KEY。")
    else:
        with st.spinner("🔄 正在從 Google News 抓取中..."):
            st.session_state.news_results = fetch_news_from_serpapi(keyword_list)
            st.session_state.submitted_data = None
        
        total_found = sum(len(v) for v in st.session_state.news_results.values())
        st.success(f"✅ 抓取完成！總共找到了 {total_found} 則相關新聞。")

# --- Step 2: Selection Form ---
if st.session_state.news_results:
    st.header("Step 2: 勾選並分類您需要的新聞")
    with st.form("news_selection_form"):
        selected_articles_data = []
        categories = ["【新北】", "【同業】", "【其他】"]
        keyword_list_in_scope = [k.strip() for k in keywords_input.split(",") if k.strip()]

        for kw in keyword_list_in_scope:
            items = st.session_state.news_results.get(kw, [])
            if items:
                st.subheader(f"🔸 {kw}")
                for i, article in enumerate(items):
                    key = f"select_{kw}_{i}"
                    title = article.get('title', "無標題")
                    url = article.get('url', "#")
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        is_selected = st.checkbox(f"[{title}]({url})", key=key, help=f"來源：{article.get('source', '未知')} - 發布於: {article.get('date', '未知')}")
                    with col2:
                        category = st.radio("分類", options=categories, key=f"cat_{kw}_{i}", horizontal=True, label_visibility="collapsed")
                    if is_selected:
                        article['category'] = category
                        selected_articles_data.append(article)
        
        submitted = st.form_submit_button("✅ 產生 Line 訊息")
        if submitted:
            st.session_state.submitted_data = selected_articles_data

# --- Step 3: Report Generation ---
if st.session_state.submitted_data is not None:
    st.header("Step 3: 複製以下訊息")
    selected_articles_data = st.session_state.submitted_data
    if not selected_articles_data:
        st.warning("⚠️ 您沒有勾選任何新聞")
    else:
        grouped_news = collections.defaultdict(list)
        for item in selected_articles_data:
            category = item.get('category', "【其他】")
            grouped_news[category].append(item)
        
        result_msg = "各位長官、同仁早安，\n今日新聞輿情連結如下：\n\n"
        category_order = ["【新北】", "【同業】", "【其他】"]
        for category in category_order:
            if category in grouped_news:
                result_msg += f"{category}\n"
                for item in grouped_news[category]:
                    result_msg += f"{item['title']}\n{item['url']}\n\n"
        st.success("✅ 已產生報表")
        st.text_area("📋 LINE 報表內容 (可複製)", result_msg.strip(), height=400)
        js_safe_msg = result_msg.strip().replace('`','\\`').replace('\\','\\\\').replace('$', '\\$')
        components.html(f"""
            <button onclick="copyText()" style="font-size:16px;padding:8px 16px;margin-top:10px; border-radius: 5px; border: 1px solid #ccc; cursor: pointer;">
                📋 複製到剪貼簿
            </button>
            <script>
            function copyText() {{
                const text = `{js_safe_msg}`;
                navigator.clipboard.writeText(text).then(function() {{
                    alert("✅ 已複製！");
                }}, function(err) {{
                    alert("❌ 失敗：" + err);
                }});
            }}
            </script>
        """, height=70)