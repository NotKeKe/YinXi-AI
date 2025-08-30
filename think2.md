## 工具優化-搜尋
*   使用 core.function 內的字串切割 function
*   使用暫存向量數據庫來儲存搜尋結果
*   告知 LLM 使用某項工具去搜尋剛剛的結果

## 決定是否傳送訊息，使用工具調用，所以需要提供channelID與使用者名稱、ID
格式應該如下:
<discord_message channelId={channelId} userName={userName} userId={userId} messageId={messageId} time={time}> {content} </discord_message>

## 工具應該有以下參數:
*   channelId
*   messageId
*   text
*   replied: bool # 讓他自己決定是否要使用回覆 default to None

## 上下文處理
*   僅保留近6條，其他存進 vector database
    *   如果報錯，就僅保留近4條
*   **自動將過去的聊天歷史存為向量，伺服器群主應有權決定是否執行此行為**
    *   如果server owner disable it, history 就只有當前的對話 (即 len of history == 1)
    *   因此不需要每次對話都將聊天歷史紀錄轉為向量

## 並發
如果在生成結束前出現另一則訊息，則在 user prompt 內累加

## example
example_passed_history_payload = {
    'channelID': 2385728935,
    'userID': 138471834,
    'userName': 'Leon',
    'messageID': 154356,
    'time': '2025/08/30 20:00:15',
    'text': '你好'
}

## system prompt
yinxi_should_response: 讓音汐判斷是否要回覆的提示詞

## 隱私政策
```markdown
> **重要提示**  
> 在使用本機 Qdrant 進行向量存儲前，請先閱讀以下條款並點擊 ✅ 同意或 ❌ 不同意。若您選擇不同意，我們將不會收集或保存您的對話內容。

---

## 1️⃣ 我們會收集哪些資訊  
- **channelID**：對話發生的 Discord 頻道 ID（用於定位資料來源）  
- **userID**：您在 Discord 的唯一識別碼 
- **userName**：您的 Discord 名稱（文字顯示，可被使用者自行更改）  
- **messageID**：對話訊息的唯一 ID（用於查詢或刪除特定訊息）  
- **time**：訊息發送時間戳（YYYY/MM/DD HH:MM:SS 格式，僅作為內部紀錄）  
- **text**：實際對話文字內容（將被轉換成向量以提升機器人回應品質）

> ❗️我們不會收集或存儲任何圖片，或者拒絕此條款的使用者訊息。若在對話中自動出現此類資料，我們將不進行向量化。

---

## 2️⃣ 資料收集目的  
- **提升機器人回應品質**：將 `text` 轉為向量，方便後續做為聊天歷史之內容。  
- **做為頻道的歷史紀錄搜尋**：目前此功能尚未實裝，但未來有可能做出相關功能，並且只能在相同頻道內搜尋。

---

## 3️⃣ 資料儲存方式  
1. **本地 Qdrant**：僅在我們的**本地NAS**內部部署，未設密碼且 ip, port 不公開。
2. **備份**：每天都會有本地備份，確保資料不會上傳到任何雲端服務。 
3. **資料保留期限**：除非使用者另行要求刪除，資料將持續保存在 Qdrant 內。

---

## 4️⃣ 使用者同意與選擇  
- 點擊 ✅ 表示「我已閱讀並同意上述條款，我願將對話內容存入本機 Qdrant」。  
- 點擊 ❌ 表示「我不同意，請勿收集或儲存我的資料」。

> ❗️一旦點選 ✅，即代表您授權我們進行向量化並保存。若在之後想撤回同意，可再次使用此指令，並點擊 ❌，資料將會被刪除。
```