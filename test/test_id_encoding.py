from unittest import TestCase

import sys
import id_encoding

class TestEncode(TestCase):

    def test_max_int(self):
        self.assertEquals('7__________', id_encoding.encode(sys.maxint))

    def test_reject_negative_id(self):
        self.assertRaises(ValueError, id_encoding.encode, -1)

    def test_encode_zero(self):
        self.assertEquals(id_encoding.encode(0), '0')

    def test_encode_max_numeral(self):
        s = id_encoding.encode(id_encoding.NUMERAL_RADIX - 1)
        self.assertEquals(s, id_encoding.NUMERAL[-1])

class TestValidate(TestCase):

    def test_accept_zero(self):
        id_encoding.check_encoding(id_encoding.encode(0))

    def test_accept_max_int(self):
        x = id_encoding.check_encoding(id_encoding.encode(sys.maxint))

    def test_reject_non_numeral(self):
        for n in xrange(0, 256):
            c = chr(n)
            if c not in id_encoding.NUMERAL:
                self.assertIsInstance(id_encoding.check_encoding(str(c)), ValueError)

    def test_reject_number_too_long(self):
        x = id_encoding.encode(sys.maxint) + '0'
        self.assertIsInstance(id_encoding.check_encoding(x), ValueError)

    def test_reject_excessive_most_significant_digit(self):

        # generate the encoding for maxint
        # then find the numeral which follows the numeral assigned to the most significant digit
        # replace the old numeral
        # then expect error upon validation

        x = id_encoding.encode(sys.maxint)
        index = id_encoding.NUMERAL.index(x[0])
        if index < id_encoding.NUMERAL_RADIX - 1:
            y = id_encoding.NUMERAL[index + 1] + x[1:]
            self.assertIsInstance(id_encoding.check_encoding(y), ValueError)


class TestDecode(TestCase):

    def test_decode_zero(self):
        x = id_encoding.decode(id_encoding.encode(0))
        self.assertEquals(0, x)
        self.assertEqual(int, x.__class__)

    def test_decode_max_int(self):
        x = id_encoding.decode(id_encoding.encode(sys.maxint))
        self.assertEquals(sys.maxint, x)
        self.assertEqual(int, x.__class__)

class TestCreateShortIdMap(TestCase):

    def test_accept_all_valid(self):
        m = id_encoding.create_short_id_map('shorten', 'submit', 'wakawaka')
        self.assertEqual(3, len(m))