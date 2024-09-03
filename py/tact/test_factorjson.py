"""Unit tests for factorjson.

"""
import unittest
import os.path
import inspect
import logging
# own imports
import act.factorjson
import act.mergejson
import act.sub
import tact.sub4t

_LOG_LEVEL = logging.CRITICAL

_J45_DE_CN_COMMON = """
{"J45":{"ACCTASSCAT":"","GL_GR_IR_NUM":"0021120000","GL_GR_IR_TXT":"GR/IR",
"GL_INV_T_GOODS_NUM":"0013600000","GL_INV_T_GOODS_TXT":"Inventory TradingGd",
"GL_PAYBLS_DOM_NUM":"0021100000","GL_PAYBLS_DOM_TXT":"Paybls Domestic",
"IR_AMT_C":"-1.0","IR_REF_TEXT":"123456789A123456","IR_TAX_AMT":"0.0",
"JE_KEY_C":"31","JE_KEY_D":"86","JOURNAL_ENTRY_NO":"2","MAT":"TG11",
"MAT_SHORT_TEXT":"Vanilla test J45","MOVE_TYPE":"101","MVT_IND":"B",
"POST_AMT":"1.0","PO_ITEM":"00010","PO_PRICE":"1","PRICE":"1.0",
"PRICE_UNIT":"1","QTY":"1.0","RLDNR_0":"0L","RLDNR_1":"2L","RLDNR_2":"3L",
"UNITS":"PC"}}
"""

_J45_DE_DELTA = """
{
    "J45": {
        "COMPANY_CODE": "1010",
        "COUNTRY": "DE",
        "CURRENCY": "EUR",
        "PLANT": "1010",
        "PURCH_ORG": "1010",
        "SUPPLIER": "0010300001",
        "SUPPLIER_NAME": "Inlandslieferant DE 1",
        "S_LOC": "101A",
        "TAX_CODE": "V0"
    }
}
"""

_ONE_LESS = '"JE_KEY_D":"86"'
_J45_DE_CN_COMMON_ONE_LESS = _J45_DE_CN_COMMON.replace(_ONE_LESS + ',', '')

# For complicated test with arrays
# --------------------------------
# JSON Fragments
_A_IN_F = '"AinF":"A in F",'
_A_IN_D = '"A":"A in D",'
# JSON value strings, each containing exactly one %-format.
# Primitives.
_A = '"string A%s"'
_B = '%d'
# Simple array & object.
_C = '[1,"two %s"]'
_D = '{' + _A_IN_D + '"B": %d}'
# Nested array & object.
_E = '[[11,22],[%d,33]]'
_F = '{' + _A_IN_F + '"BinF":[1,"two",{"A":42,"B":"string B","C":{"1":1,"2":"Two","three":[5,%d]}}]}'
# JSON attribute:value pairs, with attribute name An, Bn, ...
_AnV = f'"A%d":{_A}, "B%d":{_B}, "C%d":{_C}, "D%d":{_D}, "E%d":{_E}, "F%d":{_F}'
# Same attribute names with same values: all factored out.
_A0_V0 = _AnV % ((0, 0) * 6)
# Same attribute names with different values: two common attribute-value pairs
# factord out, _A_IN_F and _A_IN_D.
_A1_V1 = _AnV % ((1, 1) * 6)
_A1_V2 = _AnV % ((1, 2) * 6)
_A1_V3 = _AnV % ((1, 3) * 6)
_A1_V1_X = _A1_V1.replace(_A_IN_F, '').replace(_A_IN_D, '')
_A1_V2_X = _A1_V2.replace(_A_IN_F, '').replace(_A_IN_D, '')
_A1_V3_X = _A1_V3.replace(_A_IN_F, '').replace(_A_IN_D, '')
# pylint:disable-next=consider-using-f-string
_A0_V0_X = _A0_V0 + (',"D1":{%s},"F1": {%s}' % (_A_IN_D[:-1], _A_IN_F[:-1]))
# Different attribute names with same values: nothing factored out.
_A2_V9 = _AnV % ((2, 9) * 6)
_A3_V9 = _AnV % ((3, 9) * 6)
_A4_V9 = _AnV % ((4, 9) * 6)
# JSON File Contents
_F1 = f'''{{
{_A0_V0},
{_A1_V1},
{_A2_V9}
}}'''
_F2 = f'''{{
{_A1_V2},
{_A0_V0},
{_A3_V9}
}}'''
_F3 = f'''{{
{_A4_V9},
{_A1_V3},
{_A0_V0}
}}'''
_O1 = f'''{{
{_A1_V1_X},
{_A2_V9}
}}'''
_O2 = f'''{{
{_A1_V2_X},
{_A3_V9}
}}'''
_O3 = f'''{{
{_A4_V9},
{_A1_V3_X}
}}'''
_O4 = f'''{{
{_A0_V0_X}
}}'''

_FACTOR_JSON = {
    # Test name suffix
    # ================
    # a,b,c ... => file a,b,c number of items left after factoring out common
    # F 0,1,N => number of items to factor out
    # N 1,2,... => maximum object nesting depth
    # Keys
    # ====
    # n = path list of files.
    # i = json list, one string per file
    # O = expected json results, one per in file, same order as n, plus one
    #     for factored file.
    # OPTIONAL
    # d = list of directories to create for test
    # D = directory for top level input file
    # t = target directory
    'basic_a1_b1_F1_N1': {
        'n': ['a.json', 'b.json'],
        'i': ['{"x":1, "y":2}', '{"z":3, "y":2}'],
        'O': ['{"x":1}', '{"z":3}', '{"y":2}']
    },
    'j45_cn_de_a9_b9_F27_N2': {
        'n': ['j45de.json', 'j45cn.json'],
        'i': [tact.sub4t.J45_DE, tact.sub4t.J45_CN],
        'O': [_J45_DE_DELTA, tact.sub4t.J45_CN_DELTA, _J45_DE_CN_COMMON]
    },
    'nesting_a3_b3_F3_N3': {
        'n': ['a.json', 'b.json'],
        'i': [
            '{"x":1, "y":2, "D1":{ "x":1, "y":2, "D2":{"x":1, "y":2}}}',
            '{"z":1, "y":2, "D1":{ "z":1, "y":2, "D2":{"z":1, "y":2}}}'
        ],
        'O': [
            '{"x":1,        "D1":{ "x":1,        "D2":{"x":1        }}}',
            '{"z":1,        "D1":{ "z":1,        "D2":{"z":1        }}}',
            '{       "y":2, "D1":{        "y":2, "D2":{       "y":2 }}}'
        ]
    },
    'nofactors_a6_b4_F0_N3': {
        'n': ['a.json', 'b.json'],
        'i': [
            '{"x":1, "y":0, "D1":{ "x":1, "y":0, "D2":{"x":1, "y":0}} }',
            '{"z":1, "y":2, "D1":{ "z":1, "y":2} }'
        ],
        'O': [
            '{"x":1, "y":0, "D1":{ "x":1, "y":0, "D2":{"x":1, "y":0}} }',
            '{"z":1, "y":2, "D1":{ "z":1, "y":2} }', '{}'
        ]
    },
    'onefactor_a3_b2_F1_N1': {
        'n': ['a.json', 'b.json'],
        'i': [
            '{"x":1, "N1":{ "shared":"common", "myname":"own"}, "myvalue":42}',
            '{"N1":{ "shared":"common", "myownname":"own"}, "myvalue":-42}'
        ],
        'O': [
            '{"x":1, "N1":{                    "myname":"own"},     "myvalue":42}',
            '{       "N1":{                    "myownname":"own"}, "myvalue":-42}',
            '{       "N1":{ "shared":"common"}}',
        ]
    },
    'twofactors_a1_b1_F2_N2': {
        'n': ['a.json', 'b.json'],
        'i': [
            '{"N1":{ "shared":"common", "myname":"own"   }, "N1B":{"common2":42}}',
            '{"N1":{ "shared":"common", "myownname":"own"}, "N1B":{"common2":42}}'
        ],
        'O': [
            '{"N1":{                    "myname":"own"   }                      }',
            '{"N1":{                    "myownname":"own"}                      }',
            '{"N1":{ "shared":"common"                   }, "N1B":{"common2":42}}',
        ]
    },
    'allcommon_a0_b0_F2_N2': {
        'n': ['a.json', 'b.json'],
        'i': [
            '{"N1":{ "shared":"common", "common2":42}}',
            '{"N1":{ "shared":"common", "common2":42}}'
        ],
        'O': ['{}', '{}', '{"N1":{ "shared":"common", "common2":42}}'],
    },
    'mostcommon_a0_b22_F22_N2': {
        'n': ['a.json', 'b.json'],
        'i': [_J45_DE_CN_COMMON_ONE_LESS, _J45_DE_CN_COMMON],
        'O': ['{}', '{"J45":{' + _ONE_LESS + '}}', _J45_DE_CN_COMMON_ONE_LESS],
    },
    'basic_a1_b1_c1_F1_N1': {
        'n': ['a.json', 'b.json', 'c.json'],
        'i': ['{"w":0, "y":2}', '{"x":1, "y":2}', '{"z":3, "y":2}'],
        'O': ['{"w":0}', '{"x":1}', '{"z":3}', '{"y":2}']
    },
    'nesting_a3_b3_c3_F3_N3': {
        'n': ['a.json', 'b.json', 'c.json'],
        'i': [
            '{"w":1, "y":2, "D1":{ "w":1, "y":2, "D2":{"w":1, "y":2}}}',
            '{"x":1, "y":2, "D1":{ "x":1, "y":2, "D2":{"x":1, "y":2}}}',
            '{"z":1, "y":2, "D1":{ "z":1, "y":2, "D2":{"z":1, "y":2}}}'
        ],
        'O': [
            '{"w":1,        "D1":{ "w":1,        "D2":{"w":1        }}}',
            '{"x":1,        "D1":{ "x":1,        "D2":{"x":1        }}}',
            '{"z":1,        "D1":{ "z":1,        "D2":{"z":1        }}}',
            '{       "y":2, "D1":{        "y":2, "D2":{       "y":2 }}}'
        ]
    },
    'mostcommon_a0_b22_c0_F22_N2': {
        'n': ['a.json', 'b.json', 'c.json'],
        'i': [
            _J45_DE_CN_COMMON_ONE_LESS, _J45_DE_CN_COMMON,
            _J45_DE_CN_COMMON_ONE_LESS
        ],
        'O': [
            '{}', '{"J45":{' + _ONE_LESS + '}}', '{}',
            _J45_DE_CN_COMMON_ONE_LESS
        ],
    },
    'target_dir_up_same_down': {
        't': '/dir4output',
        'd': ['/X/Y/Z', '/dir4output'],
        'D': '/X/Y',
        'n': [
            '../a.json',
            'b.json',
            'Z/c.json',
        ],
        'i': ['{"x":1, "y":2}', '{"z":3, "y":2}', '{"w":4, "y":2}'],
        'O': ['{"x":1}', '{"z":3}', '{"w":4}', '{"y":2}']
    },
    'complicated': {
        'n': ['f1.json', 'f2.json', 'f3.json'],
        'i': [_F1, _F2, _F3],
        'O': [_O1, _O2, _O3, _O4],
    },
}

logger = logging.getLogger(__name__)


class Error(Exception):
    """Exceptions raised in this module are of this class."""


class TestFactorJson(tact.sub4t.JsonArrayIn):

    @classmethod
    def setUpClass(cls):
        logger.debug('in %s.setUpClass(cls).', cls.__name__)
        super().setUpClass()
        cls._td = _FACTOR_JSON

    def setUp(self):
        super().setUp()
        self._target_dir = None

    def _do_single_dirs(self, td, dl):
        super()._do_single_dirs(td, dl)
        if 't' in td:
            self._target_dir = self._resolve(td['t'], self._root_dir)
            self._checkDir('t', self._target_dir, dl, td)

    def _write_exp(self, content):
        p = os.path.join(self._root_dir, 'expected.0.json')
        with open(p, 'w', encoding='utf-8') as fp:
            fp.write(content)
        return p

    def _doit(self):
        infile = self._set_up_Ddni_mergelist(
            inspect.stack()[1].function[len('test_'):])
        logger.debug('Factoring %s.', infile)
        common_factors, factored_files, merge_files = act.factorjson.factor(
            infile, self._target_dir)
        logger.debug('Validating common factors: %s.', common_factors)
        O = self._td[self._testname]['O']
        exp_fn = self._write_exp(O[-1])
        self._assert_json_equal(common_factors, exp_fn)
        logger.debug('Validating factored_files: %s.', factored_files)
        for act_fn, exp_content, in_fn in zip(factored_files, O[:-1],
                                              self._td[self._testname]['n']):
            if act_fn is None and exp_content is None:
                logger.debug('All values factored out of %s.', in_fn)
            else:
                exp_fn = self._write_exp(exp_content)
                self._assert_json_equal(act_fn, exp_fn)
        logger.debug('Validate merge_files (by merging): %s.', merge_files)
        for merge_fn, source_fn in zip(
                merge_files, act.sub.read_and_resolve_path_array(infile)):
            act_fn = act.mergejson.merge(
                merge_fn, os.path.join(self._mergelist_dir, 'actual.json'),
                'IGNORE')
            self._assert_json_equal(act_fn, source_fn)

    def test_basic_a1_b1_F1_N1(self):
        self._doit()

    def test_j45_cn_de_a9_b9_F27_N2(self):
        self._doit()

    def test_nesting_a3_b3_F3_N3(self):
        self._doit()

    def test_nofactors_a6_b4_F0_N3(self):
        self._doit()

    def test_onefactor_a3_b2_F1_N1(self):
        self._doit()

    def test_twofactors_a1_b1_F2_N2(self):
        self._doit()

    def test_allcommon_a0_b0_F2_N2(self):
        self._doit()

    def test_mostcommon_a0_b22_F22_N2(self):
        self._doit()

    def test_basic_a1_b1_c1_F1_N1(self):
        self._doit()

    def test_nesting_a3_b3_c3_F3_N3(self):
        self._doit()

    def test_mostcommon_a0_b22_c0_F22_N2(self):
        self._doit()

    def test_target_dir_up_same_down(self):
        self._doit()

    def test_complicated(self):
        self._doit()


if __name__ == '__main__':
    tact.sub4t.set_up_root_logging(_LOG_LEVEL)
    act.factorjson.logger.setLevel(_LOG_LEVEL)
    unittest.main()
