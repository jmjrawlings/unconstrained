from ..prelude import *
from sqlmodel import Field, Relationship, create_engine, SQLModel, Session, MetaData
from sqlalchemy.orm import InstrumentedAttribute


def column(*args, **kwargs):
    return Field(*args, **kwargs)


def primary_key(**kwargs):
    """
    Create a primary key field
    """
    return Field(default=None, primary_key=True, **kwargs)


def foreign_key(key, **kwargs):
    """
    Create a foreign key field
    """
    if isinstance(key, str):
        name = key
    elif isinstance(key, InstrumentedAttribute):
        name = str(key).lower()
    else:
        raise ValueError(f'Could not get a foreign key from arg {key} of type {type(key)}')

    return Field(foreign_key=name, **kwargs)


def backref(key, **kwargs):
    """
    Create a Relationship field back populated by the key
    """
    if isinstance(key, str):
        name = key
    elif isinstance(key, InstrumentedAttribute):
        name = str(key).lower().split(".")[1]
    else:
        raise ValueError(f'Could not get a back reference key from arg {key} of type {type(key)}')

    return Relationship(
        back_populates=name, 
        sa_relationship_kwargs=dict(lazy='joined'),
        **kwargs)


def make_engine(path = None, echo=True, model=SQLModel):
    if not path:
        url = 'sqlite://'
    else:
        url = f"sqlite:///{path}"
    
    log.info(f'Creating datbase at {url}')
    engine = create_engine(url,echo=echo)
    model.metadata.create_all(engine)
    return engine


class Model(SQLModel):
    id : Optional[int] = primary_key()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)    
