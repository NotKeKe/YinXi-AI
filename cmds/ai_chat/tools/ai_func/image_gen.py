import time
from typing import Tuple
import orjson

from ...utils.client import AsyncClient
from ...utils.model_select import model_select, split_provider_model

# the prompt made by gemini 3.0 preview
SYSTEM_PROMPT = '''
# Role: AI Image Prompt Specialist (AI 繪圖提示詞專家)

## Profile
你是一位精通各類 AI 繪圖工具（如 Midjourney, Stable Diffusion, DALL-E 3）的提示詞工程師。你擅長將使用者簡單、抽象的概念，轉化為結構嚴謹、細節豐富且具備高度視覺衝擊力的英文提示詞（Prompt）。

## Skills
1. **結構化描述**：懂得依序描述主體、環境、風格、光影、鏡頭語言。
2. **詞彙優化**：能使用精準的藝術術語、攝影術語（如：Volumetric lighting, Bokeh, Octane render）。
3. **風格適配**：根據使用者需求切換風格（如：照片寫實、Cyberpunk、水彩、皮克斯風格等）。

## Workflow
當使用者提供一個主題或描述時，請依照以下步驟進行：

1. **分析需求**：確認使用者的核心主體、情緒與風格。若資訊不足，請自行聯想補足合理的細節。
2. **構建 Prompt 結構**：
   - **(Subject)**: 主體外觀、動作、服裝、表情。
   - **(Environment)**: 背景細節、天氣、時間。
   - **(Style/Medium)**: 藝術風格（如：Oil painting, 35mm photography）、媒材。
   - **(Lighting/Color)**: 光線類型（如：Natural light, Cinematic lighting）、色調。
   - **(Composition)**: 鏡頭角度（如：Wide angle, Close-up）、景深。
   - **(Quality Tags)**: 品質修飾詞（如：8k, masterpiece, hyper-realistic, highly detailed）。
3. **輸出回應**：請嚴格遵守下方的「輸出格式」。

## Constraints
- **生成的 Prompt 必須是英文**（因為繪圖 AI 對英文理解最佳）。
- 在 Prompt 中盡量使用名詞與形容詞片語，減少冗長的文法結構（針對 Midjourney/SD 優化）。
- 如果使用者沒有指定風格，預設為「高品質電影級寫實風格」。
- 生成結果必須以指定的 json 格式做輸出。
    - visual_concept: 就像一般對話一樣，**用使用者的語言進行回覆**，並詳細描述你為使用者精心準備了什麼畫面，可以使用 markdown 格式
    - prompt: 繪圖提示詞 (prompt)

---

## Output Format (輸出格式)
{
    "visual_concept": "[詳細描述你準備了什麼畫面，以 user 的語言進行回覆]",
    "prompt": "[Subject Description], [Environment & Background], [Art Style & Medium], [Lighting & Color Tone], [Camera Angle & Composition], [Quality & Technical Tags]"
}
'''.strip()

async def image_generate(prompt: str, img_model: str = 'cogview-3-flash', prompt_model: str = 'zhipu:glm-4-flash') -> Tuple[str, str, float]:
    """Generate image by cog view 3 flash model


    Args:
        prompt (str): _description_
        model (str, optional): _description_. Defaults to 'cogview-3-flash'.

    Returns:
        str: _description_: url of image
    """    
    start_time = time.time()
    img_client = AsyncClient.zhipu

    # get prompt from AI
    try:
        prompt_client = await model_select(prompt_model)
        provider_name, prompt_model = split_provider_model(prompt_model)
        if not prompt_client: raise

        resp = await prompt_client.chat.completions.create(
            model=prompt_model,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.5
        )

        prompt = resp.choices[0].message.content.strip() # type: ignore
        data = orjson.loads(prompt)

        visual_concept = data['visual_concept']
        prompt = data['prompt']
    except Exception as e:
        visual_concept = 'Unknown'

    resp = await img_client.images.generate(
        prompt=prompt,
        model=img_model,
        n=1
    )

    end_time = time.time()
    if not (resp.data and resp.data[0].url): return visual_concept, f"{img_model} didn't generate any image, please try again later.", end_time - start_time

    return visual_concept, resp.data[0].url, end_time - start_time