"""Stuff used in more than one module.
"""
import os.path
import logging
import json
import errno
import shutil
import uuid
import sys
import copy

# == PUBLIC CONSTANTS =========================================================

OUT_PREFIX = os.path.normcase('out.')
JSON_EXT = os.path.normcase('.json')
MERGELIST_EXT = os.path.normcase(f'.mergelist{JSON_EXT}')
OUT_MERGED_EXT = os.path.normcase(f'.merged{JSON_EXT}')
OUT_MERGED_DEFAULT_PREFIX = os.path.normcase(f'{OUT_PREFIX}merged.')

LOG_FILE = f'./{OUT_PREFIX}python.log.txt'
LOGGING_LEVEL_NAME2VALUE = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARN,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
LOGGING_LEVEL_VALUE2NAME = {v: k for k, v in LOGGING_LEVEL_NAME2VALUE.items()}

A_SYMSET_N = '--symset'
A_MODE4SYM_N = '--mode4symbols'
M4S_DIR = 'DIR'
M4S_ERROR = 'ERROR'
M4S_FNAME = 'FNAME'
M4S_GLOBAL = 'GLOBAL'
M4S_IGNORE = 'IGNORE'
M4S_NAMED = 'NAMED'

# -- PRIVATE CONSTANTS --------------------------------------------------------
_SYMBOLS_EXT = os.path.normcase(f'.symbols{JSON_EXT}')
_LOGGING_FORMAT = '%(asctime)s - %(name)16s - %(levelname)8s - %(message)s'
_A_LOG_LEVEL_N = '--log_level'
_A_LOG_LEVEL_D = 'info'
_A_CONSOLE_N = '--console'
_A_CONSOLE_H = 'Also write log messages to console.'
_A_LOG_LEVEL_H = ('logging level. Log messages are appended to '
                  f'"{LOG_FILE}". Default is "{_A_LOG_LEVEL_D}".')

_M4S_CHOICES = [
    M4S_DIR, M4S_ERROR, M4S_FNAME, M4S_GLOBAL, M4S_IGNORE, M4S_NAMED
]
_A_SYMSET_H = ('Symbol set name for symbol interpolation. Error unless '
               f'{A_MODE4SYM_N} is {M4S_NAMED}.')
_A_MODE4SYM_D = M4S_FNAME
_A_MODE4SYM_H = f'''
How to generate files when merge list refers to a symbol definition file.

For all choices this option is ignored if merge list does not refer to a
symbol definition file.

Choice DIR : generate one file per symbol set in the symbol definition file.
The file is generated with OUTFILE's file name, in a sub-diretory of OUTFILE's
directory, the name of which is the symbol set name. In addition, generate
OUTFILE with global symbols only (a deprecated feature to support backwards
compatibility).

Choice ERROR : raise an error if merge list refers to a symbol definition file.

Choice {M4S_FNAME} : generate OUTFILE with the symbol set determined from 
merge list's file name as follows: [*.]<symbol_set_name>{MERGELIST_EXT} (note: 
<symbol_set_name> may not contain dots).

Choice GLOBAL : generate OUTFILE with global symbols only.

Choice IGNORE : generate OUTFILE with no symbol interpolation.

Choice {M4S_NAMED} : generate OUTFILE with symbol set specified by the 
{A_SYMSET_N} option.

Default is {_A_MODE4SYM_D}.
'''

# == EVERYTHING ELSE ==========================================================

logger = logging.getLogger(__name__)


class Error(Exception):
    """Exceptions raised in this package are of this class."""


class JsonArraysNotSupported(Error):
    pass


def check_types(d, loc_stk, allow_nested_arrays=True):
    """Raise errors for unsupported json types in loaded json dict d."""
    if isinstance(d, list):
        raise JsonArraysNotSupported(f'Where: {loc_stk}.')
    for k in sorted(d.keys()):
        loc_stk.append(k)
        if isinstance(d[k], dict):
            check_types(d[k], loc_stk, allow_nested_arrays)
        elif isinstance(d[k], list) and not allow_nested_arrays:
            raise JsonArraysNotSupported(f'Where: {loc_stk}.')
        elif not (d[k] is None or isinstance(d[k],
                                             (bool, float, int, str, list))):
            t = type(d[k])
            raise Error(f'JSON decoder produced strange type "{t}". '
                        f'Where: {loc_stk}.')
        loc_stk.pop()


def write_as_json(o, fname):
    logger.info('Write json to: %s.', fname)
    logger.debug('About to serialize as json python object: %s.', o)
    with open(fname, 'w', encoding='utf-8') as fp:
        try:
            json.dump(o, fp, indent=4)
        except (TypeError, ValueError, RecursionError) as ex:
            ex.add_note(fname)
            raise Error(f'Exception writing json to {fname}.') from ex


_read_json_cache = {}


def read_json(fname, level=logging.INFO):
    cp = canonical(fname)
    if cp not in _read_json_cache:
        logger.log(level, 'Read json from: %s.', fname)
        try:
            with open(fname, 'r', encoding='utf-8') as fp:
                o = json.load(fp)
        except json.decoder.JSONDecodeError as ex:
            ex.add_note(fname)
            raise Error(f'Exception reading json from {fname}.') from ex
        _read_json_cache[cp] = o
    else:
        logger.debug('Read json cache hit : %s.', cp)
    return copy.deepcopy(_read_json_cache[cp])


def set_up_logging(level, also_log_to_console=True):
    _lf = logging.Formatter(_LOGGING_FORMAT)
    _lh = logging.FileHandler(LOG_FILE, 'a', encoding='utf8')
    _lh.setFormatter(_lf)
    logging.getLogger().addHandler(_lh)
    if also_log_to_console:
        _lh = logging.StreamHandler()
        _lh.setFormatter(_lf)
        logging.getLogger().addHandler(_lh)
    logging.getLogger().setLevel(level)
    print('Log at', LOGGING_LEVEL_VALUE2NAME[level], 'severity to file',
          os.path.abspath(LOG_FILE))
    logger.info('Program name: %s.', sys.argv[0])
    logger.info('Command line arguments: %s.', sys.argv[1:])
    logger.info('Current directory: %s.', os.getcwd())


def _is_array_of_filepaths(file_path):
    o = read_json(file_path)
    if not isinstance(o, list):
        return False
    basedir = os.path.split(os.path.abspath(file_path))[0]
    for p in o:
        if not isinstance(p, str):
            return False
        if not os.path.isabs(p):
            p = os.path.join(basedir, p)
        if not os.path.isfile(p):
            return False
    return True


class MergeListCycle(Error):
    """When merge lists referring to other merge lists make a cycle."""


def read_and_resolve_path_array(source_path):
    """Reads JSON array of file paths.

    Resolves relative paths relative to dir containing source_path.

    If array item is itself a file containing a JSON array of file paths,
    expand in place, recursively.

    Returns: list of canonical paths.

    Raises:
        MergeListCycle
    """
    return _read_and_resolve_path_array(source_path, [])


def _read_and_resolve_path_array(source_path, merge_list_stack):
    source_path = canonical(source_path)
    if source_path in merge_list_stack:
        raise MergeListCycle('Merge list in merge list makes loop: '
                             f'"{source_path}". {merge_list_stack=}')
    merge_list_stack.append(source_path)
    source_path_list_raw = read_json(source_path)
    basedir = os.path.split(source_path)[0]
    result = []
    for p in source_path_list_raw:
        if not os.path.isabs(p):
            logger.debug('Resolve %s relative to %s.', p, basedir)
            p = os.path.join(basedir, p)
        if not os.path.isfile(p):
            raise Error('Invalid item in JSON array of file paths: '
                        f'"{p}" in {source_path} is not a file.')
        if _is_array_of_filepaths(p):
            result = result + _read_and_resolve_path_array(p, merge_list_stack)
        else:
            result.append(canonical(p))
    merge_list_stack.pop()
    return result


def rok(arg, argname, argparser):
    """For arg parser to check file is readable."""
    if not os.path.exists(arg):
        argparser.error(
            f'Argument {argname} invalid. File does not exist: "{arg}".')
    if not os.path.isfile(arg):
        argparser.error(f'Argument {argname} invalid. Not a file: "{arg}".')
    if not os.access(arg, os.R_OK):
        argparser.error(f'Argument {argname} invalid. '
                        f'No read access: "{arg}".')
    return arg


def dwok(arg, argname, argparser):
    """For arg parser to check dir is writeable."""
    if os.path.exists(arg):
        if not os.path.isdir(arg):
            argparser.error(
                f'Argument {argname} invalid. Not a directory: "{arg}".')
        if not os.access(arg, os.W_OK):
            argparser.error(f'Argument {argname} invalid. No access: "{arg}".')
    return arg


def canonical(path):
    """Returns unique representation of file path."""
    return os.path.normcase(os.path.abspath(path))


def create_dir_if_inexistant(dir_path):
    """Create directory if it does not already exist."""
    try:
        os.makedirs(dir_path)
        logging.debug('Create dirs "%s".', dir_path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
            pass
        else:
            raise


def create_or_empty_dir(dir_path):
    """Ensures that dir_path is an existing empty directory."""
    if os.path.exists(dir_path):
        # Rename to work around WindowsError: [Error 5] Access is denied: ...
        # when creatng the dir after deletion.
        renamed = os.path.join(os.path.split(dir_path)[0], str(uuid.uuid4()))
        logging.debug('Rename "%s" to "%s".', dir_path, renamed)
        os.rename(dir_path, renamed)
        logging.debug('Remove "%s".', renamed)
        shutil.rmtree(renamed)
    create_dir_if_inexistant(dir_path)


def add_log_arg(argparser):
    argparser.add_argument(_A_LOG_LEVEL_N[1:3],
                           _A_LOG_LEVEL_N,
                           help=_A_LOG_LEVEL_H,
                           default=_A_LOG_LEVEL_D,
                           choices=sorted(LOGGING_LEVEL_NAME2VALUE.keys()))
    argparser.add_argument(_A_CONSOLE_N[1:3],
                           _A_CONSOLE_N,
                           help=_A_CONSOLE_H,
                           action='store_true')


def add_symset_args(arg_parser):
    arg_parser.add_argument(A_MODE4SYM_N[1:3],
                            A_MODE4SYM_N,
                            help=_A_MODE4SYM_H,
                            default=_A_MODE4SYM_D,
                            choices=_M4S_CHOICES)
    arg_parser.add_argument(A_SYMSET_N[1:3], A_SYMSET_N, help=_A_SYMSET_H)


def check_symset_options(mode4symbols, symset_name):
    """Returns error text or None if options are valid."""
    result = None
    if mode4symbols not in _M4S_CHOICES:
        result = (f'Invalid {A_MODE4SYM_N} option value: "{mode4symbols}". '
                  f'Possible values are: {_M4S_CHOICES}.')
    elif symset_name and mode4symbols != M4S_NAMED:
        result = (
            f'The {A_SYMSET_N} option is prohibited unless {A_MODE4SYM_N} '
            f'option is {M4S_NAMED}.')
    elif mode4symbols == M4S_NAMED and symset_name is None:
        result = (
            f'The {A_SYMSET_N} option is mandatory if {A_MODE4SYM_N} option '
            f'is {M4S_NAMED}.')
    return result


class MirrorSubdirs():
    """All paths returned are canonical.
    
    Mirroring of source files starts after longest common path 
    element of the source files is removed, unless in_dir_root
    is provided, in which case mirroring starts after in_dir_root
    is removed.
    """

    def __init__(self,
                 out_dir_root,
                 a_source_files_canonical,
                 in_dir_root=None):

        if not a_source_files_canonical:
            raise Error(f'No files to mirror.'
                        f'\n\t{in_dir_root=}.'
                        f'\n\t{a_source_files_canonical=}.'
                        f'\n\t{out_dir_root=}.')
        if len(a_source_files_canonical) == 1:
            self.__source_common_prefix = os.path.split(
                a_source_files_canonical[0])[0]
        else:
            self.__source_common_prefix = os.path.commonpath(
                a_source_files_canonical)
        if in_dir_root:
            in_dir_root = canonical(in_dir_root)
            if not self.__source_common_prefix.startswith(in_dir_root):
                raise Error(
                    f'All source files must be under {in_dir_root}, '
                    f'but common prefix is {self.__source_common_prefix}.')
            self.__source_common_prefix = in_dir_root
        sep = os.path.normcase('/')
        if self.__source_common_prefix[-1] != sep:
            self.__source_common_prefix = self.__source_common_prefix + sep
        logger.debug('Common prefix="%s".', self.__source_common_prefix)
        self.__out_dir = canonical(out_dir_root)

    def out_dir(self):
        return self.__out_dir

    def rel_path(self, source_path):
        """Returns source_path with common prefix removed."""
        cpath = canonical(source_path)
        if not cpath.startswith(self.__source_common_prefix):
            raise Error(
                'To mirror subdirs, path must start with '
                f'"{self.__source_common_prefix}". Canonical path="{cpath}".')
        result = cpath[len(self.__source_common_prefix):]
        return result

    def gen_file_path(self, source_path):
        """Returns mirrored target path corresponding to source_path."""
        rel_path = self.rel_path(source_path)
        path = os.path.join(self.__out_dir, rel_path)
        dir_part, file_part = os.path.split(path)
        create_dir_if_inexistant(dir_part)
        return os.path.join(dir_part, file_part)


def _is_that_file(filepath, end):
    if os.path.isdir(filepath):
        raise Error(f'Filepath argument is a directory. {filepath=}. {end=}.')
    result = False
    cp = os.path.normcase(filepath)
    fname = os.path.split(cp)[1]
    if fname.endswith(end):
        result = True
    elif end[0] == '.' and end.count('.') > 1 and fname == end[1:]:
        result = True
    return result


def is_mergelist(filepath):
    return _is_that_file(filepath, MERGELIST_EXT)


def is_symbol_def_file(filepath):
    return _is_that_file(filepath, _SYMBOLS_EXT)


def merged_file_name(mergelist_file_name):
    """Returns output file name (name only) for mergelist_file_name."""
    fn = os.path.normcase(os.path.split(mergelist_file_name)[1])
    if not is_mergelist(fn):
        raise Error(f'Invalid mergelist file name "{mergelist_file_name}".')
    if fn == MERGELIST_EXT[1:]:
        return OUT_MERGED_EXT[1:]
    return fn[:-len(MERGELIST_EXT)] + OUT_MERGED_EXT


def _main():
    set_up_logging(logging.DEBUG)
    try:
        o = {
            1: 'one',
            '2': 'two',
            Error('x'): 'The json library can not do object keys.'
        }
        write_as_json(o, r'c:\my\junk\out.json')
    except Error as x:
        logger.exception('=== exception x %s.', x)
        logger.error('=== error x %s.', x)
        print("==============================================")
        # try:
        #     raise Error('hello')
        # except Exception:
        #     pass
        raise


if __name__ == '__main__':
    _main()
