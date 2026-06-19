import math

def chunk(lst, n):
    """Split lst into consecutive groups of n elements.
    The last group may be shorter.
    chunk([1,2,3,4,5], 2) -> [[1,2], [3,4], [5]]
    """
    if n <= 0:
        raise ValueError("Group size must be positive")
    if not lst:
        return []
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def flatten(lst_of_lsts):
    """Concatenate a list of lists into a single list.
    flatten([[1,2], [3,4], [5]]) -> [1,2,3,4,5]
    """
    result = []
    for sub in lst_of_lsts:
        result.extend(sub)
    return result
