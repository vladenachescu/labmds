def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

def merge_sorted(a, b):
    result = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result

def parse_pair(s):
    """Parse 'a:b' into (int, int). Raises ValueError on bad input."""
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError(f"expected 'a:b', got '{s}'")
    return int(parts[0]), int(parts[1])

def unique_sorted_buggy(lst):
    result = sorted(lst)
    i = 0
    while i < len(result) - 1:
        if result[i] == result[i + 1]:
            result.pop(i)
        i += 1
    return result

def unique_sorted(lst):
    result = sorted(lst)
    i = 0
    while i < len(result) - 1:
        if result[i] == result[i + 1]:
            result.pop(i)
        else:
            i += 1
    return result
