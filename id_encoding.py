"""
This module implements a mechanism by which Google datastore keys ids can be represented in string form
suitable for inclusion in a URL.
"""

import itertools
import array
import re
from collections import namedtuple

import string_util

NUMERAL = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_-"
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

    Note:
        There may be an efficient way to compress repetitive numerals. The motivation would be
        to further shorten encoded ids.  There is a cost associated with increased encoding, however
        this cost may be sl;ightly offset by a decrease in the cost of decoding.
        Profiling experiments recommended.
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

    return _compress_repeats(str(encoded))

REPEAT_PAT = r'((.)\2{3,63})'
"""
regex pattern for detection of repeated characters in uncompressed encoded id.
replacement of repetition isn't worthwhile until a numeral is repeated 3 times,
because the compression requires 3 digits (=nc, n=numeral, c=count).
the maximium repettition which can be replaced is 63, because that is the value
of the highest numeral.
"""
REPEAT_RE = re.compile(REPEAT_PAT)

Repeat = namedtuple('Repeat', [ 'start', 'end', 'numeral' ])

def _compress_repeats(s):
    repeats = [ Repeat(m.start(1), m.end(1), m.group(2)) for m in REPEAT_RE.finditer(s)]
    if repeats:
        as_list = list(s)
        for r in reversed(repeats):
            as_list[r.start:r.end] = ('=', r.numeral, NUMERAL[r.end - r.start])

        return ''.join(as_list)

    return s


COMPRESSED_REPEAT_PAT = ''.join(( r'(=([', NUMERAL, r'])([', NUMERAL, ']))'))
COMPRESSED_REPEAT_RE = re.compile(COMPRESSED_REPEAT_PAT)

CompressedRepeat = namedtuple('CompressedRepeat', [ 'start', 'numeral', 'count' ])

def _expand_repeats(s):
    repeats = [ CompressedRepeat(m.start(1), m.group(2), m.group(3)) for m in COMPRESSED_REPEAT_RE.finditer(s)]
    if repeats:
        as_list = list(s)
        for r in reversed(repeats):
            count = NUMERAL_VALUE[ord(r.count)]
            as_list[r.start:r.start+3] = itertools.repeat(r.numeral, NUMERAL_VALUE[ord(r.count)])

        return as_list

    return s



MAX_ID = 2 ** 256 - 1
ENCODED_MAX_ID = encode(MAX_ID)
"""str: string representation of the maximum integer value"""

LEN_ENCODED_MAX_ID = len(ENCODED_MAX_ID)
"""int: length of said max int encoding"""

LEN_UNCOMPRESSED_MAX_ID = len(_expand_repeats(ENCODED_MAX_ID))
"""int: length of encoded numbers does not monotonically increase with value. Thus to compare
magnitudes, lengths of uncompressed ids must be compared."""

MOST_SIGNIFICANT_ENCODED_DIGIT = ENCODED_MAX_ID[0]
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
    for c in _expand_repeats(s):
        if NUMERAL_VALUE[ord(c)] == INVALID_NUMERAL:
            return ValueError(
                "unexpected character '%s' in encoded id '%s'" % \
                (s[slen:slen+1].encode('utf-8').encode('string_escape'), s.encode('utf-8').encode('string_escape')))

        slen += 1
        if slen > LEN_UNCOMPRESSED_MAX_ID:
            return ValueError("encoded value exceeds length of maximum (%d)" % LEN_ENCODED_MAX_ID)
        elif slen == LEN_UNCOMPRESSED_MAX_ID and \
            NUMERAL_VALUE[ord(s[0])] > MAX_VALUE_MS_NUMERAL:
            return ValueError("encoded value (%s) exceeds maximum (%d)" % (s, MAX_ID))


def decode(s):
    """
    Produces the corresponding integer id from an encoded string. This function does not validate
    the provided string.  To validate the input, pass the string to the method, validate_encoding.
    Note that validly encoded ids which correspond  to ids > MAX_ID are properly converted, but
    speed _may_ markedly degrade.

    Args:
        s (str): a string which represents a base-64 value according the set of numerals defined
        at the top of this module.

    Returns:
        int: if the corresponding id does not exceed MAX_ID
        long: if the corresponding id exceeds MAX_ID

    """
    id = 0
    for c in _expand_repeats(s):
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
    return string_util.truncate(shortid, LEN_ENCODED_MAX_ID + num_extras)

