import discord
from discord.ext import commands
from typing import Tuple, Union, List, Dict, Callable, Awaitable, Any
from typing import AsyncGenerator
from openai.types.chat import ChatCompletionChunk, ChatCompletion, ChatCompletionMessage
import orjson
import logging
import re
import asyncio
from openai import BadRequestError

from ..utils import model_select, to_system_message, to_user_message, get_think, clean_text, split_provider_model
from ..utils.config import base_system_prompt, summarize_history_system_prompt

# tool
from ..tools import tool_description, tool_map
from ..tools.func import search_user_long_term_memory

# long term memory
from cmds.vector.call.user_long_term_memory import long_term_memory

from core.functions import is_async, image_to_base64, current_time
from core.classes import get_bot

logger = logging.getLogger(__name__)

class Chat:
    def __init__(self, model: str = None, system_prompt: str = '', ctx: commands.Context = None):
        if not model: model = 'cerebras:qwen-3-32b'
        self.model = model.strip()
        self.ctx = ctx
        self.userID: int = ctx.author.id if ctx else None

        self.client = None

        self.system_prompt = str(base_system_prompt) if system_prompt in ('', None) else system_prompt

        self.user_info = None # 用於讓AI判別，避免重複存儲

    async def re_model(self, model: str):
        """重新選擇模型

        Args:
            model (str): 傳入模型名稱
        """        
        self.model = model
        self.client = await model_select(model)

    def re_system_prompt(self, system_prompt: str) -> bool:
        """重新設定系統提示詞


        Args:
            system_prompt (str): 系統提示詞

        Returns:
            bool: True or (False if failed)
        """        
        if not isinstance(system_prompt, str): return False

        self.system_prompt = system_prompt
        return True
    
    async def get_extra_user_info(self, user_prompt: str) -> str:
        if not self.userID: return ''

        bot = get_bot()
        name = (bot.get_user(self.userID)).global_name
        preference = None
        info = await search_user_long_term_memory(self.userID, user_prompt, 3)
        self.user_info = info

        return (
'''
## 關於 {name} 的資訊
### 注意事項 (Notice):
    1. 除非使用者明確詢問你對他的了解或對話內容確實需要這些資訊才能繼續進行（例如：根據身分給予特定回應），否則請絕對不要主動提及或重複這些個人資訊。
    2. 永遠避免「思考過程洩漏」：即使你在推理中想到「他喜歡甜品」，也不要讓這個想法出現在回應裡。
### 資訊 (Information):
- 使用者ID: `{userID}`
- 資訊: ```{info}```
'''.format(name=name, preference=preference, info=info, userID=self.ctx.author.id)
)
        #TODO

    def process_tool_decrip(self, delete_func_name: Union[str, list, None] = None):
        tmp_tools_descrip = list(tool_description)

        if not delete_func_name: return tmp_tools_descrip
        if delete_func_name == 'all': return []

        for tool in tmp_tools_descrip:
            tool_name = tool['function']['name']
            if type(delete_func_name) == list:
                if tool_name in delete_func_name:
                    delete_func_name.remove(tool_name)
                    tmp_tools_descrip.remove(tool)
                    
                    if not delete_func_name:
                        break
            elif type(delete_func_name) == str:
                if tool_name == delete_func_name: 
                    tmp_tools_descrip.remove(tool)
                    break

        return tmp_tools_descrip

    async def process_stream(self, stream: AsyncGenerator[ChatCompletionChunk, None]) -> Tuple[str, str, list]:
        think = []
        result = []
        tool_calls = []
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.tool_calls:
                # 如果有工具調用，累積工具調用資訊
                if not tool_calls:
                    tool_calls.extend([{} for _ in delta.tool_calls])
                
                for i, tool_call_chunk in enumerate(delta.tool_calls):
                    if tool_call_chunk.function.name:
                        tool_calls[i]['name'] = tool_call_chunk.function.name
                    if tool_call_chunk.function.arguments:
                        tool_calls[i].setdefault('arguments', '')
                        tool_calls[i]['arguments'] += tool_call_chunk.function.arguments
                    if tool_call_chunk.id:
                        tool_calls[i]['id'] = tool_call_chunk.id

            if delta.content:
                result.append(delta.content)
            if hasattr(delta, "reasoning"):
                if delta.reasoning:
                    think.append(delta.reasoning)

        result = ''.join(result)
        think = ''.join(think)

        think = get_think(''.join(result)) if not think else think
        result = clean_text(result)
        
        return think, result, tool_calls
    
    async def process_completion(self, response: ChatCompletion) -> Tuple[str, str, list, int]:
        think: str = ""
        result: str = ""
        tool_calls: list = []

        message: ChatCompletionMessage = response.choices[0].message

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append({
                    'id': tool_call.id,
                    'name': tool_call.function.name,
                    'arguments': tool_call.function.arguments
                })

        if message.content:
            result = message.content

        if (hasattr(message, 'reasoning_content')):
            think = message.reasoning_content
        elif (hasattr(message, 'reasoning')):
            think = message.reasoning
        else:
            think = get_think(result)

        result = clean_text(result)

        total_tokens = response.usage.total_tokens
        
        return think, result, tool_calls, total_tokens

    
    async def process_tool_calls(self, tool_calls: list, history: list, custom_tools: Dict[str, Callable[..., Union[Any, Awaitable[Any]]]] = None, include_original_tools: bool = False):
        '''Love gemini :>
        call function and add result to history
        '''
        if not (tool_calls and all('id' in tc and 'name' in tc and 'arguments' in tc for tc in tool_calls)):
            return

        assistant_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc['id'],
                    "type": "function",
                    "function": {"name": tc['name'], "arguments": tc['arguments']}
                } for tc in tool_calls
            ]
        }
        history.append(assistant_message)

        for tool_call in tool_calls:
            tool_call_id = tool_call['id']
            function_name = tool_call['name']
            function_response = "Error: An unknown error occurred."

            try:
                function_to_call = (({**custom_tools, **tool_map} if include_original_tools else custom_tools) or tool_map).get(function_name)
                if not function_to_call:
                    history.append(
                        {
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "name": function_name,
                            "content": f"Function '{function_name}' not found in tool map."
                        }
                    )
                    continue

                try:
                    function_args = orjson.loads(tool_call['arguments'])
                    if not isinstance(function_args, dict):
                        function_response = f"Error: Function arguments must be a dictionary, got {type(function_args)}"
                        continue
                except orjson.JSONDecodeError as e:
                    function_response = f"Error: Invalid JSON arguments for '{function_name}': {e}"
                    continue

                logger.info(f'`{self.model}` called `{function_name}` ({function_args})')

                if is_async(function_to_call):
                    function_response = await function_to_call(**function_args)
                else:
                    function_response = function_to_call(**function_args)

            except orjson.JSONDecodeError:
                function_response = f"Error: Failed to parse arguments for '{function_name}'. Arguments must be valid JSON."
            except (TypeError, ValueError) as e:
                function_response = f"Error: Failed to call '{function_name}'. Details: {e}"
            except Exception as e:
                function_response = f"Error: An unexpected error occurred while calling '{function_name}'. Details: {e}"
            
            # 4. 將結果添加到歷史記錄
            history.append(
                {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response), # Ensure response is a string
                }
            )

    async def process_user_prompt(self, user_prompt: str, image: discord.Attachment = None, text_file: discord.Attachment = None, url: str = None, is_vision_model: bool = False) -> list:
        image_content = None
        text_file_content = None
        if text_file:
            text_file_content = (await text_file.read()).decode('utf-8')
        if image and is_vision_model:
            image_content = await image_to_base64(image.url)
        
        prompt = (
            user_prompt,
            (f'The following is the `image url` provided by the user: ```{image.url}```' if image and not is_vision_model else ''),
            f'The following is the `url` provided by the user: `{url}`' if url else ''
            f'The following is the `file` provided by the user: ```{text_file_content}```' if text_file_content else ''
        )

        return to_user_message(('\n\n'.join(prompt)).strip(), (image_content if image_content and is_vision_model else None))
    
    async def process_input_history(self, history: list = None, is_vision_model: bool = False):
        '''處理如果content是list，且傳入模型非視覺模型 而造成的錯誤'''
        if not history: return history
        if is_vision_model: return history # 是視覺模型的話就不用管他了

        final_history = []
        for h in history:
            if h.get('role') == 'user' and isinstance(h.get('content'), list):
                h = to_user_message(str(h.get('content', [{}])[0].get('text')) + 'system deleted a image')[0]
            final_history.append(h)

        return final_history

    async def chat(
                self,
                prompt: str,
                is_vision_model: bool = False,
                model: str = None,
                temperature: float = 1.0,
                history: list = None,
                max_completion_tokens: int = None,
                top_p: float = 1.0,
                repeat_penalty: float = None,
                frequency_penalty: float = None,
                presence_penalty: float = None,

                is_enable_tools: bool = True,
                delete_tools: Union[str, list] = None,
                custom_tool_description: List[Dict[str, Union[str, Dict[str, Union[str, Dict[str, Union[str, Dict[str, Dict[str, str]], List[str]]]]]]]] = None,
                custom_tools: Dict[str, Callable[..., Union[Any, Awaitable[Any]]]] = None,
                include_original_tools: bool = False,
                tool_call_times: int = 3,

                timeout: float = None,
                url: list = None,
                image: discord.Attachment = None,
                text_file: discord.Attachment = None,
                custom_system_prompt: str = None,
                tool_choice: str = None,
                vector_database: list[str] = None
            ) -> Tuple[str, str, list]:
        if not self.client:
            if model:
                await self.re_model(model)
            else:
                self.client = await model_select(self.model)

        if not history: history = []

        provider, self.model = split_provider_model(self.model)
        if not self.model: return '', f'`{self.model}` is not available.', history

        # Openrouter 大部分模型都不支援工具調用
        if provider == 'openrouter':
            is_enable_tools = False

        extra_user_info = await self.get_extra_user_info(prompt)
        system_prompt = self.system_prompt + extra_user_info

        system = to_system_message(
            (custom_system_prompt if custom_system_prompt else system_prompt) + 
            (f'\n\n<vector_database_search_result_provided_by_user>\n{vector_database}</vector_database_search_result_provided_by_user>' if vector_database else '')
        )

        history = await self.process_input_history(history)

        history += await self.process_user_prompt(prompt, image, text_file, url, is_vision_model)

        async def call():
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=system + history,
                max_completion_tokens=max_completion_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=False,
                timeout=timeout,
                tools=((
                            custom_tool_description + self.process_tool_decrip(delete_tools)
                            if include_original_tools 
                            else custom_tool_description
                        ) 
                        or 
                        (
                            self.process_tool_decrip(delete_tools)
                            if is_enable_tools 
                            else None
                        )),
                tool_choice=tool_choice if tool_choice else ('auto' if is_enable_tools else None) ,
                **({'frequency_penalty': frequency_penalty} if frequency_penalty else {}),
                presence_penalty=presence_penalty,
                extra_body=({
                    'repeat_penalty': repeat_penalty
                }) if repeat_penalty else None
            )
            return resp
        try:
            completion = await call()
        except BadRequestError as e:
            if "Model unloaded" in str(e):
                return '', 'Model unloaded, please try again later', history
            else:
                raise

        call_times = 0

        while call_times < tool_call_times: # 3 times to call functions
            think, result, tool_calls, total_tokens = await self.process_completion(completion)
            if tool_calls:
                if provider.lower() == 'lmstudio': await asyncio.sleep(1)
                await self.process_tool_calls(tool_calls, history, custom_tools, include_original_tools)
                completion = await call()
                call_times += 1
            else:
                break

        if call_times == tool_call_times and not result: # reach limit and tool still return failed
            is_enable_tools = False
            completion = await call()
            think, result, tool_calls, total_tokens = await self.process_completion(completion)

        history.append({
            "role": "assistant",
            "content": result.strip(),
            **({'reasoning': think.strip()} if think else {})
        })

        if provider.lower() in ('ollama', 'lmstudio') and total_tokens >= 10000: await self.summarize_history(history)
        elif provider.lower() in ('lmstudio', 'cerebras') and total_tokens >= 30000: await self.summarize_history(history)
        elif total_tokens > 62000: history = await self.summarize_history(history)

        def replace_backticks_in_parentheses(s):
            '''replace "`" to "´", 避免顏文字影響 discord 輸出'''
            return re.sub(r'\(([^)]*?)\)', lambda m: '(' + m.group(1).replace('`', '´') + ')', s)
        
        if self.userID and result and self.userID:
            asyncio.create_task(long_term_memory(self.userID, prompt, result, self.user_info, self.ctx))

        return think, replace_backticks_in_parentheses(result), history
            
    async def summarize_history(self, history: list):
        ls_prompt = []
        for h in history:
            role = h.get('role', '')
            content = h.get('content', '')
            tool_calls = h.get('tool_calls', [])
            

            if role == 'user':
                ls_prompt.append(f'User: 「{content})」')
            elif role == 'assistant' and content:
                ls_prompt.append(f'Assistant: 「{content}」')
            elif role == 'assistant' and tool_calls:
                if tool_calls:
                    for t in tool_calls:
                        function = t.get('function', {})
                        name = function.get('name')
                        args = function.get('arguments')
                        ls_prompt.append(f'Assistant called a tool: {name}({args})')

        think, result, history = await self.chat(
            prompt='\n'.join(ls_prompt),
            is_enable_tools=False,
            custom_system_prompt=summarize_history_system_prompt,
            top_p=0.5
        )

        new_history = to_user_message(f'# 以下是針對先前的對話總結 (總結時間: {current_time()}):\n```{result}```')
        return new_history