from unconstrained.prelude import *

def test_seq_ints():
    assert seq(int, 1,[2,3,4]) == [1,2,3,4]

def test_seq_string():
    assert seq(str, "a", "b", "cde") == ['a','b','cde']

def test_seq_map():
    assert seq(str, "a", "b", "cde").map(len) == [1,1,3]