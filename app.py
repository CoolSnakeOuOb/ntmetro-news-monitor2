import streamlit as st
import collections
from serpapi import GoogleSearch
import streamlit.components.v1 as components
import requests
import google.generativeai as genai

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

# --- 2. 後端核心函式 (無變動) ---
@st.cache_data(ttl=60)
def get_serpapi_account_info(api_key):
    if not api_key: return None
    try:
        r = requests.get(f"https://serpapi.com/account?api_key={api_key}")
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None

def fetch_news_from_light_api(api_key, keywords: list):
    raw_results = collections.defaultdict(list)
    for kw in keywords:
        params = {"engine": "google_news_light", "q": kw, "api_key": api_key, "hl": "zh-tw", "gl": "tw", "num": 100, "tbs": "qdr:d"}
        try:
            search = GoogleSearch(params)
            data = search.get_dict()
            if "news_results" in data:
                raw_results[kw] = data["news_results"]
        except Exception as e:
            st.error(f"搜尋關鍵字 '{kw}' 時發生錯誤: {e}")
    return raw_results

@st.cache_data(ttl=600)
def get_ai_recommendations(_articles_dict, prompt_template):
    if not GEMINI_API_KEY:
        st.error("尚未設定 Gemini API Key！")
        return []
    all_titles = [item['title'] for items in _articles_dict.values() for item in items]
    if not all_titles: return []
    full_prompt = (f"{prompt_template}\n\n以下是新聞標題列表：\n" + "\n".join(f"- {title}" for title in all_titles) + "\n\n請只回傳你挑選出的新聞標題，每個標題一行，不要有其他多餘的文字或編號。")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(full_prompt)
        cleaned_titles = [title.strip().lstrip('- ') for title in response.text.strip().split('\n')]
        return cleaned_titles
    except Exception as e:
        st.error(f"請求 AI 推薦時發生錯誤: {e}")
        return []

# --- 3. Streamlit UI 介面 ---

left_margin, main_col, right_margin = st.columns([0.15, 0.7, 0.15])

with main_col:
    st.title("🚇 新北捷運輿情監測")

    if not SERPAPI_KEYS_TABLE:
        st.error("錯誤：請在 .streamlit/secrets.toml 中設定 [serpapi_keys] 表格")
        st.stop()
    
    with st.expander("📖 使用說明"):
        st.markdown("""
        1.  **選擇 API 帳號**：在所有操作開始前，請先從頁面上方的下拉選單選擇要使用的 SerpApi 帳號，並確認剩餘額度。
        2.  **設定與搜尋**：輸入要搜尋的關鍵字（用逗號分隔），然後點擊「抓取並篩選近期新聞」按鈕。
        3.  **(可選) AI 智慧推薦**：點擊「AI 推薦」按鈕，AI會為您預先勾選它認為重要的項目。
        4.  **最終確認與分類**：檢查 AI 預選的結果，您可以取消勾選或補上其他新聞，並為所有勾選項目指定分類。
        5.  **產生報表**：點擊「產生 Line 訊息」按鈕，即可獲得最終的輿情報告。
        """)
    selected_account_name = st.selectbox("選擇要使用的 SerpApi 帳號", options=list(SERPAPI_KEYS_TABLE.keys()))
    SERPAPI_API_KEY = SERPAPI_KEYS_TABLE[selected_account_name]

    account_info = get_serpapi_account_info(SERPAPI_API_KEY)
    if account_info and 'plan_searches_left' in account_info:
        searches_used = account_info['searches_per_month'] - account_info['plan_searches_left']
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("本月總額度", f"{account_info['searches_per_month']:,}")
        m_col2.metric("已用額度", f"{searches_used:,}")
        m_col3.metric("剩餘額度", f"{account_info['plan_searches_left']:,}", delta_color="inverse")

    st.divider()
    st.header("Step 1: 設定與搜尋", anchor=False, divider="rainbow")
    keywords_input = st.text_input("🔍 輸入關鍵字（逗號分隔）", DEFAULT_KEYWORDS)
    
    # 【按鈕寬度修正】調整欄位比例並移除 use_container_width
    b1_left, b1_mid, b1_right = st.columns([2.5, 1, 2.5])
    with b1_mid:
        fetch_button_pressed = st.button("📥 抓取新聞")

    if 'fetch_success_message' in st.session_state:
        st.success(st.session_state.fetch_success_message)
        del st.session_state.fetch_success_message

    if st.session_state.filtered_news:
        st.divider()
        st.header("Step 2: (可選) AI 智慧推薦", anchor=False, divider="rainbow")
        
        # 【按鈕寬度修正】調整欄位比例並移除 use_container_width
        b2_left, b2_mid, b2_right = st.columns([2.5, 1, 2.5])
        with b2_mid:
            if st.button("🤖 AI 推薦"):
                with st.spinner("🧠 AI 正在為您閱讀與挑選新聞..."):
                    recommended = get_ai_recommendations(st.session_state.filtered_news, DEFAULT_AI_PROMPT)
                    st.session_state.recommended_titles = recommended
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
                        title, url, source, date = article.get('title', "無標題"), article.get('link', "#"), article.get('source', '未知來源'), article.get('date', '未知時間')
                        key_prefix = f"item_{kw}_{i}"
                        is_recommended = title in recommended_titles
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([0.08, 0.62, 0.3])
                            with c1:
                                is_selected = st.checkbox("", key=f"{key_prefix}_select", value=is_recommended, label_visibility="collapsed")
                            with c2:
                                st.markdown(f"**{title}**")
                                st.caption(f"🔗 [{source}]({url}) | 🕒 {date}")
                            with c3:
                                category = st.radio("分類", options=CATEGORIES, key=f"{key_prefix}_cat", horizontal=True, label_visibility="collapsed")
                        if is_selected:
                            article['category'] = category
                            selected_articles_data.append(article)
            
            # 這個提交按鈕可以維持全寬，比較醒目
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
                        result_msg += f"{item['title']}\n{item['link']}\n\n"
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
                <style> button {{ font-size:16px; padding:8px 16px; margin-top:10px; border-radius: 5px; border: 1px solid #ccc; cursor: pointer; background-color: #f0f2f6;}} button:hover {{ background-color: #e0e2e6; }}</style>
            """, height=80)
        
        b_left, b_mid, b_right = st.columns([2, 1, 2])
        with b_mid:
            # 這個按鈕也可以不用全寬
            if st.button("清除報告並重新開始"):
                if 'report_data' in st.session_state: del st.session_state.report_data
                if 'filtered_news' in st.session_state: del st.session_state.filtered_news
                if 'recommended_titles' in st.session_state: del st.session_state.recommended_titles
                st.rerun()

# --- 4. 按鈕的後端處理邏輯 (放在 UI 渲染程式碼之外) ---
if fetch_button_pressed:
    keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
    if not keyword_list:
        st.warning("請輸入有效的關鍵字。")
    else:
        with st.spinner("正在抓取與篩選新聞..."):
            all_news = fetch_news_from_light_api(SERPAPI_API_KEY, keyword_list)
            filtered_results = collections.defaultdict(list)
            for kw, items in all_news.items():
                for item in items:
                    date_str = item.get("date", "")
                    if "ago" in date_str or any(marker in date_str.lower() for marker in ["second", "秒", "minute", "分鐘", "hour", "小時"]):
                         if item.get("title") and item.get("link"):
                            filtered_results[kw].append(item)
            
            st.session_state.filtered_news = filtered_results
            total_found = sum(len(v) for v in filtered_results.values())
            st.session_state.fetch_success_message = f"✅ 抓取完成！共找到 {total_found} 則近期新聞。"
            st.rerun()