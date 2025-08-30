from dataclasses import dataclass, field
from typing import Optional
from .mood import Moods
from .types import *


@dataclass
class Status:
    energy: float = 1.0
    mood: Moods = field(default_factory=Moods)

    pre_mode: Optional[MODE_TYPE] = None
    mode: MODE_TYPE = 'learning'
