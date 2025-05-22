from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import SmallInteger
import tsdb

class ClientStat(tsdb.Stat,tsdb.Base):
    total:  Mapped[int] = mapped_column( SmallInteger, default=0 )
    wifi:   Mapped[int] = mapped_column( SmallInteger, default=0 )
    wifi24: Mapped[int] = mapped_column( SmallInteger, default=0 )
    wifi5:  Mapped[int] = mapped_column( SmallInteger, default=0 )
    owe:    Mapped[int] = mapped_column( SmallInteger, default=0 )
    owe24:  Mapped[int] = mapped_column( SmallInteger, default=0 )
    owe5:   Mapped[int] = mapped_column( SmallInteger, default=0 )
