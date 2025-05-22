from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger
import tsdb

class CpuStat(tsdb.Stat,tsdb.Base):
    cat: Mapped[str] = mapped_column( primary_key=True )
    num: Mapped[Optional[int]] = mapped_column( BigInteger )
