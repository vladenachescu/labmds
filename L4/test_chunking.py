from hypothesis import given, assume
from hypothesis import strategies as st
from chunking import chunk, flatten

sizes = st.integers(min_value=1, max_value=50)

@given(st.lists(st.integers()), sizes)
def test_roundtrip(lst, n):
    assert flatten(chunk(lst, n)) == lst

@given(st.lists(st.integers()), sizes)
def test_all_chunks_correct_size(lst, n):
    chunks = chunk(lst, n)
    for c in chunks[:-1]:
        assert len(c) == n
    if chunks:
        assert 1 <= len(chunks[-1]) <= n

@given(st.lists(st.integers()), sizes)
def test_number_of_chunks(lst, n):
    import math
    chunks = chunk(lst, n)
    if not lst:
        assert chunks == []
    else:
        assert len(chunks) == math.ceil(len(lst) / n)

@given(st.lists(st.integers()), sizes)
def test_total_elements(lst, n):
    chunks = chunk(lst, n)
    assert sum(len(c) for c in chunks) == len(lst)

@given(st.lists(st.lists(st.integers(), max_size=10), max_size=10))
def test_flatten_then_chunk_preserves_elements(lst_of_lsts):
    flat = flatten(lst_of_lsts)
    assert flat == [x for sub in lst_of_lsts for x in sub]

def test_chunk_empty():
    assert chunk([], 3) == []

def test_flatten_empty():
    assert flatten([]) == []
    assert flatten([[], [], []]) == []
