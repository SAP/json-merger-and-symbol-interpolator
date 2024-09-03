"""Merge each mergelist file under a directory, recursively."""
import logging
import os
import os.path
import argparse
import sys
# own imports
import act.sub
import act.mergejson

# Name of json file used to override mode4symbols in dir sub-tree.
_MODE4SYMBOLS_FNAME = os.path.normcase('mergeall.args.json')
# Name of json file used to exclude files just that directory.
_EXCLUDE_FNAME = os.path.normcase('mergeall.exclude.json')
# Text with _A prefix for command line Args
_A_DESCRIPTION = (
    f'Apply mergejson.py to each *{act.sub.MERGELIST_EXT} and '
    f'{act.sub.MERGELIST_EXT[1:]} file under a directory '
    '(to know what mergejson.py does, read its command line help).'
    '\n\n'
    'Specific file names in a directory are ignored if listed in a per-directory '
    f'exclusion list file named {_EXCLUDE_FNAME}.'
    '\n\n'
    'The command line arguments for symbol processing can be overridden for a '
    'directory D and all it\'s sub-directories (until overridden again in a '
    f'sub-directory) with values from a file in D named {_MODE4SYMBOLS_FNAME}. '
    'For example, such a file might contain {"--mode4symbols":"NAMED", '
    '"--symset":"INDIA"} or  {"--mode4symbols":"ERROR"}. The short single dash '
    'forms of the command line argument are not recognized here.')
_A_INDIR_N = 'indir'
_A_INDIR_H = ('The directory and all its sub-directories under which to merge '
              'matching files.')
_A_OUTDIR_N = '--outdir'
_A_OUTDIR_D = f"<indir's dir>/{act.sub.OUT_PREFIX}<indir's name>"
_A_OUTDIR_H = f"""Output directory under which one *{act.sub.OUT_MERGED_EXT} target
file is written for each *{act.sub.MERGELIST_EXT} source file found.
The target file is written in a sub-directory mirroring the source file's
location. Default is {_A_OUTDIR_D}. BEWARE: If <outdir> exists, all its 
contents are deleted and then regenerated. 
"""
# Indices for tuples yielded by os.walk()
_OW_DIRPATH = 0
_OW_DIRNAMES = 1
_OW_FILENAMES = 2

logger = logging.getLogger(__name__)


class Error(act.sub.Error):
    """Exceptions raised in this module are of this class."""


def _parse_args(argv):

    def isdir(arg, argname, p):
        if not os.path.isdir(arg):
            p.error(f'Argument {argname} invalid. Not a directory: "{arg}".')
        return arg

    def if_exists_isdir(arg, argname, p):
        if os.path.exists(arg):
            return isdir(arg, argname, p)
        return arg

    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=_A_DESCRIPTION)
    p.add_argument(_A_INDIR_N,
                   help=_A_INDIR_H,
                   type=lambda x: isdir(x, _A_INDIR_N, p))
    p.add_argument(_A_OUTDIR_N[1:3],
                   _A_OUTDIR_N,
                   help=_A_OUTDIR_H,
                   default=_A_OUTDIR_D,
                   type=lambda x: if_exists_isdir(x, _A_INDIR_N, p))
    act.sub.add_symset_args(p)
    act.sub.add_log_arg(p)
    pa = p.parse_args(argv)
    err_msg = act.sub.check_symset_options(pa.mode4symbols, pa.symset)
    if err_msg:
        p.error(err_msg)
    if pa.outdir == _A_OUTDIR_D:
        h, t = os.path.split(pa.indir)
        pa.outdir = os.path.join(h, act.sub.OUT_PREFIX + t)
    return pa


def _make_mirror_subdirs_obj(source_dir, target_dir):
    in_files = []
    for t in os.walk(source_dir):
        for f in sorted(t[_OW_FILENAMES]):
            cp = act.sub.canonical(os.path.join(t[_OW_DIRPATH], f))
            if act.sub.is_mergelist(cp):
                in_files.append(cp)
    return act.sub.MirrorSubdirs(target_dir, in_files, source_dir)


def _merge_mergelist(msd, in_path, mode4symbols, symset):
    """Returns None or act.sub.Error instance iff merge failed."""
    result = None
    out_dir, in_fname = os.path.split(msd.gen_file_path(in_path))
    out_fname = act.sub.merged_file_name(in_fname)
    out_path = act.sub.canonical(os.path.join(out_dir, out_fname))
    try:
        act.mergejson.merge(in_path, out_path, mode4symbols, symset)
    except act.sub.Error as ex:
        logger.exception(
            'Exception merging %s. mode4symbols=%s. symset=%s. outfile=%s.',
            in_path, mode4symbols, symset, out_path)
        result = ex
    return result


def _new_symbol_args(dir_path, mode_args_4_dir):
    result = None
    in_path = os.path.join(dir_path, _MODE4SYMBOLS_FNAME)
    try:
        mode_args_4_dir.read(in_path)
    except act.sub.Error as ex:
        logger.exception('Exception reading new symbol mode arguments from %s.',
                         in_path)
        result = ex
    return result


class _ModeArgs4Dir:

    def __init__(self, root_dirpath, mode4symbols, symset):
        self._d2ma = {}
        self._can_overwrite_once = None
        self.add(root_dirpath, mode4symbols, symset)
        # pylint: disable=consider-iterating-dictionary
        for k in self._d2ma.keys():  # there is only one
            self._can_overwrite_once = k

    def add(self, dirpath, mode4symbols, symset):
        assert os.path.isdir(dirpath), f'Not a directory: {dirpath}.'
        k = act.sub.canonical(dirpath) + os.path.normcase('/')
        if k == self._can_overwrite_once:
            self._can_overwrite_once = None
        else:
            assert k not in self._d2ma, f'Key overwrite. {k=} {self._d2ma=}.'
        self._d2ma[k] = (mode4symbols, symset)

    def get(self, dirpath):
        """Returns (mode4symbols, symset) tuple for files in dirpath."""
        longest_matching_key = ''
        p = act.sub.canonical(dirpath) + os.path.normcase('/')
        # pylint: disable=consider-iterating-dictionary
        for k in self._d2ma.keys():
            if p.startswith(k):
                if len(k) > len(longest_matching_key):
                    longest_matching_key = k
        assert longest_matching_key in self._d2ma, f'{longest_matching_key=} {p=} {self._d2ma=}'
        return self._d2ma[longest_matching_key]

    def read(self, filepath):
        cfp = act.sub.canonical(filepath)
        dirpath, filename = os.path.split(cfp)
        j = act.sub.read_json(cfp)
        if not isinstance(j, dict):
            raise Error(f'File {filename} is not a JSON object. '
                        f'Directory: {dirpath}.')
        if act.sub.A_MODE4SYM_N not in j:
            raise Error(f'File {filename} JSON object missing key: '
                        f'{act.sub.A_MODE4SYM_N}. '
                        f'Directory: {dirpath}.')
        mode4symbols = j[act.sub.A_MODE4SYM_N]
        symset = j.get(act.sub.A_SYMSET_N)
        errmsg = act.sub.check_symset_options(mode4symbols, symset)
        if errmsg:
            raise Error(f'File {filename} JSON object invalid options.'
                        f'{errmsg} '
                        f'Directory: {dirpath}.')
        strange_keys = []
        for k in j.keys():
            if k not in [act.sub.A_MODE4SYM_N, act.sub.A_SYMSET_N]:
                strange_keys.append(k)
        if strange_keys:
            raise Error(f'File {filename} JSON object strange keys: '
                        f'{strange_keys}. '
                        f'Directory: {dirpath}.')
        self.add(dirpath, mode4symbols, symset)
        logger.info(
            'Options from %s apply in and under this directory. '
            'Options: %s. Directory: %s.', filename, j, dirpath)


def _remove_excluded_files_from_list(dirpath, filenames):
    result = None
    p = os.path.join(dirpath, _EXCLUDE_FNAME)
    assert os.path.exists(p), p
    try:
        xnames = [os.path.normcase(f) for f in act.sub.read_json(p)]
        for x in xnames:
            if x not in filenames:
                raise Error(f'File name {x} in {_EXCLUDE_FNAME}. '
                            f'No such file in directory {dirpath}. ')
            if not act.sub.is_mergelist(x):
                raise Error(f'File name {x} in {_EXCLUDE_FNAME}. '
                            'Name does not match merge list name pattern. '
                            f'Directory {dirpath}.')
            if os.path.split(x)[0]:
                raise Error(f'File name {x} in {_EXCLUDE_FNAME}. '
                            'Name can not have path components. '
                            f'Directory {dirpath}.')
            filenames.remove(x)
            logger.info('Skip file %s because it is in %s of directory %s.', x,
                        _EXCLUDE_FNAME, dirpath)
    except act.sub.Error as ex:
        logger.exception('Exclude list error.')
        result = ex
    return result


def main(argv, a_actual_out_dir=None):
    args = _parse_args(argv)
    act.sub.set_up_logging(act.sub.LOGGING_LEVEL_NAME2VALUE[args.log_level],
                           args.console)
    logger.debug('Args: %s', args)
    act.sub.create_or_empty_dir(args.outdir)
    # Output dir is returned in list (a way to pass a string by reference).
    if a_actual_out_dir is not None:
        a_actual_out_dir.append(args.outdir)
    msd = _make_mirror_subdirs_obj(args.indir, args.outdir)
    mode_args_4_dir = _ModeArgs4Dir(args.indir, args.mode4symbols, args.symset)
    # Build in_file list by walking top down to guarantee that files in
    # parent directories are processed before files in child directories.
    # We depend on this for a feature. We overwrite the per symset generated
    # merged files with a file generated from a mergelist in a source symset
    # source sub-directory. Note that glob.glob() does not guarantee this.
    exceptions = []
    for t in os.walk(args.indir):
        # Force deterministic order of dir traversal with in place sort.
        t[_OW_DIRNAMES].sort()
        # Ditto for file names, but copied as doc doesn't say in place is safe.
        filenames = [os.path.normcase(f) for f in sorted(t[_OW_FILENAMES])]
        # Are there files to exclude in this directory?
        if _EXCLUDE_FNAME in filenames:
            ex = _remove_excluded_files_from_list(t[_OW_DIRPATH], filenames)
            if ex:
                exceptions.append(ex)
        # Are there new symbol mode args defined starting from this directory?
        if _MODE4SYMBOLS_FNAME in filenames:
            ex = _new_symbol_args(t[_OW_DIRPATH], mode_args_4_dir)
            if ex:
                exceptions.append(ex)
        # Get symbol mode for this directory.
        mode4symbols, symset = mode_args_4_dir.get(t[_OW_DIRPATH])
        # Merge each merge file in current directory.
        for in_fname in filenames:
            if act.sub.is_mergelist(in_fname):
                in_path = act.sub.canonical(
                    os.path.join(t[_OW_DIRPATH], in_fname))
                ex = _merge_mergelist(msd, in_path, mode4symbols, symset)
                if ex:
                    exceptions.append(ex)
            else:
                logger.debug('Skip file "%s" in "%s".', in_fname,
                             t[_OW_DIRPATH])
    return exceptions


if __name__ == '__main__':
    main_returned = main(sys.argv[1:])
    rc = len(main_returned)
    if rc != 0:
        print('!' * 80)
        print(f'!!! Program: {sys.argv[0]}.')
        print(f'!!! {rc} EXCEPTIONS merging parameters. See log file.')
        print('!' * 80)
    sys.exit(rc)
