USER GUIDE FOR TOOLS TO MERGE AND TO REPLACE SYMBOLS IN JSON FILES
==================================================================

When shared JSON data is copied to different files, any changes to that data must be made in each file where it was copied. This is tedious and error prone; better to change shared JSON data in one place only. This user guide is about three Python programs, mergejson.py, mergeall.py and factorjson.py, which offer alternatives to copying so that shared JSON data can be changed centrally.

The most up to date and authoritative documentation for these programs is the help written to console when the program is run with the --help command line argument. These programs "live" in this git repository: https://github.com/SAP/json-merger-and-symbol-interpolator.

The reader of this guide should know how to run programs from a command prompt, have Python installed, know basic git commands, and have a basic understanding of JSON. The examples in this guide assume the PYTHONPATH environment variable includes the location where these programs were cloned by git.

Recommended reading to acquire some of this pre-requisite knowledge is: for GIT, chapters 1 & 2 of https://git-scm.com/book/en/v2; for JSON, Introduction & Syntax sections of https://en.wikipedia.org/wiki/JSON; for
Python environment variables on Windows, https://docs.python.org/3/using/windows.html#setting-envvars.

mergejson.py
============

The `mergejson.py` program merges several JSON files into one file, and then replaces symbols inside JSON value strings.

**Example 1: Merge and Replace Hello World!**

    Given files:

        a.json
            {"greeting":"Hello ${planet}!"
            ,"sky":     "The moon is full."}

        b.json
            {"sky":     "The sky is blue."
            ,"answer":  "42"}

        symbols.json
            {"planet":  "world"}

        filelist.json
            ["a.json"
            ,"b.json"
            ,"symbols.json"]

    Run mergejson.py:

        python -m mergejson filelist.json --outfile result.json

    To make file:

        result.json
            {"greeting":"Hello world!"
            ,"sky":     "The sky is blue."
            ,"answer":  "42"}

Notice:

* The main input to the `mergejson.py` program is a file containing a JSON array of references to files. This user guide calls `mergejson.py`'s main input file the merge list.

* Merging combines JSON object attribute-value pairs from two or more files. In `result.json` are 3 JSON attributes: `"greeting"`, `"sky"`, `"answer"`. The source files `a.json` and `b.json` have only two each.

* Last one wins. In `result.json`, the value of JSON attribute `"sky"`, defined both in `a.json` and `b.json`, comes from `b.json`, because `b.json` comes after `a.json` in the merge list.

* Replacement. The symbol `${planet}` in the value of JSON attribute `"greeting"` was replaced with `"world"` according to mappings defined in `symbols.json`. The name `symbols.json` is a reserved file name.

Merging
-------

Files in a merge list can be other merge lists, a symbol definition file or files to merge.

All the files to merge are merged together in order of occurrence. If the same JSON attribute is in more than one file, the result will have the value from the last file merged.

When files are merged together, each must contain a JSON object, not a JSON array.

The values of attributes in a JSON object being merged can be JSON objects, arrays or primitive types.

JSON objects can be merged only with other JSON objects. When merged, they are merged attribute by attribute. There is no limit to how deeply JSON objects can nest.

When JSON arrays are merged, the entire array either replaces or is replaced by another value. Merging never changes what is in a JSON array.

**Example 2: Merging JSON Objects and Arrays**

    Given files:

        a.json
            {"greeting":    ["Hello","universe!"]
            ,"sky":         ["The moon","is full."]
            ,"hitchhiker":  {"question":"Forgotten"}}

        b.json
            {"sky":         ["The","sky","is","blue."]
            ,"greeting":    "Hello world!"
            ,"hitchhiker":  {"answer":"42"}}

        maininput.json
            ["a.json"
            ,"b.json"]

    Run mergejson.py:

        python -m mergejson maininput.json --outfile result.json

    To make file:

        result.json
            {"greeting":    "Hello world!"
            ,"sky":         ["The","sky","is","blue."]
            ,"hitchhiker": {
                "question": "Forgotten",
                "answer":   "42"}}
Notice:

* Last one wins. JSON attributes `"greeting"` and `"sky"`.

* Nested JSON objects are merged. JSON attribute `"hitchhiker"`.

* JSON arrays are not merged but replaced.
   * Array replaced with primitive. JSON attribute `"greeting"`.
   * Array replaced with array. JSON attribute `"sky"`.

If there is only one file in the merge list other than the optional symbol definition file, that file may contain a JSON array. Nothing will be merged, but symbols will be replaced.

**Example 3: File to Merge can be a JSON Array if Alone**

    Given files:

        x.json
            ["${name}" ,"I seek ${quest}." ,"Favorite colour ${colour}."]

        symbols.json
            {"name":    "King Arthur"
            ,"quest":   "the holy grail"
            ,"colour":  "blue"}

        filelist.json
            ["x.json"
            ,"symbols.json"]

    Run mergejson.py:

        python -m mergejson filelist.json --outfile result.json

    To make file:

        result.json
            ["King Arthur", "I seek the holy grail.", "Favorite colour blue."]

Notice:

* There is only one file to merge, `x.json`.

* It contains not a JSON object but a JSON array.

A merge list is a list of references to files. These references can be absolute or relative. If relative, they are resolved relative to the location of the merge list file itself.

**Example 4: Relative Paths in Merge Lists**

    Given files:

        /some/where/else/ file2merge.json {"a":"absolute path"}
        /example/         file2merge.json {"b":"in parent dir"}
        /example/a/       file2merge.json {"c":"in same dir"}
        /example/a/b/     file2merge.json {"d":"in child dir"}

        /example/a/       mergelist.json  ["/some/where/else/file2merge.json"
                                          ,"../file2merge.json"
                                          ,"file2merge.json"
                                          ,"b/file2merge.json"]

    Run mergejson.py (MS Windows syntax; Linux no double quotes):

        python -m mergejson "/example/a/mergelist.json" --outfile result.json

    To make file:

        result.json
            {"a": "absolute path"
            ,"b": "in parent dir"
            ,"c": "in same dir"
            ,"d": "in child dir"}

Notice:

* The merge file has 1 absolute path and 3 relative paths, one above, one at and one below the merge list's own location.

* In the merge file, the `/` character is used as the path separator. This works both on Windows and Linux. If interoperability is needed, use only `/` and not `\`, the Windows path separator, in your merge files. In JSON strings, `\` has to be escaped as `\\`.

* The `mergejson.py` program's `infile` argument is the full path to the merge list, so its current working directory could be anywhere. In all previous examples, only a file name was given, so the program's current working directory had to be the merge file's directory.

If a merge list refers to a JSON file which itself is an array of valid file paths (i.e. another merge list), during processing, the reference to the target merge list in the source merge list is replaced with the target array's contents. This is similar to C language `#include` or ABAP `include`, and applies recursively.

**Example 5: Nested Merge Lists**

    Given files:

        m0.json: ["v0.json","m1.json"]
        m1.json: ["m2.json","v1.json"]
        m2.json: ["v2.json"]
        v0.json: {"o":"override A","keep0":0}
        v1.json: {"o":"override B","keep1":1}
        v2.json: {"o":"override C","keep2":2}

    Run mergejson.py:

        python -m mergejson m0.json --outfile result.json

    To make file:

        result.json
            {"keep0":0,"keep1":1,"keep2":2,"o":"override B"}

Notice:

* Result contains `"o":"override B"` from `v1.json` because `v1.json` is merged last.

* Referenced merge lists are replaced in the position in which they occur, so

        m0.json: ["v0.json","m1.json"]           becomes
                 ["v0.json","m2.json","v1.json"] becomes
                 ["v0.json","v2.json","v1.json"].

Replacing Symbols
-----------------

Symbols and their replacement values are defined in a specially named file referred to from a merge list. This file must be named either `symbols.json` or something ending with `.symbols.json`. It must contain a JSON object, the attribute-value pairs of which are the symbols and their replacement values.

Named sets of symbols can be defined with nested JSON object. Only one level of nesting is allowed. Symbols not defined in a nested JSON object are global symbols. They are overridden by identically named symbols defined in a named set.

**Example 6: Named Symbol Sets**

    Given files:

        symbols.json
            {"dog"      : { "name":"Fido",  "noise":"woof"}
            ,"mouse"    : { "name":"Mickey" }
            ,"snake"    : { "name":"Kaa",   "noise":"hiss", "skin":"scales"}
            ,"skin"     : "fur"}

        animal.json
            ["${name} has ${skin} and says ${noise}."]

        mergelist.json
            ["symbols.json", "animal.json"]

    Run mergejson.py:

        python -m mergejson mergelist.json -m NAMED -s dog --outfile result.json

    To make file:

        result.json
            ["Fido has fur and says woof."]
Notice:

* The `-m NAMED -s dog` command line arguments give the symbol set to use.

* `${name}` and `${noise}` are replaced with values defined for `"name":"Fido"` and `"noise":"woof"` in named set `"dog"`.

* `${skin}` is replaced with the global value defined for `"skin":"fur"`.

Run again with `-s mouse`.

    Given files:

        same as as above

    Run mergejson.py:

        python -m mergejson mergelist.json -m NAMED -s mouse --outfile result.json

    To make file:

        result.json
            ["Mickey has fur and says ${noise}."]

Notice:

* Undefined symbols are not replaced. `${noise}` is not replaced because symbol `"noise"` is undefined. It is defined neither in named set `"mouse"` nor as a global symbol.

Run again with `-s snake`.

    Given files:

        same as as above

    Run mergejson.py:

        python -m mergejson mergelist.json -m NAMED -s snake --outfile result.json

    To make file:

        result.json
            ["Kaa has scales and says hiss."]

Notice:

* Symbol values in named sets override global symbol values. The global `"skin":"fur"` is overridden with `"skin":"scales"` in the named set `"snake"`.

Symbol Processing Modes
-----------------------

The `--mode4symbols` (short form `-m`) argument to the `mergejson.py` program determine which symbol set to use.

In `NAMED` mode, the symbol set name is a command line argument. See example 6, `-m NAMED -s dog` (or `mouse` or `snake`).

In `FNAME` mode, the symbol set name to use comes from the merge list file name. A merge list file named `dog.mergelist.json` selects symbol set name `dog`. If the merge list file name does not end with `.mergelist.json`, only global symbols are replaced. `FNAME` mode is the default mode. Examples 1 and 3 run with this default FNAME mode.

In `DIR` mode, one result file per set in the symbols definition file is generated. Each of these files is generated in a sub-directory of the base output directory named after the symbol set. Additionally, one result file with only global symbols replaced is generated in the base output directory. The base output directory is the parent directory of the `--outfile` argument. The default base output directory, when no `--outfile` argument is given, is the merge list's directory.

**Example 7: DIR Mode**

    Given files:

        z.json
            ["${name}" ,"I seek ${quest}."]

        symbols.json
            {"king":    {"name":    "King Arthur"
                        ,"quest":   "the holy grail"}
            ,"knight":  {"name":    "Sir Lancelot"
                        ,"quest":   "Guinevere"}
            ,"name":  "Serf Bob"
            ,"quest": "subsistence"}

        filelist.json
            ["z.json"
            ,"symbols.json"]

    Run mergejson.py (base directory /x must exist):

        python -m mergejson -m DIR filelist.json --outfile "/x/result.json"

    To make files:

        /x/king/   result.json ["King Arthur",  "I seek the holy grail."]
        /x/knight/ result.json ["Sir Lancelot", "I seek Guinevere."]
        /x/        result.json ["Serf Bob",     "I seek subsistence."]

Notice:

* The symbol definition file has two symbol sets, `king` and `knight`.

* The mergejson program runs in `DIR` mode (`-m DIR`).

* This creates three output files, each called `result.json`, each in a different directory.

* A sub-directories per symbol set name is created under the base directory.

* The symbol set name for symbol replacement in generated files is the sub directory name.

* No symbol set name is used for symbol replacement in the `--outfile` target (i.e. global symbols only).

mergeall.py
===========

The `mergeall.py` program processes all merge lists in and under a source directory.

Merge lists are identified by file naming convention: `[*.]mergelist.json` (i.e. a file whose name is `mergelist.json` or ends with `.mergelist.json`).

A merge list file will be ignored if it is in a per-directory exclusion list called `mergeall.exclude.json`. The exclusion list is a JSON array of file names without any path components.

The `mergeall.py` program runs the `mergejson.py` program on each merge list file. Merged output is generated under a specified target directory, in sub-directories mirroring the source directory tree. The output file names are the source merge list file names, with suffix `mergelist.json` replaced with `merged.json`. BEWARE: If the target directory exists, all its contents are deleted and then regenerated.

The `mergeall.py` program accepts the same symbol processing mode command line arguments as `mergejson.py` does: `--mode4symbols` (short form `-m`) and `--symset` (short form `-s`). They can be overridden for a directory D and all its sub-directories (until overridden again in a sub-directory) with values from a file in D named `mergeall.args.json`. For example, such a file might contain `{"--mode4symbols":"NAMED", "--symset":"INDIA"}`. The short single dash forms of the command line arguments are not recognized in `mergeall.args.json` files.

**Example 8: Merge All**

    Given:

        in/             a.mergelist.json [      "common.json",       "symbols.json"]
        in/left/        a.mergelist.json [   "../common.json",    "../symbols.json"]
        in/left/depth2/ a.mergelist.json ["../../common.json", "../../symbols.json"]
        in/left/depth2/ b.mergelist.json ["no_such_file.json", "../../symbols.json"]
        in/right/       a.mergelist.json [   "../common.json",    "../symbols.json"]
        in/right/       b.mergelist.json [   "../common.json",    "../symbols.json"]

        in/             common.json           ["${x}"]
        in/             symbols.json          {"a":{"x":"1"},"b":{"x":"2"}}
        in/left/        mergeall.args.json    {"--mode4symbols":"NAMED", "--symset":"b"}
        in/left/depth2/ mergeall.exclude.json ["b.mergelist.json"]


    Run mergeall.py:

        python -m mergeall -o out in

    To make:

        out/             a.merged.json ["1"]
        out/left/        a.merged.json ["2"]
        out/left/depth2/ a.merged.json ["2"]
        out/right/       a.merged.json ["1"]
        out/right/       b.merged.json ["2"]

Notice:

* There are six merge lists under the source directory called `in`.

* Five files are generated under target directory called `out`.

* One file was skipped because of the exclusion list `in/left/depth2`.

* Files are generated in subdirectories mirroring the source merge lists' locations.

* No symbol mode arguments are given on the command line so `--mode4symbols` defaults to `FNAME`. In `FNAME` mode a file named `a.mergelist.json` would select symbol set `"a"`. In symbol set `"a"`, `"X"` is `"1"`, so symbol `${x}` is replaced with `1`, and the generated file a.merged.json would contain `["1"]`. Likewise, file `b.merged.json` containing `["2"]` would be generated from `b.mergelist.json` because symbol set `"b"` would be used.

* The symbol mode for sub directory `left` and everything below it comes from the file `mergeall.args.json`. `FNAME` mode is replaced by `NAMED` mode with symbol set `"b"`. Therefore, the `a.merged.json` files in `left` and `left/depth2` both contain `["2"]` because symbol set `"b"` is used for generation. In `FNAME` mode, they would have contained `["1"]`.

factorjson.py
=============

The `factorjson.py` program extracts common JSON data from multiple JSON files. The JSON files to factor are either listed in a file or specified with a filename pattern to match. The program also makes one merge list per input file with which mergejson.py could re-create the JSON in the input file.

**Example 9: Factor Hello World!**

    Given files:

        in/ a.json {"greeting":"Hello world!"
                   ,"sky":     "blue"
                   ,"answer":  42}

        in/ b.json {"greeting":"Hello world!"
                   ,"sky":     "grey"}

    Run factorjson.py:

        python -m factorjson in\*.json -o out

    To make files:

        out/ common.json       {"greeting": "Hello world!"}
        out/ a.json            {"answer": 42, "sky": "blue"}
        out/ b.json            {              "sky": "grey"}
        out/ a.mergelist.json  ["common.json","a.json"]
        out/ b.mergelist.json  ["common.json","b.json"]

Notice:

* The main argument to the `factorjson.py` program is a directory with a filename pattern. All files matching the pattern in the directory are factored.

* Output is written under the directory give by the `-o` argument. BEWARE: if the directory exists is deleted and then re-created.

* In the output directory, common JSON data is factored out of correspondingly named input files and into `common.json`. The name `common.json` is a reserved file name.

* The JSON attribute-value pairs must be the same in all input files to be factored out. Attribute "greetings" is factored out, but not attribute "sky".

* If the `mergejson.py` program were run on the `?.mergelists.json` files, the same JSON would be generated as in each source input file.

Each file to factor must contain a JSON object. The values of JSON attribute-value pairs to factor can be JSON primitive types, arrays or objects. Objects and arrays can nest repeatedly. Objects are factored attribute by attribute, but entire arrays must be the same (equivalent JSON) to be factored out.

**Example 10: Factoring Nested Objects, Arrays, and Sub-Directories.**

    Given files:

        in/       a.json  {"none" :{"a":1,"b":{"c":2,"d":3}}
                          ,"whole":{"A":10,"B":{"C":[20],"D":30}}
                          ,"part" :{"W":100,"X":{"Y":[200,1],"Z":[-3,-4]}}}

        in/under/ b.json  {"none" :{"a":10,"bb":{"c":2,"d":3}}
                          ,"whole":{"A":10,"B":{"C":[20],"D":30}}
                          ,"part" :{"W":100,"X":{"Y":[200,2],"Z":[-3,-4]}}}

        in/       aa.json ["no match"]
        in/under/ a.jsn   ["skipped"]

    Run factorjson.py:

        python -m factorjson in/**/?.json -o out

    To make files:

        out/       common.json {"part":{"W":100,"X":{"Z":[-3,-4]}}
                               ,"whole":{"A": 10,"B":{"C": [20],"D": 30}}}

        out/       a.json      {"none":{"a":1,"b":{"c":2,"d":3}}
                               ,"part":{"X":{"Y":[200,1]}}}

        out/under/ b.json      {"none":{"a":10,"bb":{"c":2,"d":3}}
                               ,"part":{"X":{"Y":[200,2]}}}

        out/       a.mergelist.json ["common.json","a.json"]
        out/under/ b.mergelist.json ["../common.json","b.json"]

Notice:

* The main argument to the `factorjson.py` program is a directory `in/` followed by a pattern `**/?.json`. The `**` means search this directory and all sub-directories for matching file names. The `?` matches any single character. The pattern can be any glob pattern (google it for fancier matching options).

* The attribute `whole` is factored out. The attibute `none` is not factored out. The attibute `part` is partly factored out.

* The attribute `part` differed only in the second element of the array `Y` nested in `X`. Everything except this array was factored out of `part`.