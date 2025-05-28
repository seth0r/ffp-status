from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
import tsdb

class SwStat(tsdb.Stat,tsdb.Base):
    domain: Mapped[str] = mapped_column( index=True )
    fw_base: Mapped[str]
    fw_release: Mapped[str] = mapped_column( index=True )
    au_branch: Mapped[str] = mapped_column( index=True )
    au_enabled: Mapped[bool] = mapped_column( index=True )
