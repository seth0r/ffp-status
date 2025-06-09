import datetime
from typing import Optional
from sqlalchemy.orm import relationship
from sqlalchemy import String, SmallInteger, DateTime, Column, ForeignKey, REAL
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column
import tsdb

class Link(tsdb.Stat,tsdb.Base):
    remotenodeid: Mapped[str] = mapped_column( String(12), ForeignKey("nodes.nodeid", ondelete="CASCADE"), primary_key=True )
    mac: Mapped[str] = mapped_column( String(17), ForeignKey("macaddrs.mac", ondelete="CASCADE"), primary_key=True )
    remotemac: Mapped[str] = mapped_column( String(17), ForeignKey("macaddrs.mac", ondelete="CASCADE"), primary_key=True )

    tq:       Mapped[int] = mapped_column( SmallInteger )
    lastseen: Mapped[float] = mapped_column( REAL )
    best:     Mapped[bool]

    node = relationship("Node", foreign_keys="[Link.nodeid]")
    remotenode = relationship("Node", foreign_keys=[remotenodeid])
