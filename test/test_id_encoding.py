from unittest import TestCase

import sys
import id_encoding

class TestEncode(TestCase):

    def test_max_int(self):
        self.assertEquals('F=_g', id_encoding.encode(id_encoding.MAX_ID))

    def test_reject_negative_id(self):
        self.assertRaises(ValueError, id_encoding.encode, -1)

    def test_encode_zero(self):
        self.assertEquals(id_encoding.encode(0), '0')

    def test_encode_max_numeral(self):
        s = id_encoding.encode(id_encoding.NUMERAL_RADIX - 1)
        self.assertEquals(s, id_encoding.NUMERAL[-1])

class TestValidate(TestCase):

    def test_accept_zero(self):
        self.assertEquals(id_encoding.decode(id_encoding.encode(0)), 0)

    def test_accept_max_int(self):
        self.assertEquals(id_encoding.decode(id_encoding.encode(id_encoding.MAX_ID)), id_encoding.MAX_ID)

    def test_reject_non_numeral(self):
        for n in xrange(0, 128):
            c = chr(n)
            if c not in id_encoding.NUMERAL:
                if c == id_encoding.REPEAT_ESCAPE:
                    self.assertEquals(id_encoding.decode(str(c)), id_encoding.DECODE_INCOMPLETE_REPEAT)
                else:
                    self.assertEquals(id_encoding.decode(str(c)), id_encoding.DECODE_INVALID_NUMERAL)

    def test_reject_number_too_long(self):
        x = id_encoding.encode(id_encoding.MAX_ID) + '0'
        self.assertEquals(id_encoding.decode(x), id_encoding.DECODE_OVERFLOW)

    def test_reject_number_too_large(self):

        # generate the encoding for id_encoding.MAX_ID
        # then find the numeral which follows the numeral assigned to the most significant digit
        # replace the old numeral
        # then expect error upon validation

        x = id_encoding.encode(id_encoding.MAX_ID)
        index = id_encoding.NUMERAL.index(x[0])
        if index < id_encoding.NUMERAL_RADIX - 1:
            # construct a number with the same number of digits as an encoded max id
            # that will not fail which processing a repeat
            #
            # I'm not sure if this formula will be valid for all values of MAX_ID.
            # It should work for all powers of 2 ** n -1 except where
            # the ms digit of encoded MAX_ID is greatest numeral ('_')
            y = id_encoding.NUMERAL[index + 1] + x[1:-1] + chr(ord(x[-1])-1) + '0'
            self.assertEquals(id_encoding.decode(y), id_encoding.DECODE_OVERFLOW)

class TestDecode(TestCase):

    def test_decode_zero(self):
        x = id_encoding.decode(id_encoding.encode(0))
        self.assertEquals(0, x)
        self.assertEqual(int, x.__class__)

    def test_decode_max_int(self):
        x = id_encoding.decode(id_encoding.encode(id_encoding.MAX_ID))
        self.assertEquals(id_encoding.MAX_ID, x)
        self.assertEqual(id_encoding.MAX_ID.__class__, x.__class__)
