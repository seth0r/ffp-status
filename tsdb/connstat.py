from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import REAL
import tsdb

class ConnStat(tsdb.Stat,tsdb.Base):
    l3proto: Mapped[str] = mapped_column( primary_key=True )
    l4proto: Mapped[str] = mapped_column( primary_key=True )
    value: Mapped[int] = mapped_column( REAL, default=0.0 )
