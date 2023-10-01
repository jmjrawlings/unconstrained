"""
Tests for domain modelling with attrs via BaseModel
"""

from unconstrained import *

@define
class SimpleModel(BaseModel):
    a : int = int_field()
    c : str = str_field(default="xd")    

def test_create_simple_model():
    m = SimpleModel()
    assert m.a == 0
    assert m.c == "xd"

def test_simple_field_conversion():
    m = SimpleModel(a=1.0, c=1.0)
    assert m.a == 1
    assert m.c == '1.0'
    m.a = 1.0
    m.c = 1.0
    assert m.a == 1
    assert m.c == '1.0'

def test_copy_simple_model():
    m1 = SimpleModel()
    m2 = m1.copy()
    assert m1 == m2
     

@define
class Item(BaseModel):
    name : str = str_field()

@define
class MapModel(BaseModel):
    items : Map[id, Item] = map_field(Item)
    

def test_create_map_model():
    m = MapModel()
    assert m.items.is_empty
    
    
def test_map_model_convert():
    m = MapModel()
    items = [Item(name="A"), Item(name="B")]
    # Add items through the map
    m.items.add(items)
    ia = m.items
    assert m.items.count == 2
    assert m.items.vals[0].name == "A"

    # Construct a new map via the attrs converter
    m.items = items
    ib = m.items
    assert m.items.count == 2
    assert m.items.vals[0].name == "A"

    # The contents should be equals
    assert ia == ib
    
    # The actual containers should be differnet
    assert id(ia) != id(ib)