from dataclasses import dataclass
from typing import Optional
from .mood import Moods
from .types import *


@dataclass
class Status:
    energy: float = 1.0
    mood: Moods = Moods()

    pre_mode: Optional[MODE_TYPE] = None
    mode: MODE_TYPE = 'learning'
