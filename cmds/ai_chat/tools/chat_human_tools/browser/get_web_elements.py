import trafilatura

from core.chat_human.manage_browser import current_pages

# 定義互動元素查詢字串，包含各種可點擊或輸入的HTML標籤和ARIA角色
INTERACTIVE_QUERY = (
    "a, button, input, textarea, select, "
    "[role='button'], [role='link'], [role='textbox'], "
    "[contenteditable='true']"
)

async def collect_view(page):
    """
    從給定的Playwright頁面收集頁面視圖資訊，包括互動元素和主要文本內容。

    Args:
        page: Playwright的Page對象。

    Returns:
        一個字典，包含頁面URL、標題、文本內容和互動元素目標。
    """
    # 1) 收集互動元素 (僅限可見且未被禁用者)
    inter = page.locator(INTERACTIVE_QUERY).locator(":visible").filter(has_not=page.locator("[disabled]"))
    n = await inter.count()
    targets = []
    
    # 遍歷互動元素，最多取60個，避免處理過多元素導致效能問題
    for i in range(min(n, 60)):
        try:
            el = inter.nth(i)
            
            # 獲取元素的角色與名稱（優先使用ARIA屬性，其次是HTML屬性或文本內容）
            role = await el.get_attribute("role")
            tag  = await el.evaluate("e => e.tagName.toLowerCase()")
            name = (
                await el.get_attribute("aria-label") 
                or await el.get_attribute("name") 
                or await el.get_attribute("placeholder")
                or (await el.text_content() or "").strip()
            )
            
            # 如果沒有可用的名稱，則跳過此元素
            if not name:
                continue
            
            # 獲取元素的邊界框，如果不可見或尺寸為零，則跳過
            box = await el.bounding_box()
            if not box or box["width"] * box["height"] == 0:
                continue
            
            # 盡量使用Playwright語義化選擇器；若不行則回退到CSS選擇器
            if role and name:
                selector = f"getByRole('{role}', {{ name: {name!r} }})"
            elif tag in ("input", "textarea") and name:
                selector = f"getByLabel({name!r})"
            elif tag in ("input",) and (ph := await el.get_attribute('placeholder')):
                selector = f"getByPlaceholder({ph!r})"
            else:
                # 回退方案：生成一個簡單的唯一CSS選擇器
                # (也可替換為 @medv/finder 或 css-selector-generator 等第三方庫)
                selector = await el.evaluate("""
                    (e) => {
                        function simplePath(el){
                            if (el.id) return '#'+el.id;
                            const p = [];
                            while (el && el.nodeType===1 && p.length<5){
                                let s = el.nodeName.toLowerCase();
                                if (el.getAttribute('name')) s += `[name="${el.getAttribute('name')}"]`;
                                const idx = Array.from(el.parentNode?.children || []).filter(x => x.nodeName===el.nodeName).indexOf(el)+1;
                                if (idx>1) s += `:nth-of-type(${idx})`;
                                p.unshift(s);
                                el = el.parentElement;
                            }
                            return p.join('>');
                        }
                        return simplePath(e);
                    }
                """)
            
            # 判斷元素可能支援的動作
            actions = ["click"]
            if tag in ("input", "textarea") or (role == "textbox"):
                actions = ["type"]
            
            targets.append({
                "role": role or tag,
                "name": name or "",
                "selector": selector,
                "actions": actions
            })
            
        except Exception as e:
            # 捕獲並印出處理特定元素時的錯誤
            print(f'Erorr at index {i}: {e}')

    # 2) 抽取頁面主文本內容 (使用Trafilatura) → 切分成段落 → 選擇Top-K段落
    html = await page.content()
    # 從HTML中提取主文章內容，排除評論和表格
    art = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    # 將文章內容按行分割並去除空白行
    paras = [p.strip() for p in art.splitlines() if p.strip()]
    
    # 將段落切塊限制（每塊約300字）
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) <= 300:
            buf = (buf + " " + p).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)  # 將最後一個緩衝區的內容加入
    
    # 只取前幾塊文本內容（這裡取前8塊，也可根據需求做embedding篩選）
    texts = [{"tag": "p", "text": t} for t in chunks[:8]]

    title = await page.title()
    
    return {
        "url": page.url,
        "title": title,
        "texts": texts,
        "targets": targets[:60],  # 再次限制互動元素的數量
        "paging": {"has_more": True}  # 預留分頁功能，未來可添加滾動或下一視圖的邏輯
    }

async def get_web_elements(uuid: str) -> str:
    page = current_pages.get(uuid)
    if not page: return f'找不到任何uuid為 `{uuid}` 的page，請先使用 `goto_page` 取得正確的uuid'

    return str(await collect_view(page))