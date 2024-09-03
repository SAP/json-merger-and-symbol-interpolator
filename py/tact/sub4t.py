"""Stuff used in more than one unit test module."""
import unittest
import os
import json
import logging
import tempfile
import shutil
import inspect
# 3rd party imports
import jcs
# own imports
import act.mergejson
import act.mergeall

_OUT_DIR = os.path.join(tempfile.gettempdir(), 'sap.act.py')
_OUT_DIR_PREFIX = 'out.4ut.'

TEST_DATA_ERROR_MSG = 'TEST DATA ERROR:'

J45_DE = """
{"J45":{"COUNTRY":"DE","COMPANY_CODE":"1010","CURRENCY":"EUR","PLANT":"1010",
"PURCH_ORG":"1010","S_LOC":"101A","SUPPLIER":"0010300001",
"SUPPLIER_NAME":"Inlandslieferant DE 1","TAX_CODE":"V0","RLDNR_0":"0L",
"RLDNR_1":"2L","RLDNR_2":"3L","GL_GR_IR_NUM":"0021120000",
"GL_GR_IR_TXT":"GR/IR","GL_INV_T_GOODS_NUM":"0013600000",
"GL_INV_T_GOODS_TXT":"Inventory TradingGd","GL_PAYBLS_DOM_NUM":"0021100000",
"GL_PAYBLS_DOM_TXT":"Paybls Domestic","JE_KEY_C":"31","JE_KEY_D":"86",
"IR_AMT_C":"-1.0","MAT":"TG11","MAT_SHORT_TEXT":"Vanilla test J45",
"POST_AMT":"1.0","PRICE":"1.0","PRICE_UNIT":"1","QTY":"1.0","UNITS":"PC",
"IR_REF_TEXT":"123456789A123456","IR_TAX_AMT":"0.0","PO_ITEM":"00010",
"ACCTASSCAT":"","PO_PRICE":"1","MOVE_TYPE":"101","MVT_IND":"B",
"JOURNAL_ENTRY_NO":"2"}}
"""

J45_CN = """
{"J45":{"COUNTRY":"CN","COMPANY_CODE":"1310","CURRENCY":"CNY","PLANT":"1310",
"PURCH_ORG":"1310","S_LOC":"131A","SUPPLIER":"0013300001",
"SUPPLIER_NAME":"Domestic Supplier CN 1","TAX_CODE":"J0","RLDNR_0":"0L",
"RLDNR_1":"2L","RLDNR_2":"3L","GL_GR_IR_NUM":"0021120000",
"GL_GR_IR_TXT":"GR/IR","GL_INV_T_GOODS_NUM":"0013600000",
"GL_INV_T_GOODS_TXT":"Inventory TradingGd","GL_PAYBLS_DOM_NUM":"0021100000",
"GL_PAYBLS_DOM_TXT":"Paybls Domestic","JE_KEY_C":"31","JE_KEY_D":"86",
"IR_AMT_C":"-1.0","MAT":"TG11","MAT_SHORT_TEXT":"Vanilla test J45",
"POST_AMT":"1.0","PRICE":"1.0","PRICE_UNIT":"1","QTY":"1.0","UNITS":"PC",
"IR_REF_TEXT":"123456789A123456","IR_TAX_AMT":"0.0","PO_ITEM":"00010",
"ACCTASSCAT":"","PO_PRICE":"1","MOVE_TYPE":"101","MVT_IND":"B",
"JOURNAL_ENTRY_NO":"2"}}
"""

J45_CN_DELTA = """
{
    "J45": {
        "COUNTRY": "CN",
        "COMPANY_CODE": "1310",
        "CURRENCY": "CNY",
        "PLANT": "1310",
        "PURCH_ORG": "1310",
        "S_LOC": "131A",
        "SUPPLIER": "0013300001",
        "SUPPLIER_NAME": "Domestic Supplier CN 1",
        "TAX_CODE": "J0"
    }
}
"""

logger = logging.getLogger(__name__)


class Error(Exception):
    """Exceptions raised in this module are of this class."""


def set_up_root_logging(level):
    lh = logging.StreamHandler()
    lh.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)16s - %(levelname)8s - %(message)s'))
    log = logging.getLogger()  # root logger
    log.addHandler(lh)
    log.setLevel(level)


def strip_lead_sep(p):
    if p[0] in '/\\':
        p = p[1:]
    return p


def canonicalpath(p):
    """Returns unique representation of file path."""
    return os.path.normcase(os.path.abspath(p))


class DirPerTest(unittest.TestCase):
    """Abstract class for tests with one temp dir per test."""

    @classmethod
    def setUpClass(cls):
        logger.debug('in DirPerTest.setUpClass(cls).')
        cls._outdir = canonicalpath(
            os.path.join(_OUT_DIR, _OUT_DIR_PREFIX + cls.__name__))
        os.makedirs(cls._outdir, exist_ok=True)
        logger.info('Made temp output dir: "%s".', cls._outdir)

    @classmethod
    def tearDownClass(cls):
        logger.info('Removing temp output dir: "%s".', cls._outdir)
        shutil.rmtree(cls._outdir)

    def setUp(self):
        self._root_dir = None
        self._testname = None

    def _assert_json_equal(self, act_file, exp_file):
        logger.debug('Read actual %s.', act_file)
        with open(act_file, 'r', encoding='utf-8') as fp:
            actual = jcs.canonicalize(json.load(fp))
        logger.debug('act=%s.', actual)
        logger.debug('Read exp %s.', exp_file)
        with open(exp_file, 'r', encoding='utf-8') as fp:
            exp = jcs.canonicalize(json.load(fp))
        logger.debug('exp=%s.', exp)
        self.assertEqual(actual, exp, f"In actual file {act_file}.")

    def _testname_root_dir(self, testname):
        self._testname = testname
        self._root_dir = canonicalpath(
            os.path.join(self._outdir, self._testname))
        os.makedirs(self._root_dir, exist_ok=True)


class JsonArrayIn(DirPerTest):
    """Abstract class for tests that read json arrays of file names."""

    _td = {}

    def setUp(self):
        super().setUp()
        self._mergelist_dir = None

    def _resolve(self, p, base):
        p = strip_lead_sep(p)
        result = canonicalpath(os.path.join(base, p))
        if not result.startswith(self._root_dir):
            self.fail(f'{TEST_DATA_ERROR_MSG} {self._testname} File or dir '
                      f'to create "{p}" resolves above test root '
                      f'"{self._root_dir}".')
        return result

    def _checkDir(self, k, the_dir, dl, td):
        if 'd' not in td:
            self.fail(f'{TEST_DATA_ERROR_MSG} {self._testname} '
                      f'{k} without d.')
        err_msg = f'{k} must be a dir from the d dir list.'
        for d in dl:
            cp = os.path.commonpath([the_dir, d])
            if not os.path.samefile(cp, self._root_dir):
                break
        else:
            self.fail(f'{TEST_DATA_ERROR_MSG} {self._testname} {err_msg}')

    def _do_single_dirs(self, td, dl):
        if 'D' in td:
            self._mergelist_dir = self._resolve(td['D'], self._root_dir)
            self._checkDir('D', self._mergelist_dir, dl, td)
        else:
            self._mergelist_dir = self._root_dir

    def _dir_stuff(self):
        td = self._td[self._testname]
        self._root_dir = canonicalpath(
            os.path.join(self._outdir, self._testname))
        os.makedirs(self._root_dir, exist_ok=True)
        dl = []
        if 'd' in td:
            for d in td['d']:
                dl.append(self._resolve(d, self._root_dir))
                os.makedirs(dl[-1], exist_ok=True)
        self._do_single_dirs(td, dl)

    def _resolve_infile_paths(self, infiles):
        result = []
        for p in infiles:
            bd = self._mergelist_dir if strip_lead_sep(
                p) == p else self._root_dir
            result.append(self._resolve(p, bd))
        return result

    def _set_up_Ddni(self, testname):
        """Make temporaory dirs and write files for test.
        
        A temporary dir for the test is created and its path stored in
        self._root_dir. Stores testname in self._testname.
        
        Sets up test according to dictionary in self._td[testname], 
        based on key values. All keys are optional, but the length 
        of the list for n and i keys must be the same.

        key d : list of dir paths to create
        key D : single path of a dir to create
        key n : list of files paths to create
        key i : list of content as strings of files to create
        
        d & D dir paths are resolved relative to self._root_dir

        The lengths of lists n and i must be the same. 
        
        The n paths are resolved relative to D dir if present, otherwise
            relative to self._root_dir.
        
        Args:
            testname: Name of test being set up. Used as index to 
                cls._td
        
        Returns: 
            list of resolved n paths, in same order as n. 
        """
        logger.debug('Test %s.  _set_up_Ddni.', testname)
        self._testname_root_dir(testname)
        self._dir_stuff()
        td = self._td[self._testname]
        fnames = self._resolve_infile_paths(td['n'])
        jsons = td['i']
        if len(fnames) != len(jsons):
            self.fail(f'{TEST_DATA_ERROR_MSG} {self._testname} '
                      f'The i list of json content (length {len(fnames)}) '
                      'must be the same length as '
                      f'the n list of json file names (length {len(jsons)}).')
        for content, fname in zip(jsons, fnames):
            if 'd' not in td:
                os.makedirs(os.path.split(fname)[0], exist_ok=True)
            with open(fname, 'w', encoding='utf-8') as fp:
                fp.write(content)
        return fnames

    @staticmethod
    def _write_mergelist(outpath, fnames):
        with open(outpath, 'w', encoding='utf-8') as fp:
            fp.write('[')
            sep = ''
            for p in fnames:
                if os.path.isabs(p):
                    p = canonicalpath(p)
                # Any windows path '\' must be '\\' in json string.
                p = p.replace('\\', '\\\\')
                fp.write(f'{sep}"{p}"')
                sep = ',\n '
            fp.write(']\n')

    def _set_up_Ddni_mergelist(self, testname, fname_mergelist=None):
        """Same as _set_up_Ddni, but adds a mergelist for all n files.
        
        Returns path to mergelist (json array file).
        """
        logger.debug('Test %s.  _set_up_Ddni_mergelist().', testname)
        fnames = self._set_up_Ddni(testname)
        if not fname_mergelist:
            fname_mergelist = 'in.array_of_files.json'
        json_array_file = os.path.join(self._mergelist_dir, fname_mergelist)
        self._write_mergelist(json_array_file, fnames)
        return json_array_file


class TestMergelistBase(JsonArrayIn):

    # First n is mergefile.
    # key o: expected result
    def _doit(self, symbol_args_tuple=(act.sub.M4S_FNAME,)):
        infiles = self._set_up_Ddni(inspect.stack()[1].function[len('test_'):])
        mergelist = infiles[0]
        td = self._td[self._testname]
        if 'o' in td:
            fn_act = act.mergejson.merge(
                mergelist, os.path.join(self._root_dir, 'actual.json'),
                *symbol_args_tuple)
            fn_exp = os.path.join(self._root_dir, 'expected.json')
            with open(fn_exp, 'w', encoding='utf-8') as fp:
                fp.write(td['o'])
            self._assert_json_equal(fn_act, fn_exp)
        else:
            with self.assertRaisesRegex(td['x'][0], td['x'][1]):
                act.mergejson.merge(mergelist, 'dummy', act.sub.M4S_ERROR)


class TestMergeallBase(JsonArrayIn):

    _IN = 'in'  # name of input base dir under self._root_dir

    def setUp(self):
        super().setUp()
        self._input_base_dir = None

    def _resolve_infile_paths(self, infiles):
        """Override to add _IN to all infiles paths."""
        result = []
        if not self._input_base_dir:
            self._input_base_dir = canonicalpath(
                os.path.join(self._root_dir, self._IN))
        for p in infiles:
            result.append(self._resolve(p, self._input_base_dir))
            if not result[-1].startswith(self._input_base_dir):
                raise Error(
                    f'n key item {p} resolves above {self._input_base_dir}.')
        return result

    def _get_canonical_expected_file_paths(self, out_base_dir):
        """Get file paths for TD 'N' key.
        
        Args:
            out_base_dir: File paths returned are resolved relative to this 
                directory
        
        Returns:
            Expected result 'N' key file paths resolved relative to 
            out_base_dir.
        
        Raises: 
            Error if N path is not a relative path or if it does not resolve 
            to a path at or under out_base_dir.
        """
        out_base_dir = canonicalpath(out_base_dir)
        result = []
        for p in self._td[self._testname].get('N'):
            if os.path.isabs(p):
                raise Error(f'N key value {p} must be a relative path.')
            fcp = canonicalpath(os.path.join(out_base_dir, p))
            if not fcp.startswith(out_base_dir):
                raise Error(f'N key value {p} not in or under {out_base_dir}.')
            result.append(fcp)
        return result

    def _check_outdir(self):
        outdir = self._td[self._testname].get('O')
        if outdir:
            if os.path.isabs(outdir):
                raise Error(f'{self._testname} O is absolute, not '
                            f'relative. O key value = "{outdir}".')
            outdir = canonicalpath(os.path.join(self._root_dir, outdir))
            o4fstr = self._td[self._testname].get("O")
            if not outdir.startswith(self._root_dir):
                raise Error(f'{self._testname} O key path value {o4fstr} '
                            f'resolves above "{self._root_dir}".')
            if outdir.startswith(self._input_base_dir):
                raise Error(f'{self._testname} O key path value {o4fstr} under '
                            f'input dir "{self._input_base_dir}".')
        return outdir

    _CALL_STACK_FNAME_INDEX = 2

    def _setup(self):
        # Create input directories and files.
        self._set_up_Ddni(inspect.stack()[
            self._CALL_STACK_FNAME_INDEX].function[len('test_'):])
        # Resolve and validate optional O key output dir.
        outdir = self._check_outdir()
        # Call mergeall.py
        arg_v = [self._input_base_dir, '-l', 'warning', '-c']
        if outdir:
            arg_v.append('--outdir')
            arg_v.append(outdir)
        if self._testname.endswith('_d4s'):
            arg_v.append('--mode4symbols')
            arg_v.append('DIR')
        return (outdir, arg_v)

    def _validate(self, arg_outdir, actual_outdir):
        # Validate location of output if passed as option in argv.
        if arg_outdir:
            self.assertEqual(arg_outdir, canonicalpath(actual_outdir))
        # Validate existence of resolved expected file paths.
        expected_files = self._get_canonical_expected_file_paths(actual_outdir)
        for p in expected_files:
            self.assertTrue(os.path.exists(p),
                            f'Expected output file does not exist: {p}.')
        # Validate contents of expected files.
        expected_contents = self._td[self._testname].get('I')
        if len(expected_files) != len(expected_contents):
            raise Error(f'Test {self._testname} definition error. '
                        'len(expected_files) != len(expected_contents).')
        for p, v, i in zip(expected_files, expected_contents,
                           range(len(expected_files))):
            exp_json = os.path.join(self._root_dir, f'expected.{i}.json')
            with open(exp_json, 'w', encoding='utf-8') as fp:
                fp.write(v)
            self._assert_json_equal(p, exp_json)
        # Validate no unexpected files or dirs.
        for dirpath, dirnames, filenames in os.walk(actual_outdir):
            if not os.path.samefile(actual_outdir, dirpath):
                # Top output directory may be empty when no files generated
                # due to exclusion list.
                self.assertTrue(dirnames or filenames,
                                f'Unexpeced output directory "{dirpath}".')
            for f in filenames:
                p = canonicalpath(os.path.join(dirpath, f))
                self.assertTrue(p in expected_files,
                                f'Unexpected output file "{p}".')

    def _doit(self):

        outdir, arg_v = self._setup()
        a_actual_outdir = []
        act.mergeall.main(arg_v, a_actual_outdir)
        self._validate(outdir, a_actual_outdir[0])
