import streamlit as st
import collections
from serpapi import GoogleSearch
import streamlit.components.v1 as components
import requests 
import google.generativeai as genai
# --- Setup: API Key & Core Functions ---

SERPAPI_API_KEY = st.secrets.get("SERPAPI_API_KEY")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@st.cache_data(ttl=60) # 使用快取，每 1 分鐘(60秒)才重新抓取一次
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

def is_published_very_recently(date_str: str) -> bool:
    """只接受時間單位為秒、分鐘、小時的新聞。"""
    if not isinstance(date_str, str):
        return False
    date_str_lower = date_str.lower()
    return any(marker in date_str_lower for marker in ["second", "秒", "minute", "分鐘", "hour", "小時"])

def fetch_news_from_light_api(keywords: list):
    """為每個關鍵字呼叫 google_news_light API，獲取大量原始結果以供篩選。"""
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
            "num": 100,
            "tbs": "qdr:d"
        }
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            if "news_results" in data:
                raw_results[kw] = data["news_results"]
        except Exception as e:
            st.error(f"搜尋關鍵字 '{kw}' 時發生錯誤: {e}")
    return raw_results

@st.cache_data(ttl=600) # 將 AI 的推薦結果快取 10 分鐘
def get_ai_recommendations(_articles_dict, prompt_template):
    if not GEMINI_API_KEY or not genai.get_model('models/gemini-1.5-flash'):
        return []

    # 將所有新聞標題整理成一個列表
    all_titles = []
    for kw, items in _articles_dict.items():
        for item in items:
            all_titles.append(item['title'])
    
    if not all_titles:
        return []

    # 組合最終的 Prompt
    full_prompt = prompt_template + "\n\n以下是新聞標題列表：\n" + "\n".join(f"- {title}" for title in all_titles)
    full_prompt += "\n\n請只回傳你挑選出的新聞標題，每個標題一行，不要有其他多餘的文字或編號。"

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(full_prompt)
        # 將 AI 回傳的文字，按換行符切分成標題列表
        recommended_titles = response.text.strip().split('\n')
        # 清理可能出現的 "- " 等符號
        cleaned_titles = [title.strip().lstrip('- ') for title in recommended_titles]
        return cleaned_titles
    except Exception as e:
        st.error(f"請求 AI 推薦時發生錯誤: {e}")
        return []
# --- Streamlit UI ---

st.set_page_config(page_title="捷運輿情工具", page_icon="🚇", layout="wide")
st.title("📰 新北捷運輿情工具")

# 【新增】在標題下方顯示 API 額度資訊
if SERPAPI_API_KEY:
    account_info = get_serpapi_account_info(SERPAPI_API_KEY)
    if account_info and 'plan_searches_left' in account_info:
        st.info(f"本月剩餘搜尋額度： {account_info['plan_searches_left']} / {account_info['searches_per_month']}")
    else:
        st.warning("無法獲取 API 額度資訊，請確認您的 API 金鑰是否正確。")

with st.expander("📖 使用說明"):
    st.markdown("""
    1.  **輸入關鍵字**：用逗號分隔。
    2.  **抓取與篩選**：點擊按鈕後，程式會抓取最多 100 則新聞，並篩選出24小時內的新聞。
    3.  **(可選) 請求 AI 推薦**：點擊「請求 AI 推薦」按鈕，AI 會根據內建的指令，為您預先勾選它認為重要的項目。
    4.  **最終確認與分類**：檢查 AI 預選的結果，您可以取消勾選或補上其他新聞，並為所有勾選項目指定分類。
    5.  **產生報表**：點擊「產生 Line 訊息」按鈕，即可獲得最終的輿情報告。
    """)

if 'filtered_news' not in st.session_state:
    st.session_state.filtered_news = collections.defaultdict(list)

st.header("Step 1:輸入關鍵字")
default_keywords = "捷運, 輕軌, 環狀線, 新北, 軌道, 鐵路"
keywords_input = st.text_input("🔍 輸入關鍵字（逗號分隔）", default_keywords)

if st.button("📥 抓取並篩選近期新聞"):
    keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
    if not keyword_list:
        st.warning("請輸入有效的關鍵字。")
    elif not SERPAPI_API_KEY:
        st.error("請先在 .streamlit/secrets.toml 中設定您的 SERPAPI_API_KEY。")
    else:
        with st.spinner("🔄 正在抓取最新新聞..."):
            all_news_results = fetch_news_from_light_api(keyword_list)
        
        filtered_results = collections.defaultdict(list)
        with st.spinner("🔍 正在進行時間篩選..."):
            for kw, items in all_news_results.items():
                for item in items:
                    if is_published_very_recently(item.get("date")):
                        if item.get("title") and item.get("link"):
                           filtered_results[kw].append(item)
        
        st.session_state.filtered_news = filtered_results
        
        total_found = sum(len(v) for v in filtered_results.values())
        st.success(f"✅ 篩選完成！總共找到了 {total_found} 則近期新聞。")


# --- AI 推薦區塊 (無輸入框版) ---
if 'filtered_news' in st.session_state and st.session_state.filtered_news:
    st.header("Step 2: (可選) 請求 AI 推薦")

    # 直接點擊按鈕，使用內建的固定指令
    if st.button("🤖 請求 AI 推薦"):
        if not GEMINI_API_KEY:
            st.error("請先在 .streamlit/secrets.toml 中設定您的 GEMINI_API_KEY。")
        else:
            # 【核心修改】將 Prompt 直接寫在程式碼中
            # 您可以隨時在這裡修改您的固定指令
            hardcoded_prompt = """
            你是一位新北捷運局的輿情觀測員，你的任務是從每日新聞中，挑選出與業務最相關、或可能需要高層注意的事件。
            請從以下新聞標題列表中，挑選出 3-5 則與「新北市」、「捷運工程」、「列車狀況」、「民眾抱怨」或「重大意外」最相關的新聞。
            """
            
            with st.spinner("🧠 AI 正在為您閱讀與挑選新聞..."):
                # 將固定的指令傳送給 AI 函數
                recommended_titles = get_ai_recommendations(st.session_state.filtered_news, hardcoded_prompt)
                
                # 將 AI 推薦的結果存到 session_state 中
                st.session_state.recommended_titles = recommended_titles
                st.success(f"AI 已推薦 {len(recommended_titles)} 則新聞，請至下方查看預勾選結果。")

# --- 勾選與分類表單 ---
if 'filtered_news' in st.session_state and st.session_state.filtered_news:
    st.header("Step 3: 勾選並分類您需要的新聞")
    
    # 從 session_state 中讀取 AI 的推薦結果 (如果沒有推薦，則為空列表)
    recommended_titles = st.session_state.get('recommended_titles', [])

    with st.form("news_selection_form"):
        selected_articles_data = []
        categories = ["【新北】", "【同業】", "【其他】"]
        
        # 使用者輸入的關鍵字列表來維持順序
        keyword_list_in_scope = [k.strip() for k in keywords_input.split(",") if k.strip()]

        for kw in keyword_list_in_scope:
            items = st.session_state.filtered_news.get(kw, [])
            if items:
                st.subheader(f"🔸 {kw}")
                for i, article in enumerate(items):
                    title = article.get('title', "無標題")
                    url = article.get('url', "#")
                    key = f"select_{kw}_{i}"

                    # 【核心修改】檢查標題是否在 AI 推薦列表中
                    is_recommended = title in recommended_titles
                    
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        # 使用 value=is_recommended 來決定是否預設勾選
                        is_selected = st.checkbox(
                            f"[{title}]({url})", 
                            key=key, 
                            value=is_recommended, 
                            help=f"來源：{article.get('source', '未知')} - 發布於: {article.get('date', '未知')}"
                        )
                    with col2:
                        category = st.radio(
                            "分類", 
                            options=categories, 
                            key=f"cat_{kw}_{i}", 
                            horizontal=True, 
                            label_visibility="collapsed"
                        )
                    
                    if is_selected:
                        article['category'] = category
                        selected_articles_data.append(article)
        
        submitted = st.form_submit_button("✅ 產生 Line 訊息")
        
        if submitted:
            # 將最終勾選的結果存到 session_state，以便在表單外產生報表
            st.session_state.form_submitted = True
            st.session_state.selected_news_for_report = selected_articles_data

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
                            result_msg += f"{item['title']}\n{item['link']}\n\n"

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