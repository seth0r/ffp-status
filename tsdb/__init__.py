import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session as SQLSession

# declarative base class
class Base(DeclarativeBase):
    pass

engine = create_engine(os.getenv( "TIMESCALEDB_URI" ))

def create():
    Base.metadata.create_all(engine)

def getSess():
    return SQLSession(engine)

__all__ = []

import pkgutil
import inspect
import time
import logging
import os

DEBUG = os.getenv("DEBUG","0").lower() in ["yes","true","on","1"]

logging.basicConfig()
logger = logging.getLogger("myapp.sqltime")
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARN)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger.debug("Start Query: %s", statement)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger.debug("Query Complete!")
    logger.debug("Total Time: %f", total)

modules = []
lastn = None
maxtrys = len(list( pkgutil.walk_packages(__path__) ))
while True:
    for loader, mname, is_pkg in pkgutil.walk_packages(__path__):
        if mname in modules:
            continue
        try:
            if DEBUG:
                print("Trying to load %s..." % mname, end=" ")
            module = loader.find_spec(mname).loader.load_module(mname)
            for name, value in inspect.getmembers(module):
                if name.startswith('__'):
                    continue
                globals()[name] = value
                __all__.append(name)
            modules.append(mname)
            if lastn == mname:
                lastn = None
            if DEBUG:
                print("loaded.")
        except (NameError,AttributeError) as ne:
            if DEBUG:
                print( ne )
            if mname == lastn:
                raise
            lastn = mname
    if lastn is None:
        break
    elif maxtrys <= 0:
        raise
    maxtrys -= 1
