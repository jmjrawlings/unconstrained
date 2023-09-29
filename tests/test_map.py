from unconstrained import *

@define
class Item(BaseModel):
    name : str = string_field()

def item(name):
    return Item(name=name)

def test_map_with_id_as_key():
    cls = Map.from_id(Item)
    map = cls()
    map.add(item("A"))
    map.add(item("B"))
    map.add(item("C"), item("D"))
    map.add([item("A")])
    assert [i.name for i in map] == ["A","B","C","D", "A"]

def test_map_with_property_as_key():
    cls = Map.module(str, Item, lambda x: x.name)
    map = cls()
    map.add(item("A"))
    map.add(item("B"))
    map.add(item("C"), item("D"))
    map.add([item("A")])
    assert map.keys == ["A","B","C","D"]

def test_map_modules_are_cached():
    get_key = lambda x: x.name
    clsA = Map.module(str, Item, get_key)
    clsB = Map.module(str, Item, get_key)
    assert id(clsA) == id(clsB)
