from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Relationship, Session, select
    

def primary_key(**kwargs):
    return Field(default=None, primary_key=True, **kwargs)


def foreign_key(key, **kwargs):
    return Field(default=None, foreign_key=key, **kwargs)


def backref(name, **kwargs):
    return Relationship(back_populates=name, **kwargs)


def make_engine(path = None, echo=True):
    if not path:
        url = 'sqlite://'
    else:
        url = f"sqlite:///{path}"
    
    engine = create_engine(url,echo=echo)
    SQLModel.metadata.create_all(engine)
    return engine


class SQLTable(SQLModel):
    """
    Convenience class so we don't 
    have to define the primary key over
    and over        
    """
    id : Optional[int] = primary_key()

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)