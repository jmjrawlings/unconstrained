from .prelude import *
from typing import Optional
from sqlmodel import Field, Relationship, create_engine, SQLModel, Session, MetaData
   

def primary_key(**kwargs):
    return Field(default=None, primary_key=True, **kwargs)


def foreign_key(key, **kwargs):
    return Field(default=None, foreign_key=key, **kwargs)


def backref(name, **kwargs):
    return Relationship(back_populates=name, **kwargs)



def make_engine(path = None, echo=True, model=SQLModel):
    if not path:
        url = 'sqlite://'
    else:
        url = f"sqlite:///{path}"
    
    log.info(f'Creating datbase at {url}')
    engine = create_engine(url,echo=echo)
    model.metadata.create_all(engine)
    return engine
