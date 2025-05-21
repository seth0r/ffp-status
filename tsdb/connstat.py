from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
import tsdb

class ConnStat(tsdb.Stat,tsdb.Base):
    v4_tcp: Mapped[int] = mapped_column( default=0 )
    v4_udp: Mapped[int] = mapped_column( default=0 )
    v4_icmp: Mapped[int] = mapped_column( default=0 )
    v4_unknown: Mapped[int] = mapped_column( default=0 )
    v6_tcp: Mapped[int] = mapped_column( default=0 )
    v6_udp: Mapped[int] = mapped_column( default=0 )
    v6_icmp: Mapped[int] = mapped_column( default=0 )
    v6_unknown: Mapped[int] = mapped_column( default=0 )
