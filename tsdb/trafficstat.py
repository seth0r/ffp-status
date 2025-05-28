from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger
import tsdb

class TrafficStat(tsdb.Stat,tsdb.Base):
    rx_bytes: Mapped[int] = mapped_column( BigInteger )
    rx_pkgs:  Mapped[int] = mapped_column( BigInteger )
    tx_bytes:   Mapped[int] = mapped_column( BigInteger )
    tx_pkgs:    Mapped[int] = mapped_column( BigInteger )
    tx_dropped: Mapped[int] = mapped_column( BigInteger )
    fw_bytes: Mapped[int] = mapped_column( BigInteger )
    fw_pkgs:  Mapped[int] = mapped_column( BigInteger )
    mgmt_rx_bytes: Mapped[int] = mapped_column( BigInteger )
    mgmt_rx_pkgs:  Mapped[int] = mapped_column( BigInteger )
    mgmt_tx_bytes: Mapped[int] = mapped_column( BigInteger )
    mgmt_tx_pkgs:  Mapped[int] = mapped_column( BigInteger )
