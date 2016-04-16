"""
This module implements a mechanism by which Google datastore keys ids can be represented in string form
suitable for inclusion in a URL.
"""

import itertools
import array
import re
from collections import namedtuple

NUMERAL = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
NUMERAL_RADIX = len(NUMERAL)
NUMERAL_PAT = r'[0-9A-z_-]'
REPEAT_ESCAPE = ('=')
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
    elif id > MAX_ID:
        raise ValueError("Attempt to encode id greater than negative number (%d)" % id)

    if id < NUMERAL_RADIX:
        return str(NUMERAL[id])

    digits = id.bit_length() / BITS_PER_NUMERAL
    slack = (id.bit_length() != digits * BITS_PER_NUMERAL)
    digits += slack
    encoded = bytearray(digits)
    position = digits - 1

    while id > 0:
        d = id & 0x3F
        id = id >> BITS_PER_NUMERAL
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
            as_list[r.start:r.end] = (REPEAT_ESCAPE, r.numeral, NUMERAL[r.end - r.start])

        return ''.join(as_list)

    return s


MAX_ID_BITS = 256
MAX_ID = 2 ** MAX_ID_BITS - 1

DECODE_INVALID_NUMERAL = -1
DECODE_INCOMPLETE_REPEAT = -2
DECODE_INVALID_REPEATED_NUMERAL = -3
DECODE_INVALID_REPEAT_COUNT_NUMERAL = -4
DECODE_REPEAT_OVERFLOWS = -5
DECODE_OVERFLOW = -6

DECODE_ERROR_REASONS = {
    DECODE_INVALID_NUMERAL: 'a character which is not a numeral was present in the string',
    DECODE_INCOMPLETE_REPEAT: 'end of string encountered in repeat sequence (=<val><count>)',
    DECODE_INVALID_REPEATED_NUMERAL: 'the digit specified to be repeated is not a numeral',
    DECODE_INVALID_REPEAT_COUNT_NUMERAL: 'the repeat count is not a numeral',
    DECODE_REPEAT_OVERFLOWS: 'repeat sequence would result in number greater than MAX_ID',
    DECODE_OVERFLOW: 'decoded id is greater than MAX_ID (too many bits or value)'
}

def decode_error_description(code):
    """
    Args:
        code (int): an error code returned from method, decode

    Returns:
        str: a description of the error

    """
    return DECODE_ERROR_REASONS.get(code, 'unspecified decode error')

class DecodeError(StopIteration):
    """
    This class provides for a more organized cessation of decoding upon error: the implementation
    of method, decode, is cleaner
    """
    def __init__(self, code):
        """
        Args:
            code (int): code which descrbes the error

        Returns:

        """
        super(DecodeError, self).__init__()
        self.code = code


def decode(s):
    """
    Produces the corresponding integer id from an encoded string.  .

    Args:
        s (str): a string which represents a base-64 value according the set of numerals defined
        at the top of this module.

    Returns:
        int: if the corresponding id does not exceed the size of an int
        long: if the corresponding id exceeds the size of an int

    """

    bit_count = 0
    id = 0

    try:
        it = iter(s)
        for c in it:
            if c == REPEAT_ESCAPE:
                try:
                    repeated = it.next()
                    count_numeral = it.next()
                except StopIteration:
                    raise DecodeError(DECODE_INCOMPLETE_REPEAT)

                val = NUMERAL_VALUE[ord(repeated)]
                count = NUMERAL_VALUE[ord(count_numeral)]
                bit_count += (count * BITS_PER_NUMERAL)

                if val == NOT_A_NUMERAL:
                    raise DecodeError(DECODE_INVALID_REPEATED_NUMERAL)
                elif count == NOT_A_NUMERAL:
                    raise DecodeError(DECODE_INVALID_REPEAT_COUNT_NUMERAL)
                elif bit_count > MAX_ID_BITS:
                    raise DecodeError(DECODE_REPEAT_OVERFLOWS)

                # countdown is not very pythonic ... but for _ in xrange(count):  ????
                while count:
                    d = id & 0x3F
                    id = id << BITS_PER_NUMERAL
                    id = id | val
                    count -= 1
            else:
                val = NUMERAL_VALUE[ord(c)]
                bit_count += BITS_PER_NUMERAL if bit_count else val.bit_length()

                if val == NOT_A_NUMERAL:
                    raise DecodeError(DECODE_INVALID_NUMERAL)
                elif bit_count > MAX_ID_BITS:
                    raise DecodeError(DECODE_OVERFLOW)

                d = id & 0x3F
                id = id << BITS_PER_NUMERAL
                id = id | val

        if bit_count == MAX_ID_BITS and id > MAX_ID:
            raise DecodeError(DECODE_OVERFLOW)

    except DecodeError as e:
        id = e.code

    return id

