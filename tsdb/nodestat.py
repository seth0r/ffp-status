from typing import Optional
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import SmallInteger, REAL
import tsdb

class NodeStat(tsdb.Stat,tsdb.Base):
    gateway_tq: Mapped[int] = mapped_column( SmallInteger )
    rootfs_usage: Mapped[float] = mapped_column( REAL )
    uptime: Mapped[float] = mapped_column( REAL )
    idletime: Mapped[float] = mapped_column( REAL )
    loadavg: Mapped[float] = mapped_column( REAL )
    proc_running: Mapped[int] = mapped_column( SmallInteger )
    proc_total:   Mapped[int] = mapped_column( SmallInteger )
    other: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )
