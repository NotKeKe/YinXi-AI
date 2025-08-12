# 🎶 音汐 (Yin-Xi) Discord 機器人 🤖
<p align="center">
  <img src="./assets/botself.png" width = "300" height = "300"/>
</p>

( cogview-3-flash 幫他畫了 6 根手指ww )

**🔗 Bot 邀請連結:**
- [URL](https://discord.com/oauth2/authorize?client_id=1388773437257941183)

這是一個 Discord 機器人專案，主要結合了 AI 的各種功能 (例如: 免費的 API 調用、向量知識庫搜尋、AI 翻譯功能等...)。 <br><br>


## ✨ 特色
*   **AI 聊天**: 透過 AI 進行對話。
*   **翻譯**: 支援 AI 多語言翻譯，以及透過提供 Message ID 進行翻譯。
*   **多語言支持**: 目前支援使用 `zh-TW`, `zh-CN`, `en-US`。

## 🚀 使用方法
- `/help` 快速取得該 Bot 的概略功能。

### 💡 常用指令範例
以下是一些常用的指令範例，讓您快速上手：
*   `/chat [您的訊息]`：與 AI 進行對話。
    > (20250806 將整體架構修改，正是支援異步)
*   `/翻譯 [語言] [文字]`：用 AI 將文字翻譯成指定語言。

## ⚡ Quick Start
**❗建議使用 Python 3.13+ 以上的環境❗**

**請先設定 `.env` 檔案**:
* 請參考以下「配置設定 - 環境變數」部分，建立並填寫您的 `.env` 檔案。 <br>
**！務必在 .env 內填上 `DISCORD_TOKEN`！**<br><br>

**選項一** 使用 **[Docker](https://www.docker.com/)** (使用 docker 才會包括 fastapi 與 MongoDB 的部分):
```bash
# 將專案克隆至本地目錄
git clone https://github.com/NotKeKe/Discord-Bot-YinXi.git

# 進入專案目錄
cd Discord-Bot-YinXi

# 使用 docker compose 執行
docker-compose up -d
```

**選項二** 使用 **[uv](https://github.com/astral-sh/uv)**:
1. **與專案環境同步**:
    ```bash
    uv sync
    ```
2. **啟動機器人**:
    ```bash
    uv run newbot2.py
    ```

## ⚙️ 配置設定

### 🔑 環境變數 (`.env`)

為了讓專案正常運行，您需要建立一個 `.env` 檔案，並在其中設定必要的環境變數。

`.env` 檔案的範例如下：

```
# 其他可能需要的環境變數，例如：
DISCORD_TOKEN = YOUR-DISCORD-BOT-TOKEN
```

請根據您的實際需求填寫這些變數。

## 🤝 貢獻指南
我們歡迎任何形式的貢獻！如果您想為 音汐 AI 機器人做出貢獻，請遵循以下步驟：
1. 把他要進伺服器 多跟他說說話吧w

## ❓ 常見問題 (FAQ)
*   這個 Bot 為什麼跟[音汐](https://github.com/NotKeKe/Discord-Bot-YinXi)那麼像?
    > 因為他本身就是從音汐這個專案複製過來改的

## 📞 聯絡與支援
如果您有任何問題、建議或需要支援，可以透過以下方式聯絡我們：
*   **Discord 伺服器**: [Discord Server](https://discord.gg/MhtxWJu)
*   至 GitHub 的 [Issues](https://github.com/NotKeKe/YinXi-AI/issues/new) 註明您的問題或建議。
*   私訊克克 (Discord: .kejc) 來詢問有關此 Bot 的各種問題

## 📄 授權
- [Apache License 2.0](LICENSE)