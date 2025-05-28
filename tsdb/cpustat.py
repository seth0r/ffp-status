from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger
import tsdb

class CpuStat(tsdb.Stat,tsdb.Base):
    user:    Mapped[int] = mapped_column( BigInteger )
    nice:    Mapped[int] = mapped_column( BigInteger )
    system:  Mapped[int] = mapped_column( BigInteger )
    idle:    Mapped[int] = mapped_column( BigInteger )
    iowait:  Mapped[int] = mapped_column( BigInteger )
    irq:     Mapped[int] = mapped_column( BigInteger )
    softirq: Mapped[int] = mapped_column( BigInteger )
