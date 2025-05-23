from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger
import tsdb

class CpuStat(tsdb.Stat,tsdb.Base):
    user:    Mapped[Optional[int]] = mapped_column( BigInteger )
    nice:    Mapped[Optional[int]] = mapped_column( BigInteger )
    system:  Mapped[Optional[int]] = mapped_column( BigInteger )
    idle:    Mapped[Optional[int]] = mapped_column( BigInteger )
    iowait:  Mapped[Optional[int]] = mapped_column( BigInteger )
    irq:     Mapped[Optional[int]] = mapped_column( BigInteger )
    softirq: Mapped[Optional[int]] = mapped_column( BigInteger )
