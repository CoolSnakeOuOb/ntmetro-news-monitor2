# 新聞輿情 Line 訊息產生器 (Streamlit + SerpApi)

這是一個使用 Streamlit 打造的網頁應用程式，旨在幫助使用者快速、有效地蒐集每日新聞輿情，並產生格式化的 Line 訊息。

## 主要功能

* **多關鍵字搜尋**：支援輸入用逗號分隔的多個關鍵字，程式會為每個關鍵字獨立進行新聞搜尋。
* **即時新聞抓取**：透過 SerpApi 的 `google_news` 引擎，獲取最全面、最即時的新聞搜尋結果。
* **24小時內新聞篩選**：採用直觀的邏輯，在抓取新聞後，自動篩選出時間標示為「小時」或「分鐘」前的近期新聞。
* **互動式勾選與分類**：在清晰的介面上，讓使用者能方便地勾選需要的新聞，並為其指定分類。
* **一鍵產生與複製**：自動將勾選的新聞排版成預設的 Line 訊息格式，並提供一鍵複製到剪貼簿的功能。

## 安裝與設定

請依照以下步驟來設定您的本機環境。

### 1. 前置需求

* 已安裝 Python 3.8 或更新版本。

### 2. 下載專案並建立虛擬環境

```bash
# (假設您已將專案檔案下載到本機)
cd path/to/your/project_folder

# 建立一個名為 venv 的虛擬環境
python -m venv venv

# 啟用虛擬環境
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. 安裝必要的函式庫

使用我們剛才產生的 `requirements.txt` 檔案，一鍵安裝所有依賴項目。

```bash
pip install -r requirements.txt
```

### 4. 設定您的 API 金鑰

這是最重要的一步。

1.  在專案的根目錄下，建立一個名為 `.streamlit` 的資料夾。
2.  在 `.streamlit` 資料夾內，建立一個名為 `secrets.toml` 的檔案。
3.  打開 `secrets.toml`，並填入您的 SerpApi 金鑰，格式如下：

    ```toml
    SERPAPI_API_KEY = "您從SerpApi網站上複製的API金鑰"
    ```

### 專案檔案結構

請確保您的最終檔案結構如下：

```
your_project_folder/
├── .streamlit/
│   └── secrets.toml
├── app.py
└── requirements.txt
```

## 如何啟動應用程式

在您的終端機中，確認虛擬環境已啟用，並位於專案根目錄下，然後執行：

```bash
streamlit run app.py
```

您的瀏覽器將會自動打開一個新分頁，顯示應用程式介面。

## 應用程式畫面

![App Screenshot](https://i.imgur.com/your-screenshot-url.png)
*(可選：您可以在此處替換成您自己截的應用程式畫面連結)*