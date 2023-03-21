import time

import pyparsing as pp


class Grammar(object):
    def __init__(self):
        self.py_code = ''
        self.cur_indent = ''
        self.cur_prefix = ''
        self.colon = pp.Literal(':')
        self.lbrace = pp.Suppress('{')
        self.rbrace = pp.Suppress('}')
        self.lbrack = pp.Literal('[')
        self.rbrack = pp.Literal(']')
        self.lparen = pp.Literal('(')
        self.rparen = pp.Literal(')')
        self.equals = pp.Literal('=')
        self.equals_star = pp.Literal('*=')
        self.equals_slash = pp.Literal('\\=')
        self.equals_minus = pp.Literal('-=')
        self.equals_plus = pp.Literal('+=')
        self.equals_and = pp.Literal('&=')
        self.equals_or = pp.Literal('|=')
        self.comma = pp.Literal(',')
        self.dot = pp.Literal('.')
        self.slash = pp.Literal('/')
        self.bslash = pp.Literal('\\')
        self.star = pp.Literal('*')
        self.comment = pp.Literal('#')
        self.minus = pp.Literal('-')
        self.plus = pp.Literal('+')
        self.mcomment = pp.Literal('@')
        self.name = pp.Word(pp.srange('[a-z]'), pp.srange('[a-zA-Z0-9_]'))
        self.key_if = pp.Keyword('IF')
        self.key_else = pp.Keyword('ELSE')
        self.key_true = pp.Keyword('T')
        self.key_false = pp.Keyword('F')
        self.key_or = pp.Keyword('OR')
        self.key_and = pp.Keyword('AND')
        self.key_not = pp.Keyword('NOT')
        self.key_eq = pp.Literal('==')
        self.key_less = pp.Literal('<')
        self.key_more = pp.Literal('>')
        self.key_leq = pp.Literal('<=')
        self.key_meq = pp.Literal('>=')
        self.key_neq = pp.Literal('!=')
        self.pow = pp.Keyword('POW')
        self.mod = pp.Keyword('MOD')
        self.div = pp.Keyword('DIV')
        # change pdf
        self.empty_set = pp.Keyword('EMPTY')
        # self.set_append = pp.Keyword('APPEND')
        # self.set_remove = pp.Keyword('REMOVE')
        # self.set_alter = self.name + self.dot + (self.set_append | self.set_remove)
        self.number = pp.Combine(pp.Opt('-') + pp.Opt(pp.Word(pp.nums) + '.') + pp.Word(pp.nums))
        self.number.set_name('number')

        self.operand = self.plus | self.minus | self.star | self.slash | self.mod | self.div | self.pow
        self.operator = pp.Forward()
        self.bool_exp = pp.Forward()
        self.arith_exp = pp.Forward()
        self.set_exp = pp.Forward()
        self.comp_op = self.key_eq | self.key_less | self.key_more | self.key_meq | self.key_leq | self.key_neq
        self.logic_op = self.key_or | self.key_and
        self.set_op = self.plus | self.minus
        self.bool_exp <<= (self.lparen + self.bool_exp + self.rparen) | \
                          (self.key_true ^ self.key_false ^ (self.key_not + self.bool_exp) |
                           (self.bool_exp + self.logic_op + self.bool_exp) |
                           (self.arith_exp + self.comp_op + self.arith_exp) | self.name)

        self.arith_exp <<= self.name ^ self.number
        #pp.Opt(self.plus | self.minus) + ((self.lparen + self.arith_exp + self.rparen) |
        #                  (self.arith_exp + self.operand + self.arith_exp) |
        self.arith_exp.set_name('num exp')
        self.arith_exp.set_parse_action(self._arith_exp_action)
        # change pdf
        self.set_exp <<= (self.lparen + self.set_exp + self.rparen) | \
                         self.empty_set ^ self.name ^ (self.set_exp + self.set_op + self.set_exp) ^ \
                         self.set_exp
        self.block = self.lbrace + pp.ZeroOrMore(self.operator) + self.rbrace
        self.block.set_name('block')
        self.block.set_parse_action(self._return_action)
        self.if_op = self.key_if + self.bool_exp + self.operator + pp.Opt(self.key_else + self.operator)
        self.if_op.set_name('if')
        self.key_import = pp.Keyword('IMPORT')
        self.imp_op = self.key_import + self.name
        self.imp_op.set_name('import')
        self.num = pp.Keyword('NUM')
        self.set = pp.Keyword('SET')
        self.bool = pp.Keyword('BOOL')
        self.type = self.num | self.bool | self.set
        self.decl = self.type + self.name
        self.decl.set_name('declaration')
        self.take_el = pp.Forward()
        self.set_ch = (self.take_el | self.name) + (self.equals | self.equals_plus | self.equals_minus) + self.set_exp
        self.bool_ch = (self.take_el | self.name) + (self.equals | self.equals_and | self.equals_or) + self.bool_exp
        self.num_ch = (self.take_el | self.name) + (self.equals | self.equals_plus | self.equals_minus |
                                                    self.equals_slash | self.equals_star) + self.arith_exp
        self.change = self.set_ch | self.bool_ch | self.num_ch
        self.change.set_name('change value')
        self.key_foreach = pp.Keyword('FOREACH')
        self.key_in = pp.Keyword('IN')
        self.key_range = pp.Keyword('RANGE')
        # change pdf
        self.iter_obj = self.name | (
                self.name + self.lbrack + pp.nums + pp.ZeroOrMore(self.comma + pp.nums) + self.rbrack) | \
                        (self.key_range + self.lparen + self.arith_exp + self.colon + self.arith_exp + self.rparen)
        self.foreach = self.key_foreach + self.name + self.key_in + self.iter_obj + self.operator
        self.foreach.set_name('loop')
        self.take_el <<= self.name + self.lbrack + self.iter_obj + self.rbrack
        self.key_return = pp.Keyword('RETURN')
        self.answer = self.key_return + self.arith_exp
        self.answer.set_name('answer')
        self.answer.set_parse_action(self._return_action)
        # not sure if it works ok
        self.operator <<= self.answer
        # | self.block | self.if_op | self.foreach | self.imp_op | self.decl | self.change

    def _set_debug(self):
        self.block.set_debug()
        self.operator.set_debug()
        self.answer.set_debug()
        self.arith_exp.set_debug()
        self.arith_exp.add_parse_action(self._debug_print)
        self.foreach.set_debug()
        self.if_op.set_debug()
        self.imp_op.set_debug()
        self.number.set_debug()


    def _return_action(self, toks):
        self.py_code += 'return '

    def _block_action(self, toks):
        self.cur_indent += '    '
        print(toks)

    def _arith_exp_action(self, s: str, loc: int, tokens):
        print(s, loc, tokens)
        self.py_code += tokens[1]

    def _debug_print(self, s: str, loc: int, tokens):
        print(s, loc, tokens)

    def parse(self, code='RETURN 0'):
        code = '{\n' + code + '}\n'
        self._set_debug()
        res = self.block.parse_string(code)
        return self.py_code

    def create_diagram(self):
        pp.autoname_elements()
        self.operator.setName('ALL')
        # print(pp.__version__)
        # street_address = pp.Word(pp.nums).set_name("house_number") + pp.Word(pp.alphas)[1, ...].set_name("street_name")
        # street_address.set_name("street_address")
        # street_address.create_diagram("street_address_diagram.html")
        self.operator.create_diagram('out.html')

class Kalah(Grammar):
    def __init__(self):
        super().__init__()
        self.key_get = pp.Keyword('GET')
        self.get = self.key_get + self.lparen + (pp.nums | self.iter_obj) + self.rparen
        self.operator <<= self.if_op ^ self.foreach ^ self.imp_op ^ self.decl ^ self.change ^ self.answer ^ self.get


