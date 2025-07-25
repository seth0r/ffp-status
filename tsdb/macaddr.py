from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import tsdb

class MacAddr(tsdb.Base):
    __tablename__ = "macaddrs"

    nodeid: Mapped[str] = mapped_column( ForeignKey("nodes.nodeid", ondelete="CASCADE") )
    mac: Mapped[str] = mapped_column( String(17), primary_key=True )

    node: Mapped["Node"] = relationship(back_populates="macaddrs")
