# 🚇 新北捷運輿情監測系統

本系統是一個基於 Streamlit 的網頁應用，透過 Google News + Gemini AI，協助使用者每日快速抓取、篩選與整理與捷運相關的新聞，並自動分類與產出 LINE 通報格式的報表。

---
[應用程式截圖](https://github.com/user-attachments/assets/855b9dbb-e72b-466b-bcac-88600fa67acd)

## 🔧 功能簡介

- 🔍 **新聞抓取**：使用 [SerpApi](https://serpapi.com/) 從 Google News 即時搜尋關鍵字新聞。
- 🤖 **AI 智能推薦**：結合 Google Gemini AI 模型，自動挑選與「新北捷運」最相關的新聞。
- 🗂️ **分類勾選**：使用者可依 AI 建議進行修正，並為每篇新聞手動分類。
- 📤 **報表產出**：自動產生格式化的 LINE 訊息內容，方便主管群組分享。

---

## 🚀 使用方法

1. **安裝依賴套件**

   ```bash
   pip install -r requirements.txt
   ```

2. **設定 API 金鑰**

   在 `.streamlit/secrets.toml` 中設定以下內容：

   ```toml
   GEMINI_API_KEY = "your_google_gemini_api_key"
   [serpapi_keys]
   帳號名稱1 = "your_serpapi_key_1"
   帳號名稱2 = "your_serpapi_key_2"

   ```

3. **啟動應用程式**

   ```bash
   streamlit run app.py
   ```

---


## 📁 專案結構

```
.
├── app.py                  # 主程式：Streamlit App
├── requirements.txt        # 相依套件清單
└── .streamlit/
    └── secrets.toml        # 私密金鑰設定檔（請勿上傳）
```

---

## 🧠 AI Prompt 範例

系統預設使用以下提示詞進行 Gemini AI 分析：
"""
你是新北捷運公司的輿情觀測員，你的任務是從每日新聞中，挑選出與公司業務最相關、或可能需要高層注意的事件。
請從以下新聞標題列表中，挑選出 3-5 則與「新北市」、「捷運工程」、「列車狀況」、「民眾抱怨」或「重大意外」最相關的新聞。
避免選擇標題內容相似的新聞。
"""

---

## 🛡️ 注意事項

- **SerpApi** 有查詢次數限制，請確認額度。
- **Gemini API** 使用的是 `gemini-1.5-flash` 模型，需正確設置金鑰。
- 本系統目前僅支援中文新聞、且針對「當日」新聞進行過濾。

---

# 技術選型與版本演進比較報告：API 驅動 vs. 瀏覽器模擬

以下說明了「新北捷運新聞輿情工具」從第一代 Playwright 模擬瀏覽器版本，演進到第二代 API 驅動版本的關鍵考量與技術差異。

---

## 📊 技術演進比較表

| 特性 / 面向 | 🏆 第二代：API 驅動版 (本版本) | ⚙️ 第一代：Playwright 瀏覽器模擬版 |
|------------|----------------------------------|----------------------------------|
| 核心技術 | **API 呼叫**：向 SerpApi / Gemini 發送結構化 HTTP 請求，接收 JSON 結果。 | **Browser Simulation**：完整啟動 Chrome 瀏覽器，模擬用戶互動。 |
| 執行速度 | **極快**，數秒內完成多關鍵字查詢。 | **非常慢**，每次都需啟動瀏覽器、等待頁面載入。 |
| 部署便利性 | **高**，可部署在 Streamlit Cloud 或任何雲端。 | **極低**，瀏覽器模擬需伺服器支援圖形環境。 |
| 系統資源耗用 | **低**，主要為網路 I/O。 | **高**，CPU/記憶體佔用嚴重。 |
| 穩定性與維護 | **高**，依賴 API 規格穩定性。 | **中等**，易因目標網站改版導致錯誤。 |
| 外部依賴 | **需要 API 金鑰**，使用 SerpApi 和 Gemini。 | **不需金鑰**，但需處理驗證碼、反爬蟲等問題。 |
| 功能擴展性 | **極高**，可擴充 AI、翻譯、分析等功能。 | **有限**，整合其他服務困難。 |

---

### 第一代 (Playwright)

- 優勢：真實模擬瀏覽器、精確抓取頁面資料。
- 劣勢：部署困難、速度極慢、資源消耗高。
- 適用：學術測試、本機自用腳本。

### 第二代 (API)

- 優勢：極快執行速度、可雲端部署、高穩定性。
- 關鍵特色：
  - 支援多 SerpApi 金鑰切換與剩餘次數查詢。
  - 結合 Gemini AI 進行智慧篩選與推薦。
  - 架構模組化，方便未來加入更多分析功能。
