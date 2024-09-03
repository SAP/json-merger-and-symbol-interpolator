"""Factor common attributes out of json files.


Data structure notes
--------------------

JSON like this
    {
        "J45": {
            "COUNTRY": "CN",
            "COMPANY_CODE": "1310"
        }
    }

loads into python as dictionaries (nested when needed)

    {'J45': {'COUNTRY': 'CN', 'COMPANY_CODE': '1310'}}

which we "flatten" into this

    {'J45.COUNTRY':'CN', 'J45.COMPANY_CODE':'1310'}

to do set operations on the dictionary's keys.

"""
import os.path
import logging
import argparse
import glob
# own imports
import act.sub

_FACTORED_EXT = f'.factored{act.sub.JSON_EXT}'
_FNAME_COMMON_FACTORS = f'common{act.sub.JSON_EXT}'

# Text with _A prefix for command line Args
_A_DESCRIPTION = (
    """Factors common values out of JSON files.

Example: factoring a.json:'{"x":1, "y":2}' and b.json:'{"z":3, "y":2}' would give
5 files: a.json:'{"x":1}', b.json:'{"z":3}', """
    f"{_FNAME_COMMON_FACTORS}:"
    """'{"y":2}', """
    f"""a{act.sub.MERGELIST_EXT}: '["{_FNAME_COMMON_FACTORS}", "a.json"]', 
b{act.sub.MERGELIST_EXT}: '["{_FNAME_COMMON_FACTORS}", "b.json"]'. 

The two ?.mergelist.json files are intended as inputs for the mergejson.py 
program. Running mergejson on these files generates the original input files.
""")
_A_INFILE_N = 'infile'
_A_INFILE_H = f"""Either a file or a glob pattern. If a file, it must
contain a JSON array of strings, each the path to a JSON file to factor. The 
paths can be absolute or relative. If relative, they are resolved relative to 
{_A_INFILE_N}'s directory. Example: ["a.json","/x/b.json","../y/c.json"]. If a
glob pattern, the files to factor are those matching the glob pattern. Example:
"/some/path/**/??.json". Hint: ** means search all sub-directories; ?? matches 
any two characters.
"""
_A_OUTDIR_N = '--outdir'
_A_OUTDIR_H = f"""Path to a directory for output. If absent, {_A_INFILE_N} must
be a file (not a glob pattern), and all output files are written to infile's 
directory. If present (1) the directory is deleted and then re-created (2) the 
directory structure of the input files is mirrored under outdir (3) output 
files are written to the mirrored directory corresponding to the input 
directory. Example: outdir=/D infile=["a.json","./x/b.json"] result:
/D/{_FNAME_COMMON_FACTORS},
/D/a.json,
/D/a{act.sub.MERGELIST_EXT},
/D/x/b.json,
/D/x/b{act.sub.MERGELIST_EXT}.
"""

logger = logging.getLogger(__name__)


class Error(act.sub.Error):
    """Exceptions raised in this module are of this class."""


def _inflate(flat_dict, flat_keys):

    def _add_element(d, kl, v):
        if len(kl) == 1:
            d[kl[0]] = v
        else:
            if kl[0] not in d:
                d[kl[0]] = {}
            _add_element(d[kl[0]], kl[1:], v)

    result = {}
    for k in sorted(flat_keys):
        _add_element(result, k.split('.'), flat_dict[k])
    return result


def _flatten(d, loc_stk, r):
    for k in sorted(d.keys()):
        loc_stk.append(k)
        if isinstance(d[k], dict):
            _flatten(d[k], loc_stk, r)
        else:
            # array or primitive type or None
            r['.'.join(loc_stk[1:])] = d[k]
        loc_stk.pop()


def _load_and_flatten(canonical_paths):
    """Reads as json each file in canonical_paths into a flattened dictionary.

    Returns:
        A dictionary of flattened dictionaries, keyed by the cannonical
        path of source.
    """
    result = {}
    for p in canonical_paths:
        o = act.sub.read_json(p)
        loc_stk = [p]
        act.sub.check_types(o, loc_stk)  #, False)
        result[p] = {}
        _flatten(o, loc_stk, result[p])
    return result


def _intersection(p2flat):
    """Returns set of keys that all flat dicts have same values for."""
    result = set()
    first_flat = None
    for p in p2flat:
        if first_flat is None:
            first_flat = p2flat[p]
            result = set(first_flat.keys())
            logger.debug('Start with %d keys from %s.', len(result), p)
        else:
            result = result & set(p2flat[p].keys())
            logger.debug('Check values of %d common keys from %s.', len(result),
                         p)
            remove = set()
            for k in result:
                # pylint: disable=unsubscriptable-object
                if first_flat[k] != p2flat[p][k]:
                    remove.add(k)
                    logger.debug('Key %s. Known value "%s" != "%s" in %s.', k,
                                 first_flat[k], p2flat[p][k], p)
            result = result - remove
    logger.info('In all %d files these %d attributes have common values: %s.',
                len(p2flat), len(result), result)
    return result


def _output_paths(in_paths, source_dir, target_dir):
    factored_files = []
    merge_files = []
    if target_dir is None:
        common_factors = os.path.join(
            source_dir, act.sub.OUT_PREFIX + _FNAME_COMMON_FACTORS)
        for p in in_paths:
            fname_base = os.path.split(p)[1]
            if not os.path.normcase(fname_base).endswith(act.sub.JSON_EXT):
                logger.warning('No conventional "%s" extension for %s.',
                               act.sub.JSON_EXT, p)
            else:
                fname_base = fname_base[:-len(act.sub.JSON_EXT)]
            factored_files.append(
                os.path.join(source_dir,
                             act.sub.OUT_PREFIX + fname_base + _FACTORED_EXT))
            merge_files.append(
                os.path.join(
                    source_dir,
                    act.sub.OUT_PREFIX + fname_base + act.sub.MERGELIST_EXT))
    else:
        common_factors = os.path.join(target_dir, _FNAME_COMMON_FACTORS)
        act.sub.create_or_empty_dir(target_dir)
        msd = act.sub.MirrorSubdirs(target_dir, in_paths)
        for p in in_paths:
            p = msd.gen_file_path(p)
            pdir, fname_base = os.path.split(p)
            fname_base_nc = os.path.normcase(fname_base)
            if not fname_base_nc.endswith(act.sub.JSON_EXT):
                logger.warning('No conventional "%s" extension for %s.',
                               act.sub.JSON_EXT, p)
            elif (fname_base_nc.endswith(act.sub.OUT_MERGED_EXT) and
                  len(fname_base_nc) > len(act.sub.OUT_MERGED_EXT)):
                # When we run on mergeall.py output to extract even more
                # common factors, we special case file name processing so that
                # the merge list and files to merge do not have merged in
                # their names.
                fname_base = fname_base[:-len(act.sub.OUT_MERGED_EXT)]
            else:
                fname_base = fname_base[:-len(act.sub.JSON_EXT)]

            factored_files.append(
                os.path.join(pdir, fname_base + act.sub.JSON_EXT))
            merge_files.append(
                os.path.join(pdir, fname_base + act.sub.MERGELIST_EXT))

    return (common_factors, factored_files, merge_files)


def factor(source_path, target_dir=None, file_not_glob=True):
    """Factor common values out of json files.

    Arrays not supported.

    Args:
        source_path: A file containing a json array of strings. Each value in
            the array is the path to a json file. Relative paths are resolved
            relative to this file's directory.

        target_dir: A directory for the output. If None, output is in same
            directory as source_path. If not None, the directory is deleted
            then re-created, mirroring input file directory structure.
            
        file_not_glob: TODO re-work this function's doc string for glob 
            patterns.

    Returns:
        A three element tuple: (common_factors, factored_files, merge_files).

        common_factors: the path to a json file containing the common
            values factored out of the source files.

        factored_files: ordered list of file paths, 1 for each
            path in source_path.

        merge_files: ordered list of file paths, 1 for each path in
            source_path. When given as input to the merge json tool, will
            result in json file equivalent of the input source.

    """
    source_path = act.sub.canonical(source_path)

    if file_not_glob:
        all_paths = act.sub.read_and_resolve_path_array(source_path)
        source_dir = os.path.split(source_path)[0]
    else:
        all_paths = []
        for p in glob.glob(source_path, recursive=True):
            if os.path.isfile(p):
                all_paths.append(act.sub.canonical(p))
        source_dir = None
    p2flat = _load_and_flatten(all_paths)
    common_factors, factored_files, merge_files = _output_paths(
        list(p2flat.keys()), source_dir, target_dir)
    common_flatkeys = _intersection(p2flat)
    if not common_flatkeys:
        logger.warning('Source files have no common values. %s.', source_path)
    # Write output, one common file, plus 2 files per source file.
    i = 0
    for p, flat in p2flat.items():
        # Write common file, first time only
        if i == 0:
            act.sub.write_as_json(_inflate(flat, common_flatkeys),
                                  common_factors)
        # Write factored file
        local_flatkeys = set(flat.keys()) - common_flatkeys
        if not local_flatkeys:
            logger.warning('All values factored out of %s.', p)
        act.sub.write_as_json(_inflate(flat, local_flatkeys), factored_files[i])
        # Write merged file
        bd = os.path.split(merge_files[i])[0]
        act.sub.write_as_json([
            os.path.relpath(common_factors, bd).replace('\\','/'),
            os.path.relpath(factored_files[i], bd).replace('\\','/')
        ], merge_files[i])
        i += 1
    return (common_factors, factored_files, merge_files)


def _parse_args():

    def _check_infile(arg):
        nonlocal file_not_glob
        if os.path.isfile(arg):
            file_not_glob = True
        else:
            file_not_glob = False
            a = glob.glob(arg, recursive=True)
            if not a:
                p.error(f'Argument {_A_INFILE_N} invalid. It is not a file, '
                        'and as a glob pattern it does not match anything: '
                        f'"{arg}".')
        return arg

    file_not_glob = None

    p = argparse.ArgumentParser(description=_A_DESCRIPTION)
    p.add_argument(_A_INFILE_N, help=_A_INFILE_H, type=_check_infile)
    p.add_argument(_A_OUTDIR_N[1:3],
                   _A_OUTDIR_N,
                   help=_A_OUTDIR_H,
                   type=lambda x: act.sub.dwok(x, _A_OUTDIR_N[2:], p))
    act.sub.add_log_arg(p)
    pa = p.parse_args()
    assert file_not_glob is not None
    if pa.outdir is None and file_not_glob is False:
        p.error(f'When {_A_INFILE_N} is a glob pattern, {_A_OUTDIR_N} is '
                'mandatory.')
    return (pa, file_not_glob)


def _main():
    args, file_not_glob = _parse_args()
    act.sub.set_up_logging(act.sub.LOGGING_LEVEL_NAME2VALUE[args.log_level],
                           args.console)
    logger.info('file_not_glob=%s', file_not_glob)
    factor(args.infile, args.outdir, file_not_glob)


if __name__ == '__main__':
    _main()
