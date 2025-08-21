## 向量 (qdrant)
*   知識庫
    *   使用者自定義知識庫
    *   一些針對某個領域的知識庫
*   聊天
    *   聊天過長時，將過去聊天歷史轉為向量存儲
    *   紀錄下使用者的偏好 -> 快取結果
    
## 快取 (redis)
*   使用者偏好

## MongoDB
*   聊天紀錄

## 本地模型使用
1. 生成標題: lmstudio **(qwen3 0.6b chat)**
2. 取得使用者資訊的 embedding : lmstudio **(qwen3 0.6b embedding)**
3. chat_human : lmstudio **(unsloth/deepseek-r1-0528-qwen3-8b)**
4. long term memory: self_ollama **(qwen3 0.6b chat)**
*   chat_human 過程
    *   => 呼叫 2.
    *   => 呼叫 3.
    *   => 呼叫 4.
        *   True: 同 2.
*   /chat 過程
    *   => 呼叫 2.
    *   => normal chat
    *   => 呼叫 4. (with 1.)
    *   => 呼叫 1. (with 4.)

## keep_think
*   現在預計擁有3個mode，他可以自己使用工具切換 (20250819)
    *   預計要分別設計3個提示詞
    *   **Question**
        1. 要怎麽讓他決定在 chat mode 下，應該在哪個頻道講話 <- Should be a must hard issue
            > 獲得全部 chat_human / DM 頻道的訊息讓他選擇?
        2. 要使用工具切換成 resting mode ，還是使用原先的 task_stop 工具切換
            > 預計刪除 task_stop，但音汐要怎麼決定休息多久?
        3. 在這3個mode之中，會有多少需要重複使用的東西? 需要將他們移出來。
    *   **Think**
        *   每次開始前，先決定 mode 切換


(20250822)
- 他不會主動去跟人聊天，也不知道有哪些頻道
- 一個隨機的心情
    - data type
        > `energy: ( random.randint() or ( energy--/second, when under 20%, random轉為另一種情緒 ) ), mood: happiness`
    - llm 自己更新情緒，例如使用者跟他聊天，可能就會 +20 happiness\
    => 擁有一些情緒種類 (開心, 傷心)
- 手動的隨機對話
    - 我認為可以去 lovelive api 調用幾句話來用，作為風格範例
    - 做一些定時工具，取得有趣的事情之類的
- 分開 self_database 與 使用者相關的資訊 -> 向量檢索可以比較不混亂，llm也比較知道要調用什麼工具