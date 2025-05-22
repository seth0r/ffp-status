from typing import Optional
from sqlalchemy.orm import Mapped
import tsdb

class SwStat(tsdb.Stat,tsdb.Base):
    domain: Mapped[Optional[str]]
    fw_base: Mapped[Optional[str]]
    fw_release: Mapped[Optional[str]]
    au_branch: Mapped[Optional[str]]
    au_enabled: Mapped[Optional[bool]]
