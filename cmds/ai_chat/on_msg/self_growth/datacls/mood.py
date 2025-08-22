from dataclasses import dataclass
import random
import logging

from core.functions import random_bool
from .types import *

logger = logging.getLogger(__name__)

@dataclass
class Moods:
    mood: MOOD_TYPE = 'happy'

    happy: float = 0.8
    sad: float = 0.0
    tired: float = 0.0
    angry: float = 0.0

    # def get_mood(self) -> str:
    #     '''
    #     f'現在情緒: {self.mood} | 程度: {getattr(self, self.mood)}'
    #     '''
    #     return f'現在情緒: {self.mood} | 程度: {getattr(self, self.mood)}'
    
    def get_dominant_mood(self) -> str:
        '''
        獲得現在數值最高的情緒
        f'情緒: `{max_value[0]}` | 數值: `{max_value[1]}`'
        '''
        vlaue_moods = [(mood, getattr(self, mood)) for mood in moods]
        max_value = max(vlaue_moods, key=lambda x: x[1])
        return f'情緒: `{max_value[0]}` | 數值: `{max_value[1]}`'
    
    def mood_decrease_task(self, num: float = 0.02): # 應該要搭配 task 使用
        """應與 task 搭配使用，除了被 LLM 調整至低於 0.5 的情緒以外，其他情緒最低只會降到 0.5

        Args:
            num (float, optional): 要減少多少. Defaults to 0.02.
        """        
        for mood in moods:
            curr_attr = getattr(self, mood)
            if curr_attr < 0.5: continue

            setattr(self, mood, max(0.5, getattr(self, mood) - num))

    def to_json(self) -> dict:
        return {mood: getattr(self, mood) for mood in moods}
    
    # 影響情緒的行為
    def called_tool(self, mode: MODE_TYPE, returned_text: str):
        if mode not in modes: return 'Not available mode'

        self.tired += 0.03
        if 'error' in returned_text.lower():
            self.angry += 0.02
            self.sad += 0.01
            self.happy -= 0.01
        else:
            if mode == 'chatting': # 聊天可以更影響情緒
                self.happy += 0.03
                self.sad -= 0.03
                self.tired -= 0.01 # 他其實是E人所以聊天不會累 (?
            else:
                self.happy += 0.01
                self.sad -= 0.01
    
    
    def random_mood(self) -> str | None:
        '''
        在當前情緒數值 <= 20% 時，先重製當前情緒為一個新值(介於50~80)，再將現在的情緒文字改為一個新的情緒。
        '''
        if getattr(self, self.mood) <= 0.2:
            if random_bool(0.2): # 20% 機率改變情緒
                setattr(self, self.mood, (random.randint(50, 80) / 100)) # 重製開心為50~80%，傷心則使用原始值

                num: int = -1

                while True:
                    num = random.randrange(0, len(moods))    # 要改為哪個情緒

                    if num != moods.index(self.mood):
                        break

                self.mood = moods[num]

                string = f'已改變情緒，{self.get_mood()}'
                logger.info(string)
                return string
    
    # llm tool
    def change_mood(self, mood: MOOD_TYPE, value: float) -> str:
        if not hasattr(self, mood):
            return f'{mood} 不在允許的情緒內'
        if value > 1 or value < -1:
            return f'value 是一個小數點，只能 <= 1 or >= -1，你卻使用了 `{value}`'
            
        new_value = max(0, getattr(self, mood) + value)
        new_value = min(new_value, 1)
        setattr(self, mood, new_value)

        return f'成功將 {mood} 增加 {value} 點, 現在的狀態為 {self.get_mood()}'