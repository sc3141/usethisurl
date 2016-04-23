"""
This module implements a mechanism by which Google datastore keys ids can be represented in string form
suitable for inclusion in a URL.
"""

import itertools
import array
import re
from collections import namedtuple

from google.appengine.ext.ndb.key import _MAX_LONG as DATASTORE_MAX_LONG

from model_error import DecodeError

# magnitude part of integer
MAX_ID_BITS = DATASTORE_MAX_LONG.bit_length()

NUMERAL = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
NUMERAL_RADIX = len(NUMERAL)
NUMERAL_PAT = r'[0-9A-z_-]'
REPEAT_ESCAPE = '='
BITS_PER_NUMERAL = 6

NOT_A_NUMERAL = 256
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

    m = array.array('i', itertools.repeat(NOT_A_NUMERAL, 256))
    for n, c in enumerate(counting):
        m[ord(c)] = n

    return m

NUMERAL_VALUE = _initialize_numeral_map(NUMERAL)
"""array: a value map of numerals"""


def encode(kid):
    """
    Produces a base-64 representation of an integer.  Note that resulting representation is *not*
    the same as that produced by the Standard Library module, :module base64:, as that module pertains to
    encoding/decoding of arbitrary binary strings.  This function represents

    Args:
        kid (int): the id of a google datastore key, hence (k)ey(id)

    Returns:
        str: a string representation of the id in base64 using the numerals identified by

    Note:
        There may be an efficient way to compress repetitive numerals. The motivation would be
        to further shorten encoded ids.  There is a cost associated with increased encoding, however
        this cost may be slightly offset by a decrease in the cost of decoding.
        Profiling experiments recommended.
    """
    if kid < 0:
        raise ValueError("Attempt to encode id using negative number (%d)" % kid)
    elif kid > DATASTORE_MAX_LONG:
        raise ValueError("Attempt to encode id greater than negative number (%d)" % kid)

    if kid < NUMERAL_RADIX:
        return str(NUMERAL[kid])

    digits = kid.bit_length() / BITS_PER_NUMERAL
    slack = (kid.bit_length() != digits * BITS_PER_NUMERAL)
    digits += slack
    encoded = bytearray(digits)
    position = digits - 1

    while kid > 0:
        d = kid & 0x3F
        kid >>= BITS_PER_NUMERAL
        encoded[position] = NUMERAL[d]
        position -= 1

    return _compress_repeats(str(encoded))

REPEAT_PAT = r'((.)\2{3,63})'
"""
regex pattern for detection of repeated characters in uncompressed encoded id.
replacement of repetition isn't worthwhile until a numeral is repeated 3 times,
because the compression requires 3 digits (=nc, n=numeral, c=count).
the maximum repetition which can be replaced is 63, because that is the value
of the highest numeral.
"""
REPEAT_RE = re.compile(REPEAT_PAT)

Repeat = namedtuple('Repeat', ['start', 'end', 'numeral'])


def _compress_repeats(s):
    repeats = [Repeat(m.start(1), m.end(1), m.group(2)) for m in REPEAT_RE.finditer(s)]
    if repeats:
        as_list = list(s)
        for r in reversed(repeats):
            as_list[r.start:r.end] = (REPEAT_ESCAPE, r.numeral, NUMERAL[r.end - r.start])

        return ''.join(as_list)

    return s


def decode(s):
    """
    Produces the corresponding integer id from an encoded string.  .

    Args:
        s (str): a string which represents a base-64 value according the set of numerals defined
        at the top of this module.

    Returns:
        int: if the corresponding id does not exceed the size of an int
        long: if the corresponding id exceeds the size of an int

    Raises:
        model_error.DecodeError:
    """
    bit_count = 0
    kid = 0

    it = iter(s)
    for c in it:
        if c == REPEAT_ESCAPE:
            try:
                repeated = it.next()
                count_numeral = it.next()
            except StopIteration:
                raise DecodeError(DecodeError.INCOMPLETE_REPEAT, s)

            val = NUMERAL_VALUE[ord(repeated)]
            if val == NOT_A_NUMERAL:
                raise DecodeError(DecodeError.INVALID_REPEATED_NUMERAL, s)

            count = NUMERAL_VALUE[ord(count_numeral)]
            if count == NOT_A_NUMERAL:
                raise DecodeError(DecodeError.INVALID_REPEAT_COUNT_NUMERAL, s)

            bit_count += (count * BITS_PER_NUMERAL)
            if bit_count > MAX_ID_BITS:
                raise DecodeError(DecodeError.REPEAT_OVERFLOWS, s)

            # countdown is not very pythonic ... but for _ in xrange(count):  ????
            while count:
                kid <<= BITS_PER_NUMERAL
                kid = kid | val
                count -= 1
        else:
            val = NUMERAL_VALUE[ord(c)]
            if val == NOT_A_NUMERAL:
                raise DecodeError(DecodeError.INVALID_NUMERAL, s)

            bit_count += (BITS_PER_NUMERAL if bit_count else val.bit_length())
            if bit_count > MAX_ID_BITS:
                raise DecodeError(DecodeError.OVERFLOW, " max %d: %s" % (MAX_ID_BITS, s))

            kid <<= BITS_PER_NUMERAL
            kid = kid | val

    if bit_count == MAX_ID_BITS and kid > DATASTORE_MAX_LONG:
        raise DecodeError(DecodeError.OVERFLOW, s)

    return kid

