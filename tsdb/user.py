import datetime
from sqlalchemy_json import MutableJson,NestedMutableJson
from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
import tsdb

class User(tsdb.Base):
    __tablename__ = "users"

    userid: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]
    active: Mapped[bool] = mapped_column( default=True )
    pwhash: Mapped[Optional[str]]
    pwtoken: Mapped[Optional[str]]
    pwtokenexpire: Mapped[Optional[datetime.datetime]]

    mails: Mapped[list] = mapped_column( MutableJson, default=list )

    settings: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )

    sessions: Mapped[List["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    nodes: Mapped[List["Node"]] = relationship(
        secondary = tsdb.nodes_owners, back_populates = "owners"
    )
