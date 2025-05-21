from typing import Optional
from sqlalchemy.orm import Mapped
import tsdb

class TrafficStat(tsdb.Stat,tsdb.Base):
    rx_bytes: Mapped[Optional[int]]
    rx_pkgs: Mapped[Optional[int]]
    tx_bytes: Mapped[Optional[int]]
    tx_pkgs: Mapped[Optional[int]]
    tx_dropped: Mapped[Optional[int]]
    fw_bytes: Mapped[Optional[int]]
    fw_pkgs: Mapped[Optional[int]]
    mgmt_rx_bytes: Mapped[Optional[int]]
    mgmt_rx_pkgs: Mapped[Optional[int]]
    mgmt_tx_bytes: Mapped[Optional[int]]
    mgmt_tx_pkgs: Mapped[Optional[int]]
