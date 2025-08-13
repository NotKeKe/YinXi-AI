# 🎶 音汐 (Yin-Xi) AI Discord 機器人 🤖
<p align="center">
  <img src="./assets/botself.png" width = "300" height = "300"/>
</p>

> ( 這次是 Copilot 畫的，我覺得不好看:) )

**[🔗 Bot 邀請連結](https://discord.com/oauth2/authorize?client_id=1388773437257941183)**

### 📝 簡介
- 這是一個 Discord 機器人專案，主要結合了 AI 的各種功能 (例如: 免費的 API 調用、向量知識庫搜尋、AI 翻譯功能等...)。 <br>

### 🛠️ 專案相關技術
- 本專案使用了 [MongoDB](https://www.mongodb.com/) 做長久存儲，[Qdrant](https://qdrant.tech/) 來做**向量**數據庫相關功能，以及使用 [Redis](https://github.com/redis/redis) 保存可用的模型及[本地 LM Studio](https://lmstudio.ai/) 狀態。

### 🔌 API 接口來源
- 目前的 API 接口來源有以下幾個:
    1. [Cerebras](https://cloud.cerebras.ai/)
    2. [Zhipu](https://open.bigmodel.cn/)
    3. [Gemini](https://aistudio.google.com/)
    4. [Ollama](https://ollama.com/)
    5. [LM Studio](https://lmstudio.ai/)
    6. 未來預計會讓使用者使用自定義 Provider，不過由於安全性問題，目前尚未開發相關功能。


## ✨ 特色
*   **AI 聊天**: 透過 AI 進行對話。
*   **翻譯**: 支援 AI 多語言翻譯，以及透過提供 Message ID 進行翻譯。
*   **多語言支持**: 目前支援使用 `zh-TW`, `zh-CN`, `en-US`。

## 🚀 使用方法
- `/help` 快速取得該 Bot 的概略功能。

### 💡 指令範例
以下是一些指令範例，讓您快速上手：<br>
1. **AI 聊天**:
    *   **/chat [您的訊息]**：
        > 與 AI 進行對話。 <br>
        > (20250806 將整體架構修改，正式支援異步)
    *   **/set_ai_channel**：
        > 讓你在不使用指令的情況下，直接在當前頻道跟音汐AI聊天。
    *   **直接透過私訊也可以聊天!**
2. **AI 翻譯**:
    *   **/翻譯 [語言] [文字]**：
        > 使用 AI 將文字翻譯成指定語言。
    *   **/translate_from_message [訊息ID] [翻譯為什麼語言]**：
        > 透過指定的 Message ID 翻譯那個人說的話 (不會顯示在頻道內，所以不用在意你的翻譯被別人看到!)
3. **提示詞調整**:
    *   基本上有分為 **提示詞描述**、**提示詞上傳**、**提示詞刪除** 等...
        > 記得多多探索可用的指令 :D
4. **向量知識庫** (相關功能尚未支援多語言，目前僅繁體中文):
    *   **/向量自定義知識庫加入**
        > 可以選擇上傳檔案，目前支援 .txt 與 .md 格式。
    *   **/向量自定義知識庫查詢**
    *   **/向量自定義知識庫刪除**
    *   **/向量自定義知識庫改名**

## ⚡ Quick Start
直接邀請**音汐 AI** 進去你的伺服器吧~<br>
[邀請連結](https://discord.com/oauth2/authorize?client_id=1388773437257941183)

## 🤝 貢獻指南
我們歡迎任何形式的貢獻！如果您想為 音汐 AI 機器人做出貢獻，請遵循以下步驟：
1. 把他邀進伺服器 多跟他說說話吧w

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