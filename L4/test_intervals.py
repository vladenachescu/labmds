from hypothesis import given
from hypothesis import strategies as st
from intervals import merge_intervals

interval = st.tuples(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100),
).map(lambda t: (min(t), max(t)))

intervals = st.lists(interval, max_size=20)

def points_covered(ivs):
    return {x for a, b in ivs for x in range(a, b + 1)}

@given(intervals)
def test_output_sorted(ivs):
    result = merge_intervals(ivs)
    starts = [a for a, _ in result]
    assert starts == sorted(starts)

@given(intervals)
def test_output_non_overlapping(ivs):
    result = merge_intervals(ivs)
    for i in range(len(result) - 1):
        assert result[i][1] < result[i + 1][0]

@given(intervals)
def test_coverage_preserved(ivs):
    assert points_covered(ivs) == points_covered(merge_intervals(ivs))

@given(intervals)
def test_idempotent(ivs):
    once = merge_intervals(ivs)
    twice = merge_intervals(once)
    assert once == twice

@given(intervals)
def test_each_output_interval_valid(ivs):
    for a, b in merge_intervals(ivs):
        assert a <= b

@given(intervals, intervals)
def test_merge_union(ivs1, ivs2):
    """Merging the concatenation covers the union of both."""
    combined = merge_intervals(ivs1 + ivs2)
    separate = points_covered(merge_intervals(ivs1)) | points_covered(merge_intervals(ivs2))
    assert points_covered(combined) == separate

def test_empty():
    assert merge_intervals([]) == []
