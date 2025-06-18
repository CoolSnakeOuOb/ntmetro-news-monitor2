# 新聞輿情 Line 訊息產生器 (Streamlit + SerpApi)

這是一個使用 Streamlit 打造的網頁應用程式，旨在幫助使用者快速、有效地蒐集每日新聞輿情，並產生格式化的 Line 訊息。

## 主要功能

* **多關鍵字搜尋**：支援輸入用逗號分隔的多個關鍵字，程式會為每個關鍵字獨立進行新聞搜尋。
* **即時新聞抓取**：透過 SerpApi 的 `google_news` 引擎，獲取最全面、最即時的新聞搜尋結果。
* **24小時內新聞篩選**：採用直觀的邏輯，在抓取新聞後，自動篩選出的近期新聞。
* **互動式勾選與分類**：在清晰的介面上，讓使用者能方便地勾選需要的新聞，並為其指定分類。
* **一鍵產生與複製**：自動將勾選的新聞排版成預設的 Line 訊息格式，並提供一鍵複製到剪貼簿的功能。

### API 使用限制 (基於 SerpApi)

本專案使用 [SerpApi](https://serpapi.com/) 提供的 Google News API 服務來獲取新聞。

* **免費方案額度**：SerpApi 的免費方案 (Developer Plan) 提供**每月 100 次**的搜尋額度。
* **額度計算方式**：在我們的應用程式中，您每輸入 N 個關鍵字並按下「抓取」按鈕，就會消耗掉 **N 次**的搜尋額度（因為程式會為每個關鍵字獨立發起一次搜尋）。
* **用量查詢**：您可以隨時登入 SerpApi 的儀表板來查看您當月剩餘的額度。

請節省使用，以確保在整個月份中都能正常運作。

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

## 與第一代 (Playwright 版本) 的比較

這個版本 (可稱之為第二代) 的核心架構與使用 Playwright 的第一代有顯著的不同，主要是為了在**速度**與**可部署性**之間取得最佳平衡。

| 特性 | 第一代 (Playwright) | 第二代 (本版本 - RSS + Requests) |
| :--- | :--- | :--- |
| **核心技術** | **瀏覽器模擬 (Browser Simulation)**<br>在背景啟動一個完整的 Chrome 瀏覽器。 | **RSS 解析 + 深度爬取 (RSS Parsing + Deep Crawl)**<br>使用輕量的 `feedparser` 和 `requests` 函式庫。|
| **最終網址準確度**| **極高**。<br>因為是完整瀏覽器，可以完美執行 JavaScript 轉址，100% 取得最終網址。| **高**。<br>使用 `requests`+`BeautifulSoup` 的方法，對絕大多數情況有效，但若 Google 大改轉址頁面結構，可能需要調整程式。|
| **執行速度** | **非常慢**。<br>每次搜尋都需要啟動和操作一個完整的瀏覽器實例。| **非常快**。<br>抓取 RSS 和解析網址的速度遠快於啟動瀏覽器。|
| **可部署性** | **極低**。<br>幾乎無法部署到免費的雲端平台 (如 Streamlit Community Cloud)。| **高**。<br>只依賴標準的 Python 函式庫，可以輕鬆部署到任何地方。|
| **API 金鑰需求**| **不需要**<br>(但需自行處理反爬蟲與 IP 封鎖問題)| **需要**|
| **主要優點** | 網址解析最準確。 | 速度快、可部署 |
| **主要缺點** | 速度慢、資源消耗大、**無法部署**。 | 網址解析的穩定性略遜於瀏覽器模擬。 |

### 演進總結

總結來說，雖然第一代的 Playwright 版本能在「獲取最終網址」上做到 100% 的準確，但其**無法被輕鬆部署到雲端平台**的致命缺點，以及緩慢的執行速度，使其難以成為一個實用的日常工具。

因此，第二代選擇了**犧牲一點點網址解析的極端穩定性**（因為 `requests`+`BeautifulSoup` 的方法可能因 Google 改版而需微調），來換取**絕對精準的時間篩選、大幅提升的執行速度、以及最重要的——能夠被部署到任何地方的靈活性**。