from unconstrained import *

def test_create_multiple_engines():
            
    from examples import queens
    engine = db.create_engine(queens.Model, echo=True)

    from examples import nurse_rostering
    engine = db.create_engine(nurse_rostering.Model, echo=True)    