from typing import Optional
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import SmallInteger
import tsdb

class NodeStat(tsdb.Stat,tsdb.Base):
    gateway_tq: Mapped[Optional[int]] = mapped_column( SmallInteger )
    rootfs_usage: Mapped[Optional[float]]
    uptime: Mapped[Optional[float]]
    idletime: Mapped[Optional[float]]
    loadavg: Mapped[Optional[float]]
    proc_running: Mapped[Optional[int]] = mapped_column( SmallInteger )
    proc_total:   Mapped[Optional[int]] = mapped_column( SmallInteger )
    other: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )
