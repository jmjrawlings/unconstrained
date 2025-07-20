"""
Tests for domain modelling with attrs via BaseModel
"""

from unconstrained import BaseModel, int_field, str_field, map_field, Id, float_field, seq_field, Seq, Map, define, UUID, Id


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
    items : Map[UUID, Item, Id] = map_field(UUID, Item, "id")
    

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

@define
class ComplexModel(BaseModel):
    a : int = int_field()
    b : float = float_field(default=23.8)
    c : str = str_field(default="xd")    
    d : Seq[Item] = seq_field(Item)
    e : Map[UUID, Item, Id] = map_field(UUID, Item, "id")


def test_model_serde():
    m1 = ComplexModel()
    m1.e.add(Item(name="A"))
    m1.e.add(Item(name="B"))
    m1.e.add(Item(name="C"))
    m1.d = m1.e.vals

    dict1 = m1.to_dict()
    json1 = m1.to_json_string()
    
    m2 = m1.copy()
    json2 = m2.to_json_string()
    dict2 = m2.to_dict()
    
    assert json1 == json2
    assert dict1 == dict2



    

    
