from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import REAL
import tsdb

class ClientStat(tsdb.Stat,tsdb.Base):
    total:  Mapped[float] = mapped_column( REAL, default=0.0 )
    wifi:   Mapped[float] = mapped_column( REAL, default=0.0 )
    wifi24: Mapped[float] = mapped_column( REAL, default=0.0 )
    wifi5:  Mapped[float] = mapped_column( REAL, default=0.0 )
    owe:    Mapped[float] = mapped_column( REAL, default=0.0 )
    owe24:  Mapped[float] = mapped_column( REAL, default=0.0 )
    owe5:   Mapped[float] = mapped_column( REAL, default=0.0 )
