def binary_search(left, right, truth_func, left_value, **kwargs):
    while left < right - 1:
        x = (right + left) // 2
        if truth_func(x, **kwargs) == left_value:
            left = x
        else:
            right = x
    return left + 1  # first one that is not left value
