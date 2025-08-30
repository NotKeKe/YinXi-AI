import asyncio
import logging
from discord import Message
from discord.ext import commands
from qdrant_client.models import Filter, MatchValue, FieldCondition
from datetime import timezone, timedelta

from ..chat.chat import Chat
from ..utils.prompt import get_single_default_system_prompt
from ..utils import to_user_message, to_assistant_message

from cmds.vector.call import search, upsert

from core.qdrant import QdrantCollectionName
from core.classes import get_bot

logger = logging.getLogger(__name__)

class YinXiRun:
    def __init__(self, ctx: commands.Context):
        self.model = 'lmstudio:qwen/qwen3-14b'
        self.ctx = ctx

        self.client = Chat(model=self.model, ctx=ctx)
        self.history = []
        self.task: asyncio.Task = None

    async def run(self):
        try:
            # history
            await self.get_passed_history() # Get history snippet from Qdrant
            await self.get_channel_history()

            # decide whether to response user (only work in a server)
            if self.ctx.guild:
                await self.client.re_system_prompt(await get_single_default_system_prompt('yinxi_should_response')) #TODO
                result = await self.decide_if_resp()
                if not result: return

            # system prompt & resp style
            system_prompt = await get_single_default_system_prompt('yinxi_chat') #TODO
            resp_example = await self.get_response_example() # also add to system prompt
            system_prompt = system_prompt.format(resp_example=resp_example)

            # call llm
            await self.call()
        except asyncio.CancelledError:
            return
        except:
            logger.error('Error accured at YinXi run: ', exc_info=True)

    async def get_passed_history(self):
        '''
        會將 history 當中的第一則訊息設置為 user message
        '''
        filter = Filter(
            must=[
                FieldCondition(key='channelID', match=MatchValue(value=self.ctx.channel.id))
            ]
        )
        payload = await search(self.ctx.message.content, QdrantCollectionName.yinxi_passed_history, filter)
        self.history.append(to_user_message(
            '\n\n'.join([
                f'<discord_message channelId={item.get('channelID')} userName={item.get('userName')} userId={item.get('userID')} messageId={item.get('messageID')} time={item.get('time')}> {item.get('text')} </discord_message>'
                for item in payload
            ])
        ))

    async def get_channel_history(self):
        channel = self.ctx.channel
        limit = 10

        histories = []
        messages = [m async for m in channel.history(limit=limit+5)]
        messages.reverse()
        pre = str()

        bot = get_bot()
        
        for m in messages:
            if not m.content: continue

            if m.author == bot.user:
                if m.content == '嘗試重啟bot...': continue
                if pre == 'bot':
                    histories[-1]['content'] += m.content + '\n'
                else:
                    histories.extend(to_assistant_message(m.content + '\n'))
                pre = 'bot'
            else:
                if m.content.startswith(']'): continue

                string_format = '<discord_message channelId={channelId} userName={userName} userId={userId} messageId={messageId} time={time}> {content} </discord_message>'

                time = self.ctx.message.created_at.astimezone(timezone(timedelta(hours=8))).strftime("%Y/%m/%d %H:%M:%S")

                content = string_format.format(
                    channelId=m.channel.id, 
                    userName=m.author.name, 
                    userId=m.author.id, 
                    messageId=m.id, 
                    time=time, 
                    content=m.content
                ) 
                
                if pre == 'user':
                    histories[-1]["content"] = content + '\n'
                else:
                    histories.extend(to_user_message(content))
                pre = 'user'

        return histories[-(limit):]

    async def decide_if_resp(self) -> bool:
        time = self.ctx.message.created_at.astimezone(timezone(timedelta(hours=8))).strftime("%Y/%m/%d %H:%M:%S")
        think, result, history = self.client.chat(
            prompt=f'請判斷以下句子是否需要回覆: <discord_message channelId={self.ctx.channel.id} userName={self.ctx.author.name} userId={self.ctx.author.id} messageId={self.ctx.message.id} time={time}> {self.ctx.message.content} </discord_message>',
            is_enable_tools=False,
            max_completion_tokens=1000,
            if_get_extra_user_info=False
        )
        return result == 'True'
    
    async def get_response_example(self) -> str:
        payload = await search(self.ctx.message.content, QdrantCollectionName.yinxi_response_example, num=10)
        return '\n'.join([p['text'] for p in payload])
        
    async def call(self):
        think, result, self.history = await self.client.chat(
            self.ctx.message.content,
            history=self.history,
            temperature=1.2,
            repeat_penalty=1.3,
            frequency_penalty=0.8,
            presence_penalty=1.0,
        )