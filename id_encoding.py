"""
This module implements a mechanism by which Google datastore keys ids can be represented in string form
suitable for inclusion in a URL.
"""

import itertools
import array
import sys

import string_util

NUMERAL = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
NUMERAL_RADIX = len(NUMERAL)

INVALID_NUMERAL = 256
"""int: magic value which indicates a character in the character set which does not correspond to a numeral"""

def _initialize_numeral_map(counting):
    """
    Creates a mapping of numeral to value per the provided counting of numerals.

    Args:
        counting (str): sequence of characters which enumerate all possible values which can be
            represented by a digit

    Returns:
        array: a mapping of the ordinal value of the character to the value which it represents
            in the numbering scheme.
    """

    m = array.array('i', itertools.repeat(INVALID_NUMERAL, 256))
    for n, c in enumerate(counting):
        m[ord(c)] = n

    return m

NUMERAL_VALUE = _initialize_numeral_map(NUMERAL)
"""array: a value map of numerals"""

def encode(id):
    """
    Produces a base-64 representation of an integer.  Note that resulting representation is *not*
    the same as that produced by the Standard Library module, :module base64:, as that module pertains to
    encoding/decoding of arbitrary binary strings.  This function represents

    Args:
        id (int): the id of a google datastore key

    Returns:
        str: a string representation of the id in base64 using the numerals identified by

    """
    if id < 0:
        raise ValueError("Attempt to encode id using negative number (%d)" % id)

    if id < NUMERAL_RADIX:
        return str(NUMERAL[id])

    position = id.bit_length() / 6
    encoded = bytearray(position + 1)

    while id > 0:
        d = id & 0x3F
        id = id >> 6
        encoded[position] = NUMERAL[d]
        position -= 1

    return str(encoded)


ENCODED_MAX_INT = encode(sys.maxint)
"""str: string representation of the maximum integer value"""

LEN_ENCODED_MAX_INT = len(ENCODED_MAX_INT)
"""int: length of said max int encoding"""

MOST_SIGNIFICANT_ENCODED_DIGIT = ENCODED_MAX_INT[0]
"""chr: numeral of the most significant digit of the max int"""

MAX_VALUE_MS_NUMERAL = NUMERAL_VALUE[ord(MOST_SIGNIFICANT_ENCODED_DIGIT)]
"""int: the value of the most significant numeral of the max int"""

def check_encoding(s):
    """
    Indicates by raise of exception that a string is not a valid encoding of an id (integer).
    Errors of excessive length require iteration over only the first LEN_ENCODED_MAX_INT + 1
    characters.

    Args:
        s (str): potential encoded id

    Returns:
        None: if s represents a valid encoding
        ValueError: if s does not represent a valid encoding

    Raises:
        ValueError: if character which is not a numeral is present or if the resulting value
            would exceed the value of the maximum integer
    """

    slen = 0
    for c in s:
        if NUMERAL_VALUE[ord(c)] == INVALID_NUMERAL:
            return ValueError(
                "unexpected character '%s' in encoded id '%s'" % \
                (s[slen:slen+1].encode('utf-8').encode('string_escape'), s.encode('utf-8').encode('string_escape')))

        slen += 1
        if slen > LEN_ENCODED_MAX_INT:
            return ValueError("encoded value exceeds length of maximum (%d)" % LEN_ENCODED_MAX_INT)
        elif slen == LEN_ENCODED_MAX_INT and \
            NUMERAL_VALUE[ord(s[0])] > MAX_VALUE_MS_NUMERAL:
            return ValueError("encoded value (%s) exceeds maximum" % s)


def decode(s):
    """
    Produces the corresponding integer id from an encoded string. This function does not validate
    the provided string.  To validate the input, pass the string to the method, validate_encoding.
    Note that validly encoded ids which correspond  to ids > sys.maxint are properly converted, but
    speed _may_ markedly degrade.

    Args:
        s (str): a string which represents a base-64 value according the set of numerals defined
        at the top of this module.

    Returns:
        int: if the corresponding id does not exceed sys.maxint
        long: if the corresponding id exceeds sys.maxint

    """
    id = 0
    for c in s:
        val = NUMERAL_VALUE[ord(c)]
        id = id << 6
        id = id | val

    return id

def create_short_id_map(*args):
    """
    Produces a dictionary of shortids which are keyed by id

    Args:
        *args: an iterable sequence of valid short ids

    Returns:
        dict: a dictionary of ids each mapped to the corresponding short-id

    """
    m = dict()

    for v in args:
        error = check_encoding(v)
        if isinstance(error, ValueError):
            raise error

        k = decode(v)
        m[k] = v

    return m

def truncate_short_id(shortid, num_extras=10):
    """
    Truncates a shortid if it is not short enough :) to be valid
    Args:
        shortid (string): the short id to potentially truncate
        num_extras (int): the amount of excess characters to preserve in the truncation

    Returns:
        string: the truncated short id plus a trailing ellipsis

    """
    return string_util.truncate(shortid, LEN_ENCODED_MAX_INT + num_extras)


