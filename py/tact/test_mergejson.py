"""Unit tests for mergejson.

"""
import unittest
import os
import json
import inspect
import logging
# own imports
import act.mergejson
import act.sub
import tact.sub4t

_LOG_LEVEL = logging.CRITICAL

_MERGE_FILES = {
    # i = json list, one string per file to merge
    #
    # o = expected json result string
    # OR
    # x = excpetion  class and regex to match in text.
    #
    # name suffix _mMnN
    # M = number of json strings to merge
    # N = nesting depth of deepest element merged; top is 0
    # Last json in sequence is expected JSON result

    # Merge; basic; no nesting.
    'merge_basic_m2n0': {
        'i': [
            '{"a":1}',
            '{"b":"two"}',
        ],
        'o': '{"a":1,"b":"two"}'
    },
    # Merge; one of each type; no nesting.
    'merge_each_type_m5n0': {
        'i': [
            '{"a":0, "b":3.1415, "c":6.02e23, "d":-1}',
            '{"e":"true", "f":"false"}',
            '{"g":"null"}',
            '{"h":"H", "i":"The quick brown fox ..."}',
            '{"j":["a0","a1"]}',
        ],
        'o': ('{"a":0, "b":3.1415, "c":6.02e23, "d":-1,'
              '"e":"true", "f":"false",'
              '"g":"null",'
              '"h":"H", "i":"The quick brown fox ...",'
              '"j":["a0","a1"]}')
    },
    # Merge; basic; nested once.
    'merge_basic_m2n1': {
        'i': [
            '{"X":{"a":1}}',
            '{"X":{"b":"two"}}',
        ],
        'o': '{"X":{"a":1,"b":"two"}}'
    },
    # Merge; one of each type; nested twice.
    'merge_each_type_m5n2': {
        'i': [
            '{"X":{"Y":{"a":0, "b":3.1415, "c":6.02e23, "d":-1}}}',
            '{"X":{"Y":{"e":"true", "f":"false"}}}',
            '{"X":{"Y":{"g":"null"}}}',
            '{"X":{"Y":{"h":"H", "i":"The quick brown fox ..."}}}',
            '{"X":{"Y":{"j":["a0","a1"]}}}',
        ],
        'o': ('{"X":{"Y":{"a":0, "b":3.1415, "c":6.02e23, "d":-1,'
              '"e":"true", "f":"false",'
              '"g":"null",'
              '"h":"H", "i":"The quick brown fox ...","j":["a0","a1"]}}}')
    },
    # Replace; basic; no nesting.
    'replace_basic_m2n0': {
        'i': [
            '{"a":1}',
            '{"a":"one"}',
        ],
        'o': '{"a":"one"}'
    },
    # Replace; one of each type; nested once.
    'replace_primitive_types_m8n1': {
        'i': [
            '{"X":{"a":0, "b":3.1415, "c":6.02e23, "d":-1}}',
            '{"X":{"d":"Replacement for -1.", "c":7.02e23}}',
            '{"X":{"e":"true", "f":"false"}}', '{"X":{"g":"null"}}',
            '{"X":{"a":-1, "b":"null", "g":"true"}}',
            '{"X":{"e":4.1415, "f":42}}',
            '{"X":{"h":"H", "i":"The quick brown fox ..."}}',
            '{"X":{"h":"false", "i":"The slow red fox ..."}}'
        ],
        'o':
            ('{"X":{"a":-1, "b":"null", "c":7.02e23, "d":"Replacement for -1.",'
             '"e":4.1415, "f":42,'
             '"g":"true",'
             '"h":"false", "i":"The slow red fox ..."}}')
    },
    # Replace and merge; basic; nested once.
    'replace_and_merge_basic_m2n1': {
        'i': [
            '{"X":{"a":1, "b":"two"}}',
            '{"X":{"c":"C", "b":"null"}}',
        ],
        'o': '{"X":{"b":"null", "c":"C", "a":1}}'
    },
    # Replace and merge; array; nested once.
    'replace_and_merge_array_m2n1': {
        'i': [
            '{"X":{"a":1, "b":"two", "c":["0","1"]}}',
            '{"X":{"c":"C", "b":"null", "a":["3"]}}',
        ],
        'o': '{"X":{"b":"null", "c":"C", "a":["3"]}}'
    },
    # Replace and merge; one of each type; nested once.
    'replace_and_merge_primitive_types_m2n1': {
        'i': [
            '{"X":{"intK":1, "intR":2,      "floatK":3.4, "floatR":5.6,    "boolK":"true",  "boolR":"false", "nullK":"null", "nullR":"null"}}',
            '{"X":{"intM":9, "intR":"true", "floatM":7.6, "floatR":"null", "boolM":"false", "boolR":42,      "nullM":"null", "nullR":123.456}}',
        ],
        'o': (
            '{"X":{"intK":1,                "floatK":3.4,                  "boolK":"true",              "nullK":"null",  '
            '      "intM":9, "intR":"true", "floatM":7.6, "floatR":"null", "boolM":"false", "boolR":42, "nullM":"null", "nullR":123.456}}'
        )
    },
    # Actual ACT parameter example: J45 CN overrides DE
    'j45_cn_override_de_m2n1': {
        'i': [tact.sub4t.J45_DE, tact.sub4t.J45_CN_DELTA],
        'o': tact.sub4t.J45_CN
    },
    # Exception can't merge object with primitive type.
    'cant_merge_exception_m2n0': {
        'i': [
            '{"a":1}',
            '{"a":{"b":0}}',
        ],
        'x': [
            act.mergejson.JsonCanNotMergeObjectWithPrimitiveType,
            r"Target type <class 'int'>. Source type <class 'dict'>."
        ],
    },
    # Exception can't merge object with primitive type; nested.
    'cant_merge_exception_m2n1': {
        'i': [
            '{"X":{"a":{"b":0}}}',
            '{"X":{"a":1}}',
        ],
        'x': [
            act.mergejson.JsonCanNotMergeObjectWithPrimitiveType,
            r"Target type <class 'dict'>. Source type <class 'int'>."
        ],
    },
    # Command line help merge example
    'help_example_m2n1': {
        'i': [
            '{"X":{"a":1, "b":2}}',
            '{"X":{"b":"two"},"a":42}',
        ],
        'o': '{"X":{"a":1,"b":"two"},"a":42}'
    },
}

_MERGE_JSON = {
    # n = path list of files to merge.
    # i = json list, one string per file to merge
    #   o = expected json result string
    # OR
    #   x = excpetion  class and regex to match in text.
    # OPTIONAL
    # d = list of directories to create for test
    # D = directory for top level input file
    # M = mode4symbols value
    # S = symset value
    # m = mergelist file name
    'minimal': {
        'n': ['a.json',],
        'i': ['{"a":1}',],
        'o': '{"a":1}'
    },
    'up_same_down_1': {
        'd': ['/X/Y/Z'],
        'D': '/X/Y',
        'n': [
            '../a.json',
            'b.json',
            'Z/c.json',
        ],
        'i': [
            '{"a":1}',
            '{"b":"two"}',
            '{"c":"null"}',
        ],
        'o': '{"a":1,"b":"two","c":"null"}'
    },
    'up_dot_down_2': {
        'd': ['/V/W/X/Y/Z'],
        'D': '/V/W/X',
        'n': [
            '../../a.json',
            './b.json',
            'Y/Z/c.json',
        ],
        'i': [
            '{"a":1}',
            '{"b":"two"}',
            '{"c":"null"}',
        ],
        'o': '{"a":1,"b":"two","c":"null"}'
    },
    'sibblings': {
        'd': ['/V/W/X/Y/Z', '/A/B/C', '/T/U'],
        'D': '/A/B/C',
        'n': [
            '../../../V/a.json',
            '../../../T/U/b.json',
            '../../../V/W/X/Y/Z/c.json',
        ],
        'i': [
            '{"a":1}',
            '{"b":"two"}',
            '{"c":"null"}',
        ],
        'o': '{"a":1,"b":"two","c":"null"}'
    },
    'absolute': {
        'd': ['/X/Y/Z', '/S/T'],
        'D': '/X/Y',
        'n': [
            '/X/a.json',
            '/X/Y//b.json',
            '/S/T/c.json',
        ],
        'i': [
            '{"a":1}',
            '{"b":"two"}',
            '{"c":"null"}',
        ],
        'o': '{"a":1,"b":"two","c":"null"}'
    },
    # Test at least once each '--mode4symbols' option, except
    # act.sub.M4S_DIR which is tested in test_mergeall.py.
    'm4s_error': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b"}'],
        'M': act.sub.M4S_ERROR,
        'x': [
            act.mergejson.Error,
            r'--mode4symbols is "ERROR"',
        ],
    },
    'm4s_fname': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b","x":{"a":"z"}}'],
        'm': 'x.mergelist.json',
        'M': act.sub.M4S_FNAME,
        'o': '["z"]'
    },
    'm4s_global': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b","x":{"a":"z"}}'],
        'M': act.sub.M4S_GLOBAL,
        'o': '["b"]'
    },
    'm4s_ignore': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b","x":{"a":"z"}}'],
        'M': act.sub.M4S_IGNORE,
        'o': '["${a}"]'
    },
    'm4s_named': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b","quack":{"a":"duck"}}'],
        'M': act.sub.M4S_NAMED,
        'S': 'quack',
        'o': '["duck"]',
    },
}

logger = logging.getLogger(__name__)


class Error(Exception):
    """Exceptions raised in this module are of this class."""


class TestCheckTypes(unittest.TestCase):

    def test_array_illegal(self):
        d = json.loads('[1,2,3]')
        with self.assertRaisesRegex(act.sub.JsonArraysNotSupported,
                                    r"Where: \['string'\]"):
            act.sub.check_types(d, ['string'])

    def test_illegal_type(self):
        d = json.loads('{"a":1}')
        d['a'] = complex('1+2j')
        with self.assertRaisesRegex(act.sub.Error, r"Where: \['string'\, 'a']"):
            act.sub.check_types(d, ['string'])


class TestMergeFiles(tact.sub4t.DirPerTest):

    _td = _MERGE_FILES

    def setUp(self):
        super().setUp()
        self._files_created = set()

    def _outpath(self, fname):
        op = tact.sub4t.canonicalpath(os.path.join(self._root_dir, fname))
        if op in self._files_created:
            self.fail(f'{tact.sub4t.TEST_DATA_ERROR_MSG} {self._testname} '
                      f'Duplicate output file path "{op}".')
        self._files_created.add(op)
        return op

    def _to_files(self, json_string_list):
        path_list = []
        count = 0
        for j in json_string_list:
            count += 1
            p = self._outpath(f'in.{count}.json')
            with open(p, 'w', encoding='utf-8') as fp:
                fp.write(j)
            path_list.append(p)
        p = self._outpath('in.mergelist.json')
        act.sub.write_as_json(path_list, p)
        return p

    def _doit(self):
        # pylint: disable=no-member
        self._testname_root_dir(inspect.stack()[1].function[len('test_'):])
        td = self._td[self._testname]
        mergelist_path = self._to_files(td['i'])
        if 'o' in td:
            act_file = act.mergejson.merge(mergelist_path,
                                           self._outpath('actual.json'),
                                           act.sub.M4S_ERROR)
            exp_file = self._outpath('expected.json')
            with open(exp_file, 'w', encoding='utf-8') as fp:
                fp.write(td['o'])
            self._assert_json_equal(act_file, exp_file)
        else:
            with self.assertRaisesRegex(td['x'][0], td['x'][1]):
                act.mergejson.merge(mergelist_path, 'dummy', act.sub.M4S_ERROR)

    def test_merge_basic_m2n0(self):
        self._doit()

    def test_merge_each_type_m5n0(self):
        self._doit()

    def test_merge_basic_m2n1(self):
        self._doit()

    def test_replace_and_merge_array_m2n1(self):
        self._doit()

    def test_merge_each_type_m5n2(self):
        self._doit()

    def test_replace_basic_m2n0(self):
        self._doit()

    def test_replace_primitive_types_m8n1(self):
        self._doit()

    def test_replace_and_merge_basic_m2n1(self):
        self._doit()

    def test_replace_and_merge_primitive_types_m2n1(self):
        self._doit()

    def test_j45_cn_override_de_m2n1(self):
        self._doit()

    def test_cant_merge_exception_m2n0(self):
        self._doit()

    def test_cant_merge_exception_m2n1(self):
        self._doit()

    def test_help_example_m2n1(self):
        self._doit()


class TestMergeJson(tact.sub4t.JsonArrayIn):

    _td = _MERGE_JSON

    def _doit(self):
        infile = self._set_up_Ddni_mergelist(
            inspect.stack()[1].function[len('test_'):])
        td = self._td[self._testname]
        fname = td.get('m')
        if fname:
            new_name = os.path.join(os.path.split(infile)[0], fname)
            os.rename(infile, new_name)
            infile = new_name
        mode4symbols = act.sub.M4S_ERROR
        symset = td.get('S')
        if 'M' in td:
            mode4symbols = td['M']
        if 'o' in td:
            fn_act = act.mergejson.merge(
                infile, os.path.join(self._root_dir, 'actual.json'),
                mode4symbols, symset)
            fn_exp = os.path.join(self._root_dir, 'expected.json')
            with open(fn_exp, 'w', encoding='utf-8') as fp:
                fp.write(self._td[self._testname]['o'])
            self._assert_json_equal(fn_act, fn_exp)
        else:
            with self.assertRaisesRegex(td['x'][0], td['x'][1]):
                act.mergejson.merge(infile, 'dummy', mode4symbols, symset)

    def test_minimal(self):
        self._doit()

    def test_up_same_down_1(self):
        self._doit()

    def test_up_dot_down_2(self):
        self._doit()

    def test_sibblings(self):
        self._doit()

    def test_absolute(self):
        self._doit()

    def test_m4s_error(self):
        self._doit()

    def test_m4s_fname(self):
        self._doit()

    def test_m4s_global(self):
        self._doit()

    def test_m4s_ignore(self):
        self._doit()

    def test_m4s_named(self):
        self._doit()


class TestMergelistInMergelist(tact.sub4t.TestMergelistBase):

    _td = {
        'minimal': {
            'n': ['m.json', 'n.json', 'a.json'],
            'i': ['["n.json"]', '["a.json"]', '{"x":0}'],
            'o': '{"x":0}',
        },
        'basic': {
            'n': ['m.json', 'n.json', 'a.json', 'b.json'],
            'i': ['["n.json", "a.json"]', '["b.json"]', '{"x":0}', '{"y":1}'],
            'o': '{"x":0,"y":1}',
        },
        'user_guide': {
            'n': [
                'm0.json',
                'm1.json',
                'm2.json',
                'v0.json',
                'v1.json',
                'v2.json',
            ],
            'i': [
                '["v0.json","m1.json"]',
                '["m2.json","v1.json"]',
                '["v2.json"]',
                '{"o":"override A","keep0":0}',
                '{"o":"override B","keep1":1}',
                '{"o":"override C","keep2":2}',
            ],
            'o': '{"keep0":0,"keep1":1,"keep2":2,"o":"override B"}'
        },
        'three_deep': {
            'n': ['m.json', 'n.json', 'a.json', 'b.json'],
            'i': ['["n.json", "a.json"]', '["b.json"]', '{"x":0}', '{"y":1}'],
            'o': '{"x":0,"y":1}',
        },
        'three_wide': {
            'n': [
                'm.json', 'n.json', 'o.json', 'p.json', 'a.json', 'b.json',
                'c.json', 'd.json'
            ],
            'i': [
                '["n.json", "o.json", "p.json"]',
                '["a.json"]',
                '["b.json", "c.json"]',
                '["d.json"]',
                '{"w":0, "W":9,         "Y":119        }',
                '{"x":1,        "X":10, "Y":118, "Z":13}',
                '{"y":2, "W":99,        "Y":117        }',
                '{"z":3,                "Y":116, "Z":12}',
            ],
            # Last one wins. Order is a,b,c,d.
            'o': ('{"w":0,"x":1,"y":2,"z":3,'
                  '       "W":99,"X":10,  "Y":116, "Z":12}')
        },
        'minimal_cycle': {
            'n': ['m.json'],
            'i': ['["m.json"]'],
            'x': [
                act.sub.MergeListCycle,
                r'Merge list in merge list makes loop\:.*m\.json.*m\.json'
            ],
        },
        'basic_cycle': {
            'n': ['m.json', 'n.json', 'a.json', 'b.json'],
            'i': [
                '["n.json", "a.json"]', '["b.json", "m.json"]', '{"x":0}',
                '{"x":1}'
            ],
            'x': [
                act.sub.MergeListCycle,
                r'Merge list in merge list makes loop\:.*m\.json.*m\.json.*n\.json'
            ],
        },
    }

    def test_minimal(self):
        self._doit()

    def test_basic(self):
        self._doit()

    def test_user_guide(self):
        self._doit()

    def test_three_deep(self):
        self._doit()

    def test_three_wide(self):
        self._doit()

    def test_minimal_cycle(self):
        self._doit()

    def test_basic_cycle(self):
        self._doit()


if __name__ == '__main__':
    tact.sub4t.set_up_root_logging(_LOG_LEVEL)
    act.mergejson.logger.setLevel(_LOG_LEVEL)
    unittest.main()
