from typing import Optional
from sqlalchemy.orm import Mapped
import tsdb

class MemStat(tsdb.Stat,tsdb.Base):
    total:     Mapped[Optional[int]]
    free:      Mapped[Optional[int]]
    available: Mapped[Optional[int]]
    buffers:   Mapped[Optional[int]]
    cached:    Mapped[Optional[int]]
