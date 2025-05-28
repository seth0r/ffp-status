from typing import Optional
from sqlalchemy.orm import Mapped
import tsdb

class MemStat(tsdb.Stat,tsdb.Base):
    total:     Mapped[int]
    free:      Mapped[int]
    available: Mapped[int]
    buffers:   Mapped[int]
    cached:    Mapped[int]
