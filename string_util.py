

def truncate(s, limit):
    """
    Truncates a s if it is not short enough
    Args:
        shortid (string): the short id to potentially truncate
        num_extras (int): the amount of excess characters to preserve in the truncation

    Returns:
        string: the truncated short id plus a trailing ellipsis

    """
    if len(s) > limit:
        return s[:limit] + '...'
    else:
        return s


