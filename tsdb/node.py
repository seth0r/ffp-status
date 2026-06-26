import datetime
from sqlalchemy_json import NestedMutableJson
from typing import List
from typing import Optional
from sqlalchemy import String, REAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
import tsdb

domain_map = {
    "pdm_bbgnord_nosae"     : 'Potsdam - Babelsberg Nord',
    "pdm_bbgsued_nosae"     : 'Potsdam - Babensberg Sued',
    "pdm_blnvst_nosae"      : 'Potsdam - Berliner Vorstadt',
    "pdm_bornim_nosae"      : 'Potsdam - Bornim',
    "pdm_bornstedt_nosae"   : 'Potsdam - Bornstedt',
    "pdm_brbvst_nosae"      : 'Potsdam - Brandenburger Vorstadt',
    "pdm_drewitz_nosae"     : 'Potsdam - Drewitz',
    "pdm_eiche_nosae"       : 'Potsdam - Eiche',
    "pdm_fahrland_nosae"    : 'Potsdam - Fahrland',
    "pdm_golm_nosae"        : 'Potsdam - Golm',
    "pdm_grglien_nosae"     : 'Potsdam - Gross Glienicke',
    "pdm_grube_nosae"       : 'Potsdam - Grube',
    "pdm_hbf_brau_nosae"    : 'Potsdam - Hauptbahnhof und Brauhausberg Nord',
    "pdm_hist_nosae"        : 'Potsdam - Historische Innenstadt',
    "pdm_jagvst_nosae"      : 'Potsdam - Jaegervorstadt',
    "pdm_kirchsteig_nosae"  : 'Potsdam - Kirchsteigfeld',
    "pdm_klglien_nosae"     : 'Potsdam - Klein Glienicke',
    "pdm_marquardt_nosae"   : 'Potsdam - Marquardt',
    "pdm_nauvst_nosae"      : 'Potsdam - Nauener Vorstadt',
    "pdm_nedlitz_nosae"     : 'Potsdam - Nedlitz',
    "pdm_neufahrland_nosae" : 'Potsdam - Neu Fahrland',
    "pdm_pdmwest_nosae"     : 'Potsdam - Potsdam West',
    "pdm_sacrow_nosae"      : 'Potsdam - Sacrow',
    "pdm_satzkorn_nosae"    : 'Potsdam - Satzkorn',
    "pdm_schlaatz_nosae"    : 'Potsdam - Schlaatz',
    "pdm_stern_nosae"       : 'Potsdam - Stern',
    "pdm_teltvst_nosae"     : 'Potsdam - Teltower Vorstadt',
    "pdm_tempvst_nosae"     : 'Potsdam - Templiner Vorstadt',
    "pdm_uetz_paaren_nosae" : 'Potsdam - Uetz-Paaren',
    "pdm_waldstadt1_nosae"  : 'Potsdam - Waldstadt I und Industriegelaende',
    "pdm_waldstadt2_nosae"  : 'Potsdam - Waldstadt II',
    "pdm_zo_nuth_nosae"     : 'Potsdam - Zentrum Ost und Nuthepark',

    "umland_hvl_nosae"      : 'Umland - Havelland',
    "umland_pm_nosae"       : 'Umland - Potsdam-Mittelmark',
    "umland_tf_nosae"       : 'Umland - Teltow-Flaeming',

    "potsdam_nosae"         : 'Potsdam',
    "potsdam_umland_nosae"  : 'Potsdam Umland',
}

class Node(tsdb.Base):
    __tablename__ = "nodes"

    nodeid: Mapped[str] = mapped_column( String(12), primary_key=True )
    hostname: Mapped[str]
    last_data: Mapped[datetime.datetime] = mapped_column( index=True )
    loc_lon: Mapped[Optional[float]]
    loc_lat: Mapped[Optional[float]]
    loc_guess_lon: Mapped[Optional[float]]
    loc_guess_lat: Mapped[Optional[float]]
    contact: Mapped[Optional[str]]
    last_contact_update: Mapped[Optional[datetime.datetime]]
    network: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )
    software: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )
    uptime: Mapped[Optional[float]] = mapped_column( REAL )

    hw_model: Mapped[Optional[str]]
    hw_nproc: Mapped[Optional[int]]

    domain: Mapped[Optional[str]]

    def domain_name(self):
        return domain_map.get(self.domain,self.domain)

    settings: Mapped[dict] = mapped_column( NestedMutableJson, default=dict )

    macaddrs: Mapped[List["MacAddr"]] = relationship(
        back_populates = "node", cascade = "all, delete-orphan"
    )
    owners: Mapped[List["User"]] = relationship(
        secondary = tsdb.nodes_owners, back_populates = "nodes"
    )
