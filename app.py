import streamlit as st
import collections
from serpapi import GoogleSearch
import streamlit.components.v1 as components

# --- Setup: API Key & Core Functions ---

SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY")

def is_published_very_recently(date_str: str) -> bool:
    """
    採用您的最終版邏輯：只接受時間單位為秒、分鐘、小時的新聞。
    """
    if not isinstance(date_str, str):
        return False
    
    date_str_lower = date_str.lower()
    
    # 只要時間單位是秒、分鐘或小時，就認定為近期
    if any(marker in date_str_lower for marker in ["second", "秒", "minute", "分鐘", "hour", "小時"]):
        return True
        
    return False

def fetch_news_from_light_api(keywords: list):
    """
    為每個關鍵字呼叫 google_news_light API，獲取大量原始結果以供篩選。
    """
    raw_results = collections.defaultdict(list)
    if not SERPAPI_API_KEY:
        st.error("錯誤：請在 .streamlit/secrets.toml 中設定您的 SERPAPI_API_KEY")
        return raw_results

    for kw in keywords:
        params = {
            "engine": "google_news_light",
            "q": kw,
            "api_key": SERPAPI_API_KEY,
            "hl": "zh-tw",
            "gl": "tw",
            "num": 100,      # 【核心】請求 100 則新聞，作為篩選的候選池
            "tbs": "qdr:d"   # 仍然建議 API 優先給近一天的結果，增加命中率
        }
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            if "news_results" in data:
                raw_results[kw] = data["news_results"]
        except Exception as e:
            st.error(f"搜尋關鍵字 '{kw}' 時發生錯誤: {e}")
            
    return raw_results

# --- Streamlit UI ---

st.set_page_config(page_title="捷運輿情工具", page_icon="🚇", layout="wide")
st.title("📰 新北捷運輿情工具")

with st.expander("📖 使用說明"):
    st.markdown("""
    1.  **輸入關鍵字**：用逗號分隔。
    2.  **抓取與篩選**：點擊按鈕後，程式會抓取最多 100 則新聞，並篩選出24小時內的新聞。
    3.  **勾選與分類**：從篩選後的結果中挑選您需要的文章。
    4.  **產生訊息**：產生最終的 LINE 格式訊息。
    """)

if 'filtered_news' not in st.session_state:
    st.session_state.filtered_news = collections.defaultdict(list)

default_keywords = "捷運, 輕軌, 環狀線, 新北, 軌道, 鐵路"
keywords_input = st.text_input("🔍 輸入關鍵字（逗號分隔）", default_keywords)

if st.button("📥 獲取近期新聞"):
    keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
    if not keyword_list:
        st.warning("請輸入有效的關鍵字。")
    elif not SERPAPI_API_KEY:
        st.error("請先在 .streamlit/secrets.toml 中設定您的 SERPAPI_API_KEY。")
    else:
        with st.spinner("🔄 正在搜尋最新新聞..."):
            all_news_results = fetch_news_from_light_api(keyword_list)
        
        filtered_results = collections.defaultdict(list)
        with st.spinner("🔍 正在進行時間篩選..."):
            for kw, items in all_news_results.items():
                for item in items:
                    if is_published_very_recently(item.get("date")):
                        filtered_results[kw].append(item)
        
        st.session_state.filtered_news = filtered_results
        
        total_found = sum(len(v) for v in filtered_results.values())
        st.success(f"✅ 篩選完成！總共找到了 {total_found} 則近期新聞。")

# --- 勾選與分類表單 ---
if st.session_state.filtered_news:
    st.header("Step 2: 勾選並分類您需要的新聞")
    with st.form("news_selection_form"):
        selected_articles_data = []
        categories = ["【新北】", "【同業】", "【其他】"]
        
        keyword_list_in_scope = [k.strip() for k in keywords_input.split(",") if k.strip()]

        for kw in keyword_list_in_scope:
            items = st.session_state.filtered_news.get(kw, [])
            if items:
                st.subheader(f"🔸 {kw}")
                for i, article in enumerate(items):
                    title = article.get('title', "無標題")
                    url = article.get('link', "#")
                    key = f"select_{kw}_{i}"

                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        is_selected = st.checkbox(f"[{title}]({url})", key=key, help=f"來源：{article.get('source', '未知')} - 發布於: {article.get('date', '未知')}")
                    with col2:
                        category = st.radio("分類", options=categories, key=f"cat_{kw}_{i}", horizontal=True, label_visibility="collapsed")
                    
                    if is_selected:
                        article['category'] = category
                        selected_articles_data.append(article)
        
        submitted = st.form_submit_button("✅ 產生 Line 訊息")

        # --- 報表產生 ---
        if submitted:
            st.header("Step 3: 複製以下訊息")
            if not selected_articles_data:
                st.warning("⚠️ 請至少勾選一則新聞")
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
                            # 直接使用 link 作為 url
                            result_msg += f"{item['title']}\n{item['link']}\n\n"

                st.success("✅ 已產生訊息")
                st.text_area("📋 LINE 訊息內容 (可複製)", result_msg.strip(), height=400)
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
