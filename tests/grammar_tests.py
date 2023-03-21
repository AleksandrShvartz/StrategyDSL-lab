import unittest

from dsl.parser import Grammar


class TestGrammar(unittest.TestCase):

    def test_simple(self):
        gr = Grammar()
        code = gr.parse()
        self.assertEqual(code, 'return 0')

    def test_nums_simple(self):
        gr = Grammar()
        gr._set_debug()
        res = gr.arith_exp.parse_string('0')
        self.assertEqual(res.asList()[0], '0')

if __name__ == '__main__':
    unittest.main()
