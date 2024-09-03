r"""
===================================
Mergejson Tool String Interpolation
===================================
Enable interpolation of symbols in values in json files, so that all 
occurrences of '${...}' where ... is a symbol name are replaced with a value
for that symbol.

Symbol name value pairs are defined in a json file. Multiple named sets of 
symbols can be defined, in addition to "global" symbols. 

Example:

The file symbols.json:
{"cat"    : { "name":"Felix", "noise":"meow" }
,"dog"    : { "name":"Fido",  "noise":"woof"}
,"mouse"  : { "name":"Mickey" }
,"snake"  : { "name":"Kaa",   "noise":"hiss",  "skin":"scales"}
,"skin":"fur"
}

The file animal.json:
["${name} has ${skin} and says ${noise}."]

File cat.mergelist.json:
["symbols.json", "animal.json"]
after merging, the generated file cat.merged.json:
["Felix has fur and says meow."]

File a.dog.mergelist.json:
["animal.json", "symbols.json"]
after merging, the generated file a.dog.merged.json
["Fido has fur and says woof."]

File snake.mergelist.json
["symbols.json", "animal.json"]
after merging, the generated file snake.merged.json
["Kaa has scales and says hiss."]

File mouse.mergelist.json
["symbols.json", "animal.json"]
after merging, the generated file mouse.merged.json
["Mickey has fur and says ${noise}."]

Notice
1. Nameing convention identifies the symbol definition file in the merge list.
2. The mergelist file name identifies the symbol set to use (if not given as a
   command line parameter).
3. Global symbols defined outside a set can be overridden in a set (e.g. skin 
   for snake). 
4. Undefined symbols are ignored (e.g. noise for mouse).

Symbol Definition File 
=======================
Symbol definition file name: [*.]symbols.json
I.e. simply symbols.json, or anything, followed by .symbols.json.

Named sets of symbols can not nest.

Mergelist File
==============
If not specified as a command line parameter, the name of the symbol set to
use is determined from the merge list file name as follows. 
Mergelist file name: [*.]<symbol_set_name>.mergelist.json 
<symbol_set_name> can not contain dots.
I.e. simply <symbol_set_name>, followed by .mergelist.json, or anything 
ending with a dot followed by <symbol_set_name>.mergelist.json

A mergelist file shall refer to 0 or 1 symbol definition files.
Error if more than one.
Error if 0 and command line specifies a symbol set name.
Error if 1 and mergelist file refers to no other files.
Error if symbol set name not defined in symbol file. 

Pseuo-BNF
=========
symbols := '{' symbol_set_or_global_symbol (',' symbol_set_or_global_symbol)* '}'
symbol_set_or_global_symbol := ( symbol_set | symbol_def )
symbol_set := name ':' '{' symbol_def (',' symbol_def)* '}'
symbol_def := name ':' value
name := '"' (letter|'_') (letter | digit | '_')* '"'
value := A json value

Notes
=====
Interpolate once, values only, prior to writing, after merge.

Skip type check if only one file so that interpolation can be applied to
files containing JSON arrays.
"""

# !!! B E W A R E the module docstring is epilog of mergejson.py's help.

import re
import logging
# own imports
import act.sub

logger = logging.getLogger(__name__)


class Error(act.sub.Error):
    """Exceptions raised in this module are of this class."""


class Symbols:  # pylint: disable=too-few-public-methods

    _R_NAME = r'[^\d\W]\w*'

    _read_json_cache = {}

    def __init__(self, in_file, set_name=None):
        self.sym2val = {}
        self.replacement_counts = {}
        self.names_not_in_dict = set()
        self.set_names = set()
        self._rx = re.compile(r'\$\{(' + self._R_NAME + r')\}', re.UNICODE)
        self.source_file = act.sub.canonical(in_file)
        k = self.source_file  # k is short hand for self.source_file
        if k not in self._read_json_cache:
            self._read_json_cache[k] = act.sub.read_json(in_file)
        self._parse(self._read_json_cache[k], in_file, set_name)

    def _parse(self, d, fname, set_name):
        """Argument d is a read only reference (from a cache)."""

        def _check_name(n):
            if rx.match(n) is None:
                raise Error(
                    f'Symbol name {n} not an identifier in file {fname}.')

        if isinstance(d, list):
            raise Error(
                f'Symbol definition file is a json array. File: {fname}.')
        rx = re.compile('^' + self._R_NAME + r'\Z')
        # first pass: globals and check everything
        for k in sorted(d.keys()):
            _check_name(k)
            if isinstance(d[k], str):
                self.sym2val[k] = d[k]
                self.replacement_counts[k] = 0
            elif isinstance(d[k], dict):
                self.set_names.add(k)
                for j in sorted(d[k].keys()):
                    _check_name(j)
                    if not isinstance(d[k][j], str):
                        raise Error(
                            f'Invalid value for symbol {j} in set {k} in {fname}.'
                        )
            else:
                raise Error(f'Invalid value for symbol {k} in {fname}.')
        if set_name and set_name not in self.set_names:
            raise Error(
                f'No symbol set "{set_name}" in symbol def file {fname}.')
        #second pass: values redefined in symbol set override globals
        for k in sorted(self.set_names):
            if k == set_name:
                for j in sorted(d[k].keys()):
                    self.sym2val[j] = d[k][j]
                    self.replacement_counts[j] = 0
                break

    def _repl(self, match_obj):
        k = match_obj.group(1)
        if k not in self.sym2val:
            self.names_not_in_dict.add(k)
            result = match_obj.group(0)
        else:
            result = self.sym2val[k]
            self.replacement_counts[k] = self.replacement_counts[k] + 1
        return result

    def _replace(self, s):
        return self._rx.sub(self._repl, s)

    def interpolate(self, jo):
        """Interpolate symbols in decoded JSON values. 
        
        Args: 
            jo: Decoded JSON in which to interpolate symbols. 
        """

        def f(k_or_i):
            if isinstance(v, str):
                jo[k_or_i] = self._replace(v)
            elif isinstance(v, (dict, list)):
                self.interpolate(v)
            elif not (v is None or isinstance(v, (bool, float, int))):
                raise Error(
                    f'Strange type for decoded JSON. Type {type(v)}. Value {v}.'
                )

        if isinstance(jo, list):
            for i, v in enumerate(jo):
                f(i)
        elif isinstance(jo, dict):
            for k, v in jo.items():
                f(k)
        else:
            raise Error(f'This is not decoded JSON: jo={jo}.')
