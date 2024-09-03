"""Unit tests for mergeall.py.
"""
import os
import logging
# own imports
import tact.sub4t

_LOG_LEVEL = logging.INFO
_MAJ_FNAME = os.path.normcase('mergeall.args.json')
_EXCLUDE_FNAME = os.path.normcase('mergeall.exclude.json')

# Test Data (TD) key meanings:
# n : see tact.sub4t.JsonArrayIn._set_up_Ddni
# i : see tact.sub4t.JsonArrayIn._set_up_Ddni
# N : list of expected result file paths. Paths must be relative, resolved from
#     the output directory (see O key). All these files and none others must be
#     present under the output directory or test fails.
# I : list of content as strings of each N file, corresponding 1:1 with N list.
# O : (optional) output directory relative path. If present, resolved from
#     parent dir of test's _root_dir and passed to mergeall.py as command line
#     option --outdir.
#
# Test Name suffix
# _d4s => run mergeall.py with --mode4symbols DIR command line option.

_TD = {
    'minimal': {
        'n': ['z.json', 'mergelist.json'],
        'i': ['{"b":1}', '["z.json"]'],
        'N': ['merged.json'],
        'I': ['{"b":1}'],
    },
    'minimal_a': {
        'n': ['a.json', 'a.mergelist.json'],
        'i': ['{"x":1}', '["a.json"]'],
        'N': ['a.merged.json'],
        'I': ['{"x":1}'],
    },
    'plain': {
        # two subdirs
        # one has two mergelists
        # the other three mergelists
        # each subdrir has a shared common file
        # and a per-mergelist own file
        'n': [
            'd1/a.mergelist.json',
            'd1/b.mergelist.json',
            'd1/a.json',
            'd1/b.json',
            'd1/common.json',
            'd2/a.mergelist.json',
            'd2/b.mergelist.json',
            'd2/c.mergelist.json',
            'd2/a.json',
            'd2/b.json',
            'd2/c.json',
            'd2/common.json',
        ],
        'i': [
            '["a.json","common.json"]',
            '["b.json","common.json"]',
            '{"a":1}',
            '{"b":2}',
            '{"C":3}',
            '["a.json","common.json"]',
            '["b.json","common.json"]',
            '["c.json","common.json"]',
            '{"a2":4}',
            '{"b2":5}',
            '{"c2":6}',
            '{"C2":7}',
        ],
        'N': [
            'd1/a.merged.json',
            'd1/b.merged.json',
            'd2/a.merged.json',
            'd2/b.merged.json',
            'd2/c.merged.json',
        ],
        'I': [
            '{"a":1,"C":3}',
            '{"b":2,"C":3}',
            '{"a2":4,"C2":7}',
            '{"b2":5,"C2":7}',
            '{"c2":6,"C2":7}',
        ],
    },
    'fancy': {
        # depth one
        # depth two
        # depth three
        # one merge file
        # two merge files
        # three merge files
        # sub dir w/o merge file
        # long merge file name "a.b.c.d.mergelist.json"
        # typical merge file name "de.mergelist.json
        'n': [
            'A/common.json',
            'A/de.mergelist.json',
            'A/de.json',
            'A/fr.mergelist.json',
            'A/fr.json',
            'A/us.mergelist.json',
            'A/us.json',
            'B/C/cmn.json',
            'B/C/ch.mergelist.json',
            'B/C/ch.json',
            'B/C/D/some.mergelist.json',
            'B/C/D/forsome.json',
            'B/C/D/a.b.c.d.mergelist.json',
            'B/C/D/w.x.y.z.json',
        ],
        'i': [
            '{"A":1}',
            '["de.json","common.json"]',
            '{"country":"germany"}',
            '["fr.json","common.json"]',
            '{"country":"France"}',
            '["us.json","common.json"]',
            '{"country":"U.S.A."}',
            '{"BCD":2}',
            '["ch.json","cmn.json"]',
            '{"country":"switzerland"}',
            '["forsome.json"]',
            '{"answer":42}',
            '["w.x.y.z.json"]',
            '{"wxyz":"Z"}',
        ],
        'N': [
            'A/de.merged.json',
            'A/fr.merged.json',
            'A/us.merged.json',
            'B/C/ch.merged.json',
            'B/C/D/some.merged.json',
            'B/C/D/a.b.c.d.merged.json',
        ],
        'I': [
            '{"A":1,"country":"germany"}',
            '{"A":1,"country":"France"}',
            '{"A":1,"country":"U.S.A."}',
            '{"BCD":2,"country":"switzerland"}',
            '{"answer":42}',
            '{"wxyz":"Z"}',
        ],
    },
    'trivial_d4s': {
        # No symbol sets in symbol file.
        'n': ['a.json', 'a.mergelist.json', 'symbols.json'],
        'i': ['{"b":"${x}"}', '["a.json", "symbols.json"]', '{"x":"0"}'],
        'N': ['a.merged.json'],
        'I': ['{"b":"0"}'],
    },
    'minimal_d4s': {
        # One symbol set in symbol file, no global symbols.
        'n': ['a.json', 'a.mergelist.json', 'symbols.json'],
        'i': ['{"b":"${x}"}', '["a.json", "symbols.json"]', '{"S":{"x":"1"}}'],
        'N': ['S/a.merged.json', 'a.merged.json'],
        'I': ['{"b":"1"}', '{"b":"${x}"}'],
    },
    'minimal_w_global_d4s': {
        # One symbol set in symbol file, with global symbols.
        'n': ['a.json', 'a.mergelist.json', 'symbols.json'],
        'i': [
            '{"b":"${x}"}', '["a.json", "symbols.json"]',
            '{"S":{"x":"1"}, "x":"2"}'
        ],
        'N': ['S/a.merged.json', 'a.merged.json'],
        'I': ['{"b":"1"}', '{"b":"2"}'],
    },
    'mergelist321_symset123_d4s': {
        # Tests sub-directory per symbol set creation.
        # A/Q A/R A/S
        # mergelists: Q 3, R 2, S 1
        # symbolsets: Q 1, R 2, S 3
        # only symbol file in S has global symbols
        'n': [
            'A/Q/x.mergelist.json',
            'A/Q/y.mergelist.json',
            'A/Q/z.mergelist.json',
            'A/Q/f.json',
            'A/Q/symbols.json',
            'A/R/xx.mergelist.json',
            'A/R/yy.mergelist.json',
            'A/R/symbols.json',
            'A/S/xxx.mergelist.json',
            'A/S/symbols.json',
        ],
        'i': [
            '["f.json", "symbols.json"]',
            '["f.json", "symbols.json"]',
            '["f.json", "symbols.json"]',
            '{"p":"${x}"}',
            '{"S1":{"x":"1"}}',
            '["../Q/f.json", "symbols.json"]',
            '["../Q/f.json", "symbols.json"]',
            '{"S2":{"x":"2"},"S3":{"x":"3"}}',
            '["../Q/f.json", "symbols.json"]',
            '{"S4":{"x":"4"},"S5":{"x":"5"},"S6":{"x":"6"},"x":"7"}',
        ],
        'N': [
            'A/Q/S1/x.merged.json',
            'A/Q/S1/y.merged.json',
            'A/Q/S1/z.merged.json',
            'A/Q/x.merged.json',
            'A/Q/y.merged.json',
            'A/Q/z.merged.json',
            'A/R/S2/xx.merged.json',
            'A/R/S2/yy.merged.json',
            'A/R/S3/xx.merged.json',
            'A/R/S3/yy.merged.json',
            'A/R/xx.merged.json',
            'A/R/yy.merged.json',
            'A/S/S4/xxx.merged.json',
            'A/S/S5/xxx.merged.json',
            'A/S/S6/xxx.merged.json',
            'A/S/xxx.merged.json',
        ],
        'I': [
            '{"p":"1"}',
            '{"p":"1"}',
            '{"p":"1"}',
            '{"p":"${x}"}',
            '{"p":"${x}"}',
            '{"p":"${x}"}',
            '{"p":"2"}',
            '{"p":"2"}',
            '{"p":"3"}',
            '{"p":"3"}',
            '{"p":"${x}"}',
            '{"p":"${x}"}',
            '{"p":"4"}',
            '{"p":"5"}',
            '{"p":"6"}',
            '{"p":"7"}',
        ],
    },
    'ledgers_d4s': {
        # Test pACT actual use case with minimal subset of real parameters.
        # Parameters for one pACT: 3 countries, 4 different ledger settings.
        # Ledger settings in common shared file.
        'O':
            'out',
        'n': [
            'j45/vanilla/symbols.json',
            'j45/vanilla/common.json',
            'j45/vanilla/de.mergelist.json',
            'j45/vanilla/us.mergelist.json',
            'j45/vanilla/fr.mergelist.json',
            'j45/vanilla/de.json',
            'j45/vanilla/us.json',
            'j45/vanilla/fr.json',
        ],
        'i': [
            ('{"local" : { "LEDGER_SETUP":"LOCAL"  }\n'
             ',"ifrs"  : { "LEDGER_SETUP":"IFRS"   }\n'
             ',"usgaap": { "LEDGER_SETUP":"USGAAP" }\n'
             ',"all"   : { "LEDGER_SETUP":"ALL"    }\n'
             ',            "LEDGER_SETUP":"ALL"     \n'
             '}'),
            '{"ACT":{"QTY":"1.0","LEDGER_SETUP":"${LEDGER_SETUP}"}}',
            '["common.json", "de.json", "symbols.json"]',
            '["common.json", "us.json", "symbols.json"]',
            '["common.json", "fr.json", "symbols.json"]',
            '{"ACT":{"BUKRS":"1010"}}',
            '{"ACT":{"BUKRS":"1710"}}',
            '{"ACT":{"BUKRS":"1210"}}',
        ],
        'N': [
            'j45/vanilla/de.merged.json',
            'j45/vanilla/us.merged.json',
            'j45/vanilla/fr.merged.json',
            'j45/vanilla/local/de.merged.json',
            'j45/vanilla/local/us.merged.json',
            'j45/vanilla/local/fr.merged.json',
            'j45/vanilla/ifrs/de.merged.json',
            'j45/vanilla/ifrs/us.merged.json',
            'j45/vanilla/ifrs/fr.merged.json',
            'j45/vanilla/usgaap/de.merged.json',
            'j45/vanilla/usgaap/us.merged.json',
            'j45/vanilla/usgaap/fr.merged.json',
            'j45/vanilla/all/de.merged.json',
            'j45/vanilla/all/us.merged.json',
            'j45/vanilla/all/fr.merged.json',
        ],
        'I': [
            '{"ACT":{"QTY":"1.0","BUKRS":"1010","LEDGER_SETUP":"ALL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1710","LEDGER_SETUP":"ALL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1210","LEDGER_SETUP":"ALL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1010","LEDGER_SETUP":"LOCAL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1710","LEDGER_SETUP":"LOCAL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1210","LEDGER_SETUP":"LOCAL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1010","LEDGER_SETUP":"IFRS"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1710","LEDGER_SETUP":"IFRS"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1210","LEDGER_SETUP":"IFRS"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1010","LEDGER_SETUP":"USGAAP"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1710","LEDGER_SETUP":"USGAAP"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1210","LEDGER_SETUP":"USGAAP"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1010","LEDGER_SETUP":"ALL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1710","LEDGER_SETUP":"ALL"}}',
            '{"ACT":{"QTY":"1.0","BUKRS":"1210","LEDGER_SETUP":"ALL"}}',
        ],
    },
    'symset_subdir_override_topdown_d4s': {
        # Test that would fail if mergelist paths were processed in
        # alphabetical and not top down order.
        'n': [
            'x/ae.mergelist.json',
            'x/cn.mergelist.json',
            'x/ifrs/cn.mergelist.json',
            'x/ifrs/zw.mergelist.json',
            'x/zw.mergelist.json',
            'x/symbols.json',
            'x/basedir.json',
            'x/ifrs/subdir.json',
        ],
        'i': [
            '["symbols.json", "basedir.json"]',
            '["symbols.json", "basedir.json"]',
            '["subdir.json"]',
            '["subdir.json"]',
            '["symbols.json", "basedir.json"]',
            '{"ifrs":{"answer":"42"}, "answer":"a question"}',
            '{"the_answer_is":"${answer}"}',
            '{"p":"0"}',
        ],
        'N': [
            'x/ae.merged.json',
            'x/cn.merged.json',
            'x/zw.merged.json',
            'x/ifrs/ae.merged.json',
            'x/ifrs/cn.merged.json',  # overridden
            'x/ifrs/zw.merged.json',  # overridden
        ],
        'I': [
            '{"the_answer_is":"a question"}',
            '{"the_answer_is":"a question"}',
            '{"the_answer_is":"a question"}',
            '{"the_answer_is":"42"}',
            '{"p":"0"}',
            '{"p":"0"}',
        ],
    },
}

logger = logging.getLogger(__name__)


class Error(Exception):
    """Exceptions raised in this module are of this class."""


class TestMergeall(tact.sub4t.TestMergeallBase):

    _td = _TD

    def test_minimal(self):
        self._doit()

    def test_minimal_a(self):
        self._doit()

    def test_plain(self):
        self._doit()

    def test_fancy(self):
        self._doit()

    def test_trivial_d4s(self):
        self._doit()

    def test_minimal_d4s(self):
        self._doit()

    def test_minimal_w_global_d4s(self):
        self._doit()

    def test_mergelist321_symset123_d4s(self):
        self._doit()

    def test_ledgers_d4s(self):
        self._doit()

    def test_symset_subdir_override_topdown_d4s(self):
        self._doit()


class TestMergeallM4S(tact.sub4t.TestMergeallBase):
    """Test merge all with mode for symbols overridden in json files.
    
    The new mode applies for the current dir and all subdirs (until overridden 
    in a subdir).
    """

    _td = {
        # Override command line args at root (depth 0).
        # From ERROR to IGNORE, (mergelist has symbol.json).
        'minimal': {
            'M': 'ERROR',
            'n': ['a.json', 'a.mergelist.json', 'symbols.json', _MAJ_FNAME],
            'i': [
                '{"p":"${x}"}',
                '["a.json", "symbols.json"]',
                '{"x":"0"}',
                '{"--mode4symbols":"IGNORE"}',
            ],
            'N': ['a.merged.json'],
            'I': ['{"p":"${x}"}'],
        },
        # Override command line args at root (depth 0).
        # From ERROR to GLOBAL.
        'd0_error_to_global': {
            'M': 'ERROR',
            'n': ['a.json', 'a.mergelist.json', 'symbols.json', _MAJ_FNAME],
            'i': [
                '{"p":"${x}"}',
                '["a.json", "symbols.json"]',
                '{"x":"1"}',
                '{"--mode4symbols":"GLOBAL"}',
            ],
            'N': ['a.merged.json'],
            'I': ['{"p":"1"}'],
        },
        # Override command line args at root (depth 0).
        # Change symbol set.
        'd0_change_symset': {
            'M': 'NAMED',
            'S': 'A',
            'n': ['a.json', 'a.mergelist.json', 'symbols.json', _MAJ_FNAME],
            'i': [
                '{"p":"${x}"}',
                '["a.json", "symbols.json"]',
                '{"A":{"x":"a1"},"B":{"x":"b2"}}',
                '{"--mode4symbols":"NAMED", "--symset":"B"}',
            ],
            'N': ['a.merged.json'],
            'I': ['{"p":"b2"}'],
        },
        # Test override applies under sub branch.
        # One override only: change symbol set.
        'd3_sub_branch_only': {
            'M':
                'NAMED',
            'S':
                'A',
            'n': [
                'a.json',
                'a.mergelist.json',
                'symbols.json',
                f'left/{_MAJ_FNAME}',
                'left/a.mergelist.json',
                'left/left/a.mergelist.json',
                'left/right/a.mergelist.json',
                'right/a.mergelist.json',
                'right/left/a.mergelist.json',
                'right/right/a.mergelist.json',
            ],
            'i': [
                '{"p":"${x}"}',
                '["a.json", "symbols.json"]',
                '{"A":{"x":"a1"},"B":{"x":"b2"}}',
                # left branch
                '{"--mode4symbols":"NAMED", "--symset":"B"}',
                '["../a.json", "../symbols.json"]',
                '["../../a.json", "../../symbols.json"]',
                '["../../a.json", "../../symbols.json"]',
                # right branch
                '["../a.json", "../symbols.json"]',
                '["../../a.json", "../../symbols.json"]',
                '["../../a.json", "../../symbols.json"]',
            ],
            'N': [
                'a.merged.json',
                'left/a.merged.json',
                'left/left/a.merged.json',
                'left/right/a.merged.json',
                'right/a.merged.json',
                'right/left/a.merged.json',
                'right/right/a.merged.json',
            ],
            'I': [
                '{"p":"a1"}',
                '{"p":"b2"}',
                '{"p":"b2"}',
                '{"p":"b2"}',
                '{"p":"a1"}',
                '{"p":"a1"}',
                '{"p":"a1"}',
            ],
        },
        # Test override in every sub-directory.
        # One sub-directory has two merge lists, one called mergelist.json
        'd3_everywhere': {
            'M':
                'NAMED',
            'S':
                'A',
            'n': [
                'a.json',
                'b.json',
                'a.mergelist.json',
                'symbols.json',
                f'{_MAJ_FNAME}',
                f'left/{_MAJ_FNAME}',
                'left/a.mergelist.json',
                f'left/left/{_MAJ_FNAME}',
                'left/left/a.mergelist.json',
                f'left/right/{_MAJ_FNAME}',
                'left/right/a.mergelist.json',
                f'right/{_MAJ_FNAME}',
                'right/a.mergelist.json',
                'right/mergelist.json',
                f'right/left/{_MAJ_FNAME}',
                'right/left/a.mergelist.json',
                f'right/right/{_MAJ_FNAME}',
                'right/right/a.mergelist.json',
            ],
            'i': [
                '{"p":"${x}"}',
                '{"pb":"${x}"}',
                '["a.json", "symbols.json"]',
                '''{
                "A":{"x":"a1"},"B":{"x":"b2"},"C":{"x":"c3"},
                "D":{"x":"d4"},"E":{"x":"e5"},"F":{"x":"f6"},
                "G":{"x":"g7"},"H":{"x":"h8"}
                }
                ''',
                '{"--mode4symbols":"NAMED", "--symset":"B"}',
                # left branch
                '{"--mode4symbols":"NAMED", "--symset":"C"}',
                '["../a.json", "../symbols.json"]',
                '{"--mode4symbols":"NAMED", "--symset":"D"}',
                '["../../a.json", "../../symbols.json"]',
                '{"--mode4symbols":"NAMED", "--symset":"E"}',
                '["../../a.json", "../../symbols.json"]',
                # right branch
                '{"--mode4symbols":"NAMED", "--symset":"F"}',
                '["../a.json", "../symbols.json"]',
                '["../b.json", "../symbols.json"]',
                '{"--mode4symbols":"NAMED", "--symset":"G"}',
                '["../../a.json", "../../symbols.json"]',
                '{"--mode4symbols":"NAMED", "--symset":"H"}',
                '["../../a.json", "../../symbols.json"]',
            ],
            'N': [
                'a.merged.json',
                'left/a.merged.json',
                'left/left/a.merged.json',
                'left/right/a.merged.json',
                'right/a.merged.json',
                'right/merged.json',
                'right/left/a.merged.json',
                'right/right/a.merged.json',
            ],
            'I': [
                '{"p":"b2"}',
                '{"p":"c3"}',
                '{"p":"d4"}',
                '{"p":"e5"}',
                '{"p":"f6"}',
                '{"pb":"f6"}',
                '{"p":"g7"}',
                '{"p":"h8"}',
            ],
        },
        # Variety. Override (*) in various sub-directories.
        #                   top A
        #      left         mid*C        right
        # left*B right | left  right | left  right*D
        "d3_various": {
            'M':
                'NAMED',
            'S':
                'A',
            'n': [
                'symbols.json',
                'a.json',
                'mergelist.json',
                'left/mergelist.json',
                f'left/left/{_MAJ_FNAME}',
                'left/left/mergelist.json',
                'left/right/mergelist.json',
                f'mid/{_MAJ_FNAME}',
                'mid/mergelist.json',
                'mid/left/mergelist.json',
                'mid/right/mergelist.json',
                'right/mergelist.json',
                'right/left/mergelist.json',
                'right/right/mergelist.json',
                f'right/right/{_MAJ_FNAME}',
            ],
            'i': [
                ('{"A":{"x":"1"},"B":{"x":"2"},"C":{"x":"3"},'
                 '"D":{"x":"4"}}'),
                '{"p":"${x}"}',
                '["a.json", "symbols.json"]',  # top
                '["../a.json", "../symbols.json"]',  # left
                '{"--mode4symbols":"NAMED", "--symset":"B"}',  # left left
                '["../../a.json", "../../symbols.json"]',  # left left
                '["../../a.json", "../../symbols.json"]',  # left right
                '{"--mode4symbols":"NAMED", "--symset":"C"}',  # mid
                '["../a.json", "../symbols.json"]',  # mid 
                '["../../a.json", "../../symbols.json"]',  # mid left
                '["../../a.json", "../../symbols.json"]',  # mid right
                '["../a.json", "../symbols.json"]',  # right
                '["../../a.json", "../../symbols.json"]',  # right left
                '["../../a.json", "../../symbols.json"]',  # right right
                '{"--mode4symbols":"NAMED", "--symset":"D"}',  # right right
            ],
            'N': [
                'merged.json',  # A
                'left/merged.json',  # A
                'left/left/merged.json',  # B
                'left/right/merged.json',  # A
                'mid/merged.json',  # C
                'mid/left/merged.json',  # C
                'mid/right/merged.json',  # C
                'right/merged.json',  # A
                'right/left/merged.json',  # A
                'right/right/merged.json',  # D
            ],
            'I': [
                '{"p":"1"}',
                '{"p":"1"}',
                '{"p":"2"}',
                '{"p":"1"}',
                '{"p":"3"}',
                '{"p":"3"}',
                '{"p":"3"}',
                '{"p":"1"}',
                '{"p":"1"}',
                '{"p":"4"}',
            ],
        },
    }

    _CALL_STACK_FNAME_INDEX = 3

    def _setup(self):
        outdir, arg_v = super()._setup()
        td = self._td[self._testname]
        for k, argname in [('M', '--mode4symbols'), ('S', '--symset')]:
            v = td.get(k)
            if v:
                arg_v.append(argname)
                arg_v.append(v)
        return (outdir, arg_v)

    def test_minimal(self):
        self._doit()

    def test_d0_error_to_global(self):
        self._doit()

    def test_d0_change_symset(self):
        self._doit()

    def test_d3_sub_branch_only(self):
        self._doit()

    def test_d3_everywhere(self):
        self._doit()

    def test_d3_various(self):
        self._doit()


class TestMergeallExclude(tact.sub4t.TestMergeallBase):

    _td = {
        # One file, exclude it.
        'minimal': {
            'n': ['mergelist.json', _EXCLUDE_FNAME],
            'i': ['["a.json"]', '["mergelist.json"]'],
            'N': [],
            'I': [],
        },
        # Two files, exclude one.
        'vanilla': {
            'n': [
                'a.json', 'a.mergelist.json', 'mergelist.json', _EXCLUDE_FNAME
            ],
            'i': [
                '{"name":"value"}',
                'Work in progress.',
                '["a.json"]',
                '["a.mergelist.json"]',
            ],
            'N': ['merged.json'],
            'I': ['{"name":"value"}'],
        },
        # Three dirs deep.
        #     top a,b exclude a
        #     mid a,b exclude b
        #     bottom a.b.c exclude a, b
        'fancy': {
            'n': [
                't/a.json',
                't/a.mergelist.json',
                't/b.mergelist.json',
                _EXCLUDE_FNAME,
                't/m/a.mergelist.json',
                't/m/b.mergelist.json',
                f't/m/{_EXCLUDE_FNAME}',
                't/m/b/a.mergelist.json',
                't/m/b/b.mergelist.json',
                't/m/b/c.mergelist.json',
                f't/m/b/{_EXCLUDE_FNAME}',
            ],
            'i': [
                '{"name":"value"}',
                'Work in progress.',
                '["a.json"]',
                '["a.mergelist.json"]',
                '["../a.json"]',
                'Work in progress.',
                '["b.mergelist.json"]',
                'Work in progress.',
                'Work in progress.',
                '["../../a.json"]',
                '["a.mergelist.json","b.mergelist.json"]',
            ],
            'N': [
                't/b.merged.json',
                't/m/a.merged.json',
                't/m/b/c.merged.json',
            ],
            'I': ['{"name":"value"}', '{"name":"value"}', '{"name":"value"}'],
        },
    }

    def test_minimal(self):
        self._doit()

    def test_vanilla(self):
        self._doit()

    def test_fancy(self):
        self._doit()
