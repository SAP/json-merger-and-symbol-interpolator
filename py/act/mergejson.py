"""Merge and replace symbols in json files.
"""

import logging
import os.path
import argparse
# own imports
import act.sub
import act.symbols

# Text with _A prefix for command line Args
_A_DESCRIPTION = """Merge json files and replace symbols.

Example (notice "last name wins"): Merging {"X":{"a":1, "b":2}} with {"X":{"b":"two"},"a":42} gives {"X":{"a":1,"b":"two"},"a":42}.

Objects can not be merged with primitives.

Array are treated like primitives during merge. Values that are arrays replace or are replaced by other values.
"""
_A_INFILE_N = 'infile'
_A_INFILE_H = """The merge list, which is a json file containing an array of
strings, each the path to a json file to merge, and optionally, one path to a
symbol definition file for symbol interpolation in json values.

If a json file to merge is itself an array of valid file paths, it is replaced
with its contents (similar to C language #include), and this applies
recursively.

The file paths can be absolute or relative. If relative, they are resolved
relative to the directory containing the json array of references to files.
Example: ["a.json","/x/b.json","../y/c.json","symbols.json"].
"""
_A_OUTFILE_N = '--outfile'
_A_OUTFILE_D = f"<infile's dir>/{act.sub.OUT_MERGED_DEFAULT_PREFIX}<infile's name>"
_A_OUTFILE_H = f'Merged json file to (over)write. Default is {_A_OUTFILE_D}.'

logger = logging.getLogger(__name__)


class Error(act.sub.Error):
    """Exceptions raised in this module are of this class."""


class JsonCanNotMergeObjectWithPrimitiveType(Error):
    pass


def _merge_files(source_path_list, target_path, symbols=None):
    """Merge json files in a source file list.
    """
    logger.debug("ENTER _merge_files(%s, %s).", source_path_list, target_path)
    t = {}
    file_count = 0
    for p in source_path_list:
        file_count += 1
        loc_stk = [p]
        o = act.sub.read_json(p)
        if len(source_path_list) > 1:
            logger.debug('Check types %s.', o)
            try:
                act.sub.check_types(o, loc_stk)
            except act.sub.Error:
                logger.exception('Can not merge file %s.', p)
                raise
        if file_count > 1:
            logger.debug('Merge %s into %s.', o, t)
            _merge_obj(t, o, loc_stk)
        else:
            t = o
    if symbols:
        logger.debug('before interpolate %s', t)
        logger.debug('sym2val %s', symbols.sym2val)
        symbols.interpolate(t)
        logger.debug('after interpolate %s', t)
    try:
        act.sub.write_as_json(t, target_path)
    except act.sub.Error:
        try:
            os.remove(target_path)
        except FileNotFoundError:
            pass
        raise
    return target_path


def _preprocess(mergelist_path):
    """Pre-process mergelist. 
    
    Remove the symbol definition file and replace files that are
    themselves merge lists the files they refer to (recursively). 
    
    Args:
        mergelist_path: merge list file 
     
    Returns: (merge_source_path_list, symbols) tuple. 
        merge_source_path_list: A list of canonicalized paths of files to 
            merge.
        symbols: symbols object (global symbols set only), or None if no
            symbol definition file.
    """
    mspl = []
    symbols = None
    sym_def_path = None
    for p in act.sub.read_and_resolve_path_array(mergelist_path):
        if not act.sub.is_symbol_def_file(p):
            mspl.append(p)
        elif not sym_def_path:
            sym_def_path = p
        else:
            raise Error('Merge list can have at most one symbol definition '
                        f'file. The 2nd symbol def file {p}. '
                        f'Merge list: {mergelist_path}.')
    if sym_def_path:
        if not mspl:
            raise Error('Merge list has only a symbol definition file, and '
                        'no other files. '
                        f'Merge list: {mergelist_path}. '
                        f'Symbol definition file {sym_def_path}.')
        symbols = act.symbols.Symbols(sym_def_path)
    return (mspl, symbols)


def merge(source_path, target_path, symbol_set_mode, symbol_set_name=None):
    """Merge json files in a json array of file paths.
    
    Args:
        source_path: Merge list file (JSON array of file paths).
        target_path: Output file path. In DIR mode, several files with 
            this name may be created, one per symbol set name, in sub-
            directories in teh otuptu file's directory.
        symbol_set_mode: See command line help. 
        symbol_set_name: See command lien help. 

    Returns:
         target_path, or sequence of target paths for DIR mode.
    
    Raises (act.sub.Error or classes derived from it)
        o For invalid combinations of symbol_set_mode and symbol_set_name 
          arguments.
        o If a merge list element does not resolve to an existing file.
        o If merge lists has more than one symbol file.
        o ... 
    """
    err_msg = act.sub.check_symset_options(symbol_set_mode, symbol_set_name)
    if err_msg:
        raise Error(err_msg)
    files2merge, symbols = _preprocess(source_path)
    if symbols:
        if symbol_set_mode == act.sub.M4S_ERROR:
            raise Error(
                f'Merge list has a symbol file and {act.sub.A_MODE4SYM_N} is '
                f'"{act.sub.M4S_ERROR}". Merge list: {source_path}.')
        if symbol_set_mode == act.sub.M4S_IGNORE:
            symbols = None
        elif symbol_set_mode == act.sub.M4S_NAMED:
            symbols = act.symbols.Symbols(symbols.source_file, symbol_set_name)
        elif symbol_set_mode == act.sub.M4S_FNAME:
            # FNAME mode is default, so if there is no symbol def file in
            # merge list, merge without complaining. IGNORE or ERROR as default
            # would have been more intuitive. For legacy reasons it is FNAME.
            symbol_set_name = _determine_symbol_set_name(source_path)
            if symbol_set_name:
                # Instantiate symbols again, for the set name. In this case,
                # the first instantiation just told us there were symbols in
                # the merge list.
                symbols = act.symbols.Symbols(symbols.source_file,
                                              symbol_set_name)
            else:
                logger.debug(
                    'DOUMENTED FEATURE '
                    'Merge list has a symbol file, and symbol set '
                    'name could not be determined from merge list '
                    'file name, so global symbols only. '
                    'Merge list: %s.', source_path)
        elif symbol_set_mode == act.sub.M4S_DIR:
            # R E T U R N
            return _merge_dir_mode(files2merge, target_path, symbols)
    elif symbol_set_name:
        raise Error('Merge list has no symbol definition file. Expected a '
                    f'symbol definition file with symbol set '
                    f'"{symbol_set_name}". Merge list: {source_path}.')
    return _merge_files(files2merge, target_path, symbols)


def _merge_dir_mode(files2merge, target_path, symbols):
    outpaths = []
    # Global symbols in base dir.
    outpaths.append(_merge_files(files2merge, target_path, symbols))
    try:
        h, t = os.path.split(target_path)
        for symbol_set_name in sorted(symbols.set_names):
            po = os.path.join(h, symbol_set_name)
            act.sub.create_dir_if_inexistant(po)
            po = os.path.join(po, t)
            outpaths.append(
                _merge_files(
                    files2merge, po,
                    act.symbols.Symbols(symbols.source_file, symbol_set_name)))
    except act.sub.Error:
        for po in outpaths:
            try:
                os.remove(po)
            except FileNotFoundError:
                pass
        raise
    return outpaths


def _merge_obj(t, s, loc_stk):
    """Merge object s into object t."""
    kt = set(t.keys())
    ks = set(s.keys())
    for k in sorted(kt & ks):  # attribute names in common
        loc_stk.append(k)
        if isinstance(t[k], dict) and isinstance(s[k], dict):
            logger.debug('Merge objects. Source %s.', loc_stk)
            _merge_obj(t[k], s[k], loc_stk)
        elif isinstance(t[k], dict) or isinstance(s[k], dict):
            raise JsonCanNotMergeObjectWithPrimitiveType(
                f'Target type {type(t[k])}. Source type {type(s[k])}. '
                f'Source {loc_stk}.')
        elif t[k] != s[k]:
            logger.debug('Replace value "%s" with "%s" from: %s.', t[k], s[k],
                         loc_stk)
            t[k] = s[k]
        else:
            logger.debug('Same value "%s". Source %s.', s[k], loc_stk)
        loc_stk.pop()
    for k in sorted(ks - kt):  # source only attribute names
        loc_stk.append(k)
        logger.debug('Add value "%s" from: %s.', s[k], loc_stk)
        t[k] = s[k]
        loc_stk.pop()


def _determine_symbol_set_name(mergelist_path):
    """Result None means default to global symbol set."""
    result = None
    fname = os.path.split(act.sub.canonical(mergelist_path))[1]
    if fname.endswith(act.sub.MERGELIST_EXT):
        # Chop off ending
        s = fname[:len(fname) - len(act.sub.MERGELIST_EXT)]
        # Any dots in what remains?
        i = s.rfind('.')
        if i >= 0:
            # Yes. Chop off up to rightmost dot.
            dot_setname = s[i:]
            if len(dot_setname) > 1:
                # There is more than just a dot. Chop off dot for sym set name.
                result = dot_setname[1:]
            else:
                # There is only a dot.
                raise Error(
                    f'Could not determine symbol set name from {fname}. '
                    f'Strange file names like "{act.sub.MERGELIST_EXT}" or '
                    f'"a.{act.sub.MERGELIST_EXT}" not allowed.'
                    f'Merge list: {mergelist_path}.')
        else:
            # No. What remains is symbol set name.
            result = s
    return result


def _parse_args():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=_A_DESCRIPTION,
        epilog=act.symbols.__doc__)
    p.add_argument(_A_INFILE_N,
                   help=_A_INFILE_H,
                   type=lambda x: act.sub.rok(x, _A_INFILE_N, p))
    p.add_argument(_A_OUTFILE_N[1:3],
                   _A_OUTFILE_N,
                   help=_A_OUTFILE_H,
                   default=_A_OUTFILE_D)
    act.sub.add_symset_args(p)
    act.sub.add_log_arg(p)
    pa = p.parse_args()
    if pa.outfile == _A_OUTFILE_D:
        h, t = os.path.split(pa.infile)
        pa.outfile = os.path.join(h, act.sub.OUT_MERGED_DEFAULT_PREFIX + t)
    else:
        h, t = os.path.split(act.sub.canonical(pa.outfile))
        if not os.path.isdir(h):
            val_name_in_help = _A_OUTFILE_N[2:].upper()
            p.error(f'Parent directory of {val_name_in_help} does not exist. '
                    f'{val_name_in_help}: {pa.outfile}.')
    err_msg = act.sub.check_symset_options(pa.mode4symbols, pa.symset)
    if err_msg:
        p.error(err_msg)
    return pa


def _main():
    args = _parse_args()
    act.sub.set_up_logging(act.sub.LOGGING_LEVEL_NAME2VALUE[args.log_level],
                           args.console)
    logger.debug('symset=%s mode4symbols=%s', args.symset, args.mode4symbols)
    merge(args.infile, args.outfile, args.mode4symbols, args.symset)


if __name__ == '__main__':
    _main()
