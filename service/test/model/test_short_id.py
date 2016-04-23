from unittest import TestCase

from google.appengine.ext.ndb.key import _MAX_LONG

import service.model.short_id as short_id
from service.model.model_error import DecodeError


class TestEncode(TestCase):

    def test_max_int(self):
        encoded = short_id.encode(_MAX_LONG)
        self.assertEquals(short_id.MAX_ID_BITS, 63)
        self.assertEquals(encoded, '7=_A')

    def test_reject_negative_id(self):
        self.assertRaises(ValueError, short_id.encode, -1)

    def test_encode_zero(self):
        self.assertEquals(short_id.encode(0), '0')

    def test_encode_max_numeral(self):
        s = short_id.encode(short_id.NUMERAL_RADIX - 1)
        self.assertEquals(s, short_id.NUMERAL[-1])


class TestDecode(TestCase):

    def test__zero(self):
        x = short_id.decode(short_id.encode(0))
        self.assertEquals(0, x)
        self.assertEqual(int, x.__class__)

    def test_decode_max_int(self):
        x = short_id.decode(short_id.encode(_MAX_LONG))
        self.assertEquals(_MAX_LONG, x)

    def test_reject_non_numeral(self):
        for n in xrange(0, 128):
            c = chr(n)
            if c not in short_id.NUMERAL:
                with self.assertRaises(DecodeError) as cm:
                    short_id.decode(str(c))
                e = cm.exception
                if c == short_id.REPEAT_ESCAPE:
                    self.assertEquals(e.code, DecodeError.INCOMPLETE_REPEAT)
                else:
                    self.assertEquals(e.code, DecodeError.INVALID_NUMERAL)

    def test_reject_number_too_long(self):
        x = short_id.encode(_MAX_LONG) + '0'
        with self.assertRaises(DecodeError) as cm:
            short_id.decode(x)
        e = cm.exception
        self.assertEqual(e.code, DecodeError.OVERFLOW)

    def test_reject_number_too_large(self):

        # generate the encoding for short_id.MAX_ID
        # then find the numeral which follows the numeral assigned to the most significant digit
        # replace the old numeral
        # then expect error upon validation
        if short_id.MAX_ID_BITS == 128:
            encoded = 'F________________________________________'
        elif short_id.MAX_ID_BITS == 64:
            encoded = '7___________'
        else:
            self.fail("number of bits in a datastore id is not an expected value (64 or 128")

        index = short_id.NUMERAL.index(encoded[0])
        if index < short_id.NUMERAL_RADIX - 1:
            # construct a number with the same number of digits as an encoded max id
            # that will not fail which processing a repeat
            #
            # I'm not sure if this formula will be valid for all values of MAX_ID.
            # It should work for all powers of 2 ** n -1 except where
            # the ms digit of encoded MAX_ID is greatest numeral ('_')
            replaced_numeral = short_id.NUMERAL[short_id.NUMERAL_VALUE[ord(encoded[-1])]]
            y = short_id.NUMERAL[index + 1] + encoded[1:-1] + replaced_numeral + '0'
            with self.assertRaises(DecodeError) as cm:
                short_id.decode(y)
            e = cm.exception
            self.assertEqual(e.code, DecodeError.OVERFLOW)

