from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
import tsdb

class ConnStat(tsdb.Stat,tsdb.Base):
    l3proto: Mapped[str] = mapped_column( primary_key=True )
    l4proto: Mapped[str] = mapped_column( primary_key=True )
    num: Mapped[int] = mapped_column( default=0 )
