# 🚇 新聞輿情 Line 訊息產生器 (Streamlit + SerpApi + Gemini)

一個使用 Streamlit、SerpApi 和 Google Gemini AI 打造的自動化新聞輿情監測與報告產生器。

本工具旨在快速抓取與指定關鍵字相關的即時新聞，透過 AI 進行初步篩選推薦，並由人工進行最終確認與分類，最後一鍵產生適用於通訊軟體（如 LINE）的輿情報告。

![應用程式截圖](https://i.imgur.com/your-screenshot-url.png)

---

## 🚀 主要功能

* **多金鑰管理**：支援多組 SerpApi 金鑰，可透過下拉選單切換，並即時顯示 API 剩餘額度。
* **AI 智慧推薦**：整合 Google Gemini 1.5 Flash 模型，能根據預設指令自動閱讀新聞標題，並預先勾選出最相關的項目。
* **多關鍵字搜尋**：可一次輸入多個以逗號分隔的關鍵字進行批次新聞抓取。
* **卡片式 UI**：採用置中的卡片式佈局，讓新聞列表在寬螢幕上更清晰、專業，操作體驗更流暢。
* **互動式確認與分類**：使用者保有最終決定權，可自由增減勾選項目，並為每則新聞指派分類。
* **一鍵報告生成**：自動將最終選定的新聞，依分類整理成適合貼在 LINE 群組的格式化文字，並提供「複製到剪貼簿」功能。

---

## 🛠️ 安裝與設定

請依照以下步驟來設定您的本機環境。

### 1. 前置需求
* Python 3.9 或更高版本。
* Git 版本控制工具。

### 2. 安裝步驟
```bash
# 1. 複製此專案
git clone [您的 GitHub 專案網址]
cd [您的專案資料夾名稱]

# 2. 建立並啟用虛擬環境 (建議)
python -m venv venv
# Windows: .\venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 3. 安裝所有必要的函式庫
pip install -r requirements.txt
