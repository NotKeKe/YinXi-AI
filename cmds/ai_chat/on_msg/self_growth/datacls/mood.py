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

    def get_mood(self) -> str:
        return f'現在情緒: {self.mood} | 程度: {getattr(self, self.mood)}'

    def get_mood_status(self) -> str:
        return '快樂/傷心指數: ' + str({'happy': self.happy, 'sad': self.sad})
    
    
    def random_mood(self) -> str | None:
        '''
        在當前情緒數值 <= 20% 時，先重製當前情緒為一個新值(介於50~80)，再將現在的情緒文字改為一個新的情緒。
        '''
        if getattr(self, self.mood) <= 0.2:
            if random_bool(0.2): # 20% 機率改變情緒
                setattr(self, self.mood, (random.randint(50, 80) / 100)) # 重製開心為50~80%，傷心則使用原始值

                num: int = -1

                while True:
                    num = random.randrange(0, len(moods)-1)    # 要改為哪個情緒

                    if num != moods.index(self.mood):
                        break

                self.mood = moods[num]

                string = f'已改變情緒，{self.get_mood()}'
                logger.info(string)
                return string
    
    def change_mood(self, mood: MOOD_TYPE, value: int) -> str: # 以開心作為範例
        if not hasattr(self, mood):
            return f'{mood} 不在允許的情緒內'
            
        new_value = max(0, getattr(self, mood) + value)
        setattr(self, mood, new_value)
        self.mood = mood

        if new_value < 0:
            self.random_mood()

        return f'成功將 {mood} 增加 {value} 點, 現在的狀態為 {self.get_mood()}'