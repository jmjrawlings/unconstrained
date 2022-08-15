from unconstrained.prelude import *


def test_to_list():
    assert to_list(1,[2,3,4]) == [1,2,3,4]
    assert to_list((1,2,3),(3,2,1)) == [1,2,3,3,2,1]
    assert to_list("a", "b", "cde") == ['a','b','cde']
    assert to_list("a", "b", "cde", ignore_types=[]) == ['a','b','c','d','e']
