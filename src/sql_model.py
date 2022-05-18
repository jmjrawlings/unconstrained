from sqlmodel import Field, SQLModel, create_engine, Relationship, Session, select


def primary_key(**kwargs):
    return Field(default=None, primary_key=True, **kwargs)


def foreign_key(key, **kwargs):
    return Field(default=None, foreign_key=key, **kwargs)


def backref(name, **kwargs):
    return Relationship(back_populates=name, **kwargs)


def make_engine(name = None, echo=True):
    if not name:
        url = 'sqlite://'
    else:
        url = f"sqlite:///{name}.db"
    
    engine = create_engine(url,echo=echo)
    SQLModel.metadata.create_all(engine)
    return engine
