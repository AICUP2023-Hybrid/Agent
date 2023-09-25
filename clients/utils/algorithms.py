def balance_two_nodes_binary_search(left, right, danger_func, **kwargs):
    d = danger_func(right - 1, **kwargs)
    if d > 0:
        return right
    while left < right - 1:
        x = (right + left) // 2
        d = danger_func(x, **kwargs)
        x += (d / 0.7) // 2
        x = int(max(left, min(right - 1, x)))
        if d <= 0:
            right = x
        else:
            left = x
    return left + 1  # first one that is not left value


def binary_search(left, right, truth_func, left_value, **kwargs):
    while left < right - 1:
        x = (right + left) // 2
        if truth_func(x, **kwargs) == left_value:
            left = x
        else:
            right = x
    return left + 1  # first one that is not left value
