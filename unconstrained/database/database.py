from ..prelude import *
import sqlmodel
from sqlmodel import Field, Relationship, SQLModel, Session
from sqlalchemy.orm import InstrumentedAttribute


def column(*args, **kwargs):
    """
    Create a normal field
    """
    return Field(*args, **kwargs)


def primary_key(**kwargs):
    """
    Create a primary key column
    """
    return Field(default=None, primary_key=True, **kwargs)


def foreign_key(key, **kwargs):
    """
    Create a foreign key column
    """
    if isinstance(key, str):
        name = key
    elif isinstance(key, InstrumentedAttribute):
        name = str(key).lower()
    else:
        raise ValueError(f'Could not get a foreign key from arg {key} of type {type(key)}')

    return Field(foreign_key=name, **kwargs)


def relation(key, **kwargs):
    """
    Create a Relationship column back populated by the key
    """

    if isinstance(key, str):
        name = key
    elif isinstance(key, InstrumentedAttribute):
        name = str(key).lower().split(".")[1]
    else:
        raise ValueError(f'Could not get a back reference key from arg {key} of type {type(key)}')

    return Relationship(
        back_populates=name, 
        # sa_relationship_kwargs=dict(lazy='joined'),
        **kwargs)


TModel = TypeVar("TModel", bound=SQLModel)


def create_engine(model: Type[TModel], path = None, echo=False, **kwargs):
    """
    Create a database engine for the given Model class.

    The database will be created at the path if given, otherwise
    an in-memory database will be used.
    """
    
    if not path:
        uri = 'sqlite://'
        log.info(f'Creating in-memory SQL engine for {model.__name__}')
    else:
        path = to_filepath(path)
        uri = f"sqlite:///{path}"
        log.info(f'Creating SQL engine for {model.__name__} at {path}')
    
    engine = sqlmodel.create_engine(uri,echo=echo, **kwargs)
    model.metadata.create_all(engine)
    return engine


def session(engine):
    """
    Create a database session for the given engine
    """
    return Session(engine)


def create_model_class():
    """
    Create a subclass of SQLModel with hashing based
    on the database id.
    """
    
    class Model(SQLModel):
        metadata = sqlmodel.MetaData()
        
        id : Optional[int] = primary_key()

        def __hash__(self):
            if not self.id:
                raise ValueError("Cannot hash a model without a database id")
            return hash(self.id)

        def __str__(self):
            if not self.id:
                return f'{self.__tablename__} (unsynced)'
            else:
                return f'{self.__tablename__} (id={self.id})'

        def __repr__(self):
            return f'<{self!s}>'
                

    return Model