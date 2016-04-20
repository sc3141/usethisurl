

def ellipsicate(s, limit):
    """
    Truncates a s if it is not short enough
    Args:
        s (string): s to potentially truncate
        limit (int): the amount of characters to preserve in the truncation

    Returns:
        string: if string exceeds limit, truncated string plus a trailing ellipsis

    """
    if len(s) > limit:
        return s[:limit] + '...'
    else:
        return s


