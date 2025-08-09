import typing
import traceback
import discord
from discord import app_commands
from discord.ext import commands

from core.functions import read_json, write_json
from core.functions import create_basic_embed, current_time
from cmds.AIsTwo.others.func import gener_title
from cmds.AIsTwo.utils import to_assistant_message, to_user_message

HISTORY_DATA_PATH = './cmds/data.json/chat_history.json'
HISTORY_DATA_FORCHANNEL_PATH = './cmds/data.json/chat_history_forchannel.json'
channel_system_prompts_PATH = './cmds/data.json/chat_channel_system_prompts.json'
channel_model_select_PATH = './cmds/data.json/chat_channel_modelSelect.json'
chat_human_PATH = './cmds/data.json/chat_human.json'
chat_human_summary_PATH = './cmds/data.json/chat_human_summary.json'
style_train_PATH = './cmds/data.json/chat_style_train.json'
personality_PATH = './cmds/data.json/chat_personality.json'
weather_messages_PATH = './cmds/data.json/weather_messages.json'

class HistoryData:
    user = None
    channel = None
    channel_system_prompts = None
    channel_model_select = None
    chat_human = None
    chat_human_summary = None
    style_train = None
    personality = None
    weather_messages = None

    if_new_data = {
        "user": False,
        "channel": False,
        "channel_system_prompts": False,
        "channel_model_select": False,
        "chat_human": False,
        "chat_human_summary": False,
        "style_train": False,
        "personality": False,
        "weather_messages": False
    }

    @classmethod
    def initdata(cls):
        if cls.user is None:
            cls.user = read_json(HISTORY_DATA_PATH)
        if cls.channel is None:
            cls.channel = read_json(HISTORY_DATA_FORCHANNEL_PATH)
        if cls.channel_system_prompts is None:
            cls.channel_system_prompts = read_json(channel_system_prompts_PATH)
        if cls.channel_model_select is None:
            cls.channel_model_select = read_json(channel_model_select_PATH)
        if cls.chat_human is None:
            cls.chat_human = read_json(chat_human_PATH)
        if cls.style_train is None:
            cls.style_train = read_json(style_train_PATH)
        if cls.personality is None:
            cls.personality = read_json(personality_PATH)
        if cls.weather_messages is None:
            cls.weather_messages = read_json(weather_messages_PATH)
        if cls.chat_human_summary is None:
            cls.chat_human_summary = read_json(chat_human_summary_PATH)
    
    @classmethod
    def writeUser(cls, data=None):
        if data is not None:
            cls.user = data
        cls.if_new_data["user"] = True
        # write_json(cls.user, HISTORY_DATA_PATH)

    @classmethod
    def writeChannel(cls, data=None):
        if data is not None:
            cls.channel = data
        cls.if_new_data["channel"] = True
        # write_json(cls.channel, HISTORY_DATA_FORCHANNEL_PATH)

    @classmethod
    def writeChannelSystemPrompts(cls, data=None):
        if data is not None:
            cls.channel_system_prompts = data
        cls.if_new_data["channel_system_prompts"] = True

    @classmethod
    def writeChannelSelectModel(cls, ctx: commands.Context, model: str = None):
        if model is not None:
            cls.channel_model_select[str(ctx.channel.id)] = model
        cls.if_new_data["channel_model_select"] = True
        # write_json(cls.channel_model_select, channel_model_select_PATH)

    @classmethod
    def writeChatHuman(cls, data=None):
        if data is not None:
            cls.chat_human = data
        cls.if_new_data["chat_human"] = True
        # write_json(cls.chat_human, chat_human_PATH)

    @classmethod
    def writeChatHumanSummary(cls, data=None):
        if data is not None:
            cls.chat_human_summary = data
        cls.if_new_data["chat_human_summary"] = True

    @classmethod
    def writeStyleTrain(cls, data=None):
        if data is not None:
            cls.style_train = data
        cls.if_new_data["style_train"] = True
        # write_json(cls.style_train, style_train_PATH)

    @classmethod
    def writePersonality(cls, data=None):
        if data is not None:
            cls.personality = data
        cls.if_new_data["personality"] = True

    @classmethod
    def writeWeatherMessages(cls, data=None):
        if data is not None:
            cls.weather_messages = data
        cls.if_new_data["weather_messages"] = True

    @classmethod
    def timed_storage(cls, force=False):
        if not any(cls.if_new_data.values()) and not force:
            return
        
        if cls.if_new_data["user"]:
            write_json(cls.user, HISTORY_DATA_PATH)
        if cls.if_new_data["channel"]:
            write_json(cls.channel, HISTORY_DATA_FORCHANNEL_PATH)
        if cls.if_new_data["channel_model_select"]:
            write_json(cls.channel_model_select, channel_model_select_PATH)
        if cls.if_new_data["chat_human"]:
            write_json(cls.chat_human, chat_human_PATH)
        if cls.if_new_data["chat_human_summary"]:
            write_json(cls.chat_human_summary, chat_human_summary_PATH)
        if cls.if_new_data["style_train"]:
            write_json(cls.style_train, style_train_PATH)
        if cls.if_new_data["personality"]:
            write_json(cls.personality, personality_PATH)
        if cls.if_new_data["weather_messages"]:
            write_json(cls.weather_messages, weather_messages_PATH)
            
        # 清除已存儲的標記
        for key in cls.if_new_data:
            cls.if_new_data[key] = False

    @classmethod
    def createNewHistory(cls, userID, content, result):
        userID = str(userID)
        data = cls.user

        results = to_user_message(content) + to_assistant_message(result)

        # title = content if len(content) < 20 else content[:20]
        title = (gener_title(results) if len(content) >= 20 else content) + f'create at: {current_time()}'

        if userID not in data:
            data[userID] = {
                title: results
            }
        else:
            data[userID][title] = results

        cls.writeUser(data)

    @classmethod
    def appendHistory(cls, userID, content, result, title=None, reasoning=None):
        userID = str(userID)
        data = cls.user

        if result == '' and reasoning != None:
            result = reasoning
            reasoning = None

        if title is None or userID not in data:
            cls.createNewHistory(userID, content, result); return
    
        data[userID][title] += to_user_message(content) + to_assistant_message(result, reasoning)

        cls.writeUser(data)

    @classmethod
    def appendHistoryForChannel(cls, channelID, content, result, reasoning=None, userID=None, attachments:list=None):
        userID = int(userID)
        channelID = str(channelID)

        data = cls.channel
        if result == '' and reasoning != None:
            result = reasoning
            reasoning = None

        data[channelID] += to_user_message(content, userID, attachments) + to_assistant_message(result, reasoning)
        cls.writeChannel(data)

    @classmethod
    def appendHistoryForChatHuman(cls, channelID, content, result, reasoning=None, userID=None):
        userID = int(userID)
        channelID = str(channelID)

        data = cls.chat_human
        if channelID not in data:
            data[channelID] = []
        if result == '' and reasoning != None:
            result = reasoning
            reasoning = None

        data[channelID] += to_user_message(content, userID) + to_assistant_message(result, reasoning)
        cls.writeChatHuman(data)

    @classmethod
    def appendHistoryForStyleTrain(cls, content, result, reasoning=None):
        if result in (None, '') and reasoning in (None, ''): return 

        data  = cls.style_train
        data['data'] += to_user_message(content) + to_assistant_message(result if result not in (None, '') else reasoning)
        cls.writeStyleTrain(data)


async def chat_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    HistoryData.initdata()
    userID = str(interaction.user.id)

    data = HistoryData.user[userID]
    data = list(data.keys())
    data.reverse() #由新到舊排序
    if current:
        data = [history for history in data if current.lower().strip() in history.lower() and history != '']

    # 限制最多回傳 25 個結果
    return [app_commands.Choice(name=history, value=history) for history in data[:25] if history != '']

def create_result_embed(ctx: commands.Context, result, model):
    embed = create_basic_embed(title='AI文字生成', color=ctx.author.color)
    embed.add_field(name=' ', value=result)
    embed.set_footer(text=f'Powered by {model}')
    return embed

def get_history(ctx: commands.Context, history_title: str = None):
    if history_title is not None:
        history = HistoryData.user[str(ctx.author.id)][history_title]
    else:
        history = None

    return history