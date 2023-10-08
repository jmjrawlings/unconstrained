"""
Tests for the map object
"""

from unconstrained import *

@define
class Item(BaseModel):
    name : str = str_field()

def item(name):
    return Item(name=name)

def test_map_with_id_as_key():
    map : Map[UUID, Item, Id] = id_map(Item)
    map.add(item("A"))
    map.add(item("B"))
    map.add(item("C"), item("D"))
    map.add([item("A")])
    assert [i.name for i in map] == ["A","B","C","D", "A"]

def test_map_with_property_as_key():
    Name = Literal["name"]
    map : Map[str, Item, Name] = Map(str, Item, "name")
    map.add(item("A"))
    map.add(item("B"))
    map.add(item("C"), item("D"))
    map.add([item("A")])
    assert map.keys == ["A","B","C","D"]