from unittest import TestCase

import service.model.short_id as short_id

class TestEncode(TestCase):

    def test_max_int(self):
        self.assertEquals('F=_g', short_id.encode(short_id.MAX_ID))

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
        x = short_id.decode(short_id.encode(short_id.MAX_ID))
        self.assertEquals(short_id.MAX_ID, x)
        self.assertEqual(short_id.MAX_ID.__class__, x.__class__)

    def test_reject_non_numeral(self):
        for n in xrange(0, 128):
            c = chr(n)
            if c not in short_id.NUMERAL:
                if c == short_id.REPEAT_ESCAPE:
                    self.assertEquals(short_id.decode(str(c)), short_id.DECODE_INCOMPLETE_REPEAT)
                else:
                    self.assertEquals(short_id.decode(str(c)), short_id.DECODE_INVALID_NUMERAL)

    def test_reject_number_too_long(self):
        x = short_id.encode(short_id.MAX_ID) + '0'
        self.assertEquals(short_id.decode(x), short_id.DECODE_OVERFLOW)

    def test_reject_number_too_large(self):

        # generate the encoding for short_id.MAX_ID
        # then find the numeral which follows the numeral assigned to the most significant digit
        # replace the old numeral
        # then expect error upon validation

        x = short_id.encode(short_id.MAX_ID)
        index = short_id.NUMERAL.index(x[0])
        if index < short_id.NUMERAL_RADIX - 1:
            # construct a number with the same number of digits as an encoded max id
            # that will not fail which processing a repeat
            #
            # I'm not sure if this formula will be valid for all values of MAX_ID.
            # It should work for all powers of 2 ** n -1 except where
            # the ms digit of encoded MAX_ID is greatest numeral ('_')
            y = short_id.NUMERAL[index + 1] + x[1:-1] + chr(ord(x[-1]) - 1) + '0'
            self.assertEquals(short_id.decode(y), short_id.DECODE_OVERFLOW)

