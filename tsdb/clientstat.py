from typing import Optional
from sqlalchemy.orm import Mapped
import tsdb

class ClientStat(tsdb.Stat,tsdb.Base):
    total: Mapped[Optional[int]]
    wifi: Mapped[Optional[int]]
    wifi24: Mapped[Optional[int]]
    wifi5: Mapped[Optional[int]]
    owe: Mapped[Optional[int]]
    owe24: Mapped[Optional[int]]
    owe5: Mapped[Optional[int]]
