def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.
    merge_intervals([(1, 3), (2, 5), (8, 10)]) -> [(1, 5), (8, 10)]
    merge_intervals([(1, 5), (2, 3)])           -> [(1, 5)]
    Each interval is (start, end) with start <= end.
    """
    if not intervals:
        return []
    
    # Sort intervals by their start point
    sorted_ivs = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_ivs[0]]
    
    for current in sorted_ivs[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current
        # Since they are sorted, prev_start <= curr_start.
        # They overlap or touch if curr_start <= prev_end.
        if curr_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)
            
    return merged
