import pytest
from hypothesis import given, assume
from hypothesis import strategies as st
from utils import clamp, merge_sorted, parse_pair, unique_sorted, unique_sorted_buggy

# === clamp tests ===
def test_clamp_inside():
    assert clamp(5, 1, 10) == 5

def test_clamp_below():
    assert clamp(0, 1, 10) == 1

def test_clamp_above():
    assert clamp(12, 1, 10) == 10

def test_clamp_boundary_lo():
    assert clamp(1, 1, 10) == 1

def test_clamp_boundary_hi():
    assert clamp(10, 1, 10) == 10

def test_clamp_equal_bounds():
    assert clamp(3, 5, 5) == 5
    assert clamp(7, 5, 5) == 5

@given(st.integers(), st.integers(), st.integers())
def test_clamp_hypothesis(x, lo, hi):
    assume(lo <= hi)
    res = clamp(x, lo, hi)
    assert lo <= res <= hi
    if lo <= x <= hi:
        assert res == x
    assert clamp(res, lo, hi) == res

# === merge_sorted tests ===
def test_merge_sorted_normal():
    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]

def test_merge_sorted_empty_one():
    assert merge_sorted([], [1, 2, 3]) == [1, 2, 3]
    assert merge_sorted([1, 2, 3], []) == [1, 2, 3]

def test_merge_sorted_empty_both():
    assert merge_sorted([], []) == []

def test_merge_sorted_duplicates():
    assert merge_sorted([1, 2, 2], [2, 3]) == [1, 2, 2, 2, 3]

@given(st.lists(st.integers()).map(sorted), st.lists(st.integers()).map(sorted))
def test_merge_sorted_hypothesis(a, b):
    res = merge_sorted(a, b)
    assert len(res) == len(a) + len(b)
    assert res == sorted(res)
    assert sorted(res) == sorted(a + b)

# === parse_pair tests ===
def test_parse_pair_valid():
    assert parse_pair("3:5") == (3, 5)
    assert parse_pair("-1:10") == (-1, 10)

def test_parse_pair_no_separator():
    with pytest.raises(ValueError):
        parse_pair("hello")

def test_parse_pair_too_many_separators():
    with pytest.raises(ValueError):
        parse_pair("1:2:3")

def test_parse_pair_non_int():
    with pytest.raises(ValueError):
        parse_pair("a:b")

# === unique_sorted tests ===
def test_unique_sorted_normal():
    assert unique_sorted([3, 1, 2, 1, 3]) == [1, 2, 3]

def test_unique_sorted_empty():
    assert unique_sorted([]) == []

def test_unique_sorted_no_dupes():
    assert unique_sorted([1, 2, 3]) == [1, 2, 3]

def test_unique_sorted_buggy_exposes_bug():
    # Input with 3 consecutive identical elements after sorting
    test_input = [1, 1, 1]
    
    # The buggy implementation fails to remove all duplicates
    buggy_res = unique_sorted_buggy(test_input)
    assert buggy_res != [1]  # It leaves [1, 1]
    
    # The correct implementation succeeds
    correct_res = unique_sorted(test_input)
    assert correct_res == [1]
