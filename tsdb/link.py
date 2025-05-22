import datetime
from typing import Optional
from sqlalchemy.orm import relationship
from sqlalchemy import String, SmallInteger, DateTime, Column, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column
import tsdb

class Link(tsdb.Base):
    __tablename__ = "links"
    __table_args__ = ({
        'timescaledb_hypertable':{
            'time_column_name': 'timestamp'
        }
    })

    timestamp = Column(
        DateTime(), default=datetime.datetime.now, primary_key=True
    )
 
    lnodeid: Mapped[str] = mapped_column( String(12), ForeignKey("nodes.nodeid", ondelete="CASCADE"), primary_key=True )
    rnodeid: Mapped[str] = mapped_column( String(12), ForeignKey("nodes.nodeid", ondelete="CASCADE"), primary_key=True )
    lmac: Mapped[str] = mapped_column( String(17), ForeignKey("macaddrs.mac", ondelete="CASCADE"), primary_key=True )
    rmac: Mapped[str] = mapped_column( String(17), ForeignKey("macaddrs.mac", ondelete="CASCADE"), primary_key=True )

    tq:       Mapped[Optional[int]] = mapped_column( SmallInteger )
    lastseen: Mapped[Optional[float]]
    best:     Mapped[Optional[bool]]

    lnode = relationship("Node", foreign_keys=[lnodeid])
    rnode = relationship("Node", foreign_keys=[rnodeid])
