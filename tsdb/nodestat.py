from typing import Optional
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import SmallInteger
import tsdb

class NodeStat(tsdb.Stat,tsdb.Base):
    gateway_tq: Mapped[int] = mapped_column( SmallInteger )
    rootfs_usage: Mapped[float]
    uptime: Mapped[float]
    idletime: Mapped[float]
    loadavg: Mapped[float]
    proc_running: Mapped[int] = mapped_column( SmallInteger )
    proc_total:   Mapped[int] = mapped_column( SmallInteger )
    other: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )
