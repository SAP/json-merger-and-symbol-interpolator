"""
=================================================================
Test First Design for Mergejson Tool String Interpolation Feature
=================================================================

TEST FEATURES

module test_symbols.py
Juat like _MERGE_JSON except
OPTIONAL 
no dirr stuff
'f' name of mergelist file
's' symbol set name

- minimal
symbol_set = None
symbols.json
{"a":"b"}
f.json
["${a}"]
mergelist.json
{"f.json","symbols.json"}
result.json
["b"]

- cat 
symbol_set = None
symbols.json
{"cat"    : { "name":"Felix", "noise":"meow" }
,"dog"    : { "name":"Fido",  "noise":"woof"}
,"mouse"  : { "name":"Mickey" }
,"snake"  : { "name":"Kaa",   "noise":"hiss",  "skin":"scales"}
,"skin":"fur"
}
animal.json
["${name} has ${skin} and says ${noise}."]
cat.mergelist.json
["symbols.json", "animal.json"]
result.json
["Felix has fur and says meow."]

- dog (just like cat except)   // set name from file with prefix
some.dog.mergelist.json
["animal.json", "symbols.json"] // symbol def file not first in mergelist
result.json
["Fido has fur and says woof."]

- snake (just like cat except)     // override of global symbol in set
cat.mergelist.json RENAME snake.mergelist.json
result.json
["Kaa has scales and says hiss."]

- mouse (just like cat except)  // symbol not found unchanged
cat.mergelist.json RENAME mouse.mergelist.json
result.json
["Mickey has fur and says ${noise}."]

- symbol_def_file_name (just like cat except)
symbols.json RENAME a.b.symbols.json // symbol def file name with prefix
cat.mergelist.json
["a.b.symbols.json", "animal.json"]

- symbol_set_param (just like cat except) // symbol set parameter trumps file name
symbol_set = dog
result.json
["Fido has fur and says woof."]

- no_symbol_set (just like cat except) // no symbol set -> just global symbols
cat.mergelist.json RENAME mergelist.json 
result.json
["${name} has fur and says ${noise}."]

- arrays_ok_if_only_one_file // cat tests this as animals is an array

// interpolation at various levels of nesting
// in object; (array covered in cat) 
// array nested in object; object nested in array
// 3 levels of nesting object
// 3 levels nesting array
- nesting

- do_not_replace_in_names


TEST ERROR AND WARNING DETECTION

- more_than_one_symbol_set_files_in_mergelist
- symbol_set_param_but_no_symbol_set_file
- mergelist_has_only_symbol_set_file
- symbol_set_cl_arg_no_set_in_file
- symbol_set_from_fname_no_set_in_file
- array not allowed if files are merge i.e. more than one.

STRESS AND LOAD
- one_thousand_symbols
symbol_set = None
symbols.json
{"s0":"0", "s1":"v1", ... , "s998":"998", "s999":"v999"}
f.json
["${s0} ${s1} ... ${s999}",
{"x":"${s999} ... ${s0}", 
 "y":{"z":[{"a": "${s1} ... ${s998}"}]
     }
}
]
mergelist.json
{"f.json","symbols.json"}
result.json
["0 v1 ... 998 v999", {"x":"v999 998 ... v1 0"}
{"x":"v999 ... 0", 
 "y":{"z":[{"a": "v1 ... 998"}]
     }
}
]

"""
import unittest
import os
import inspect
import logging
# own imports
import act.mergejson
import tact.sub4t

_LOG_LEVEL = logging.DEBUG

_CAT_SYMBOLS_JSON = """
{"cat"    : { "name":"Felix", "noise":"meow" }
,"dog"    : { "name":"Fido",  "noise":"woof"}
,"mouse"  : { "name":"Mickey" }
,"snake"  : { "name":"Kaa",   "noise":"hiss",  "skin":"scales"}
,"skin":"fur"
}
"""
_ANIMAL_JSON = '["${name} has ${skin} and says ${noise}."]'

_MERGE_W_SYMBOLS = {
    # n = path list of files to merge.
    # i = json list, one string per file to merge
    # o = expected json result string
    # OPTIONAL
    # f = name of mergelist file
    # s = symbol set name
    # x = expect error raised containing all strings in sequence.
    'minimal': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b"}'],
        'o': '["b"]'
    },
    'minimal_obj': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['{"x":"${a}"}', '{"a":"b"}'],
        'o': '{"x":"b"}'
    },
    'cat': {
        'n': ['symbols.json', 'animal.json'],
        'i': [_CAT_SYMBOLS_JSON, _ANIMAL_JSON],
        'o': '["Felix has fur and says meow."]',
        'f': 'cat.mergelist.json',
    },
    'dog': {
        'n': ['animal.json', 'symbols.json'],
        'i': [_ANIMAL_JSON, _CAT_SYMBOLS_JSON],
        'o': '["Fido has fur and says woof."]',
        'f': 'some.dog.mergelist.json',
    },
    'snake': {
        'n': ['symbols.json', 'animal.json'],
        'i': [_CAT_SYMBOLS_JSON, _ANIMAL_JSON],
        'o': '["Kaa has scales and says hiss."]',
        'f': 'snake.mergelist.json',
    },
    'mouse': {
        'n': ['symbols.json', 'animal.json'],
        'i': [_CAT_SYMBOLS_JSON, _ANIMAL_JSON],
        'o': '["Mickey has fur and says ${noise}."]',
        'f': 'mouse.mergelist.json',
    },
    'symbol_def_file_name': {
        'n': ['a.b.symbols.json', 'animal.json'],
        'i': [_CAT_SYMBOLS_JSON, _ANIMAL_JSON],
        'o': '["Felix has fur and says meow."]',
        'f': 'cat.mergelist.json',
    },
    'symbol_set_param': {
        'n': ['symbols.json', 'animal.json'],
        'i': [_CAT_SYMBOLS_JSON, _ANIMAL_JSON],
        'o': '["Fido has fur and says woof."]',
        'f': 'cat.mergelist.json',
        's': 'dog',
    },
    'no_symbol_set': {
        'n': ['symbols.json', 'animal.json'],
        'i': [_CAT_SYMBOLS_JSON, _ANIMAL_JSON],
        'o': '["${name} has fur and says ${noise}."]',
        'f': 'mergelist.json',
    },
    'nesting': {
        'n': ['symbols.json', 'f.json'],
        'i': [
            '{"a":"A", "b":"B"}', """
        {
            "obj": "object ${a}.",
            "arr": [
                "array nested in object ${b}.",
                {
                    "o": "object nested in array ${a}."
                },
                ["fluff",
                    ["three levels of array nesting ${a}.", "x"]
                ]
            ],
            "on1": {
                "on2": {
                    "on3": "three levels of object nesting ${b}."
                }
            }
        }"""
        ],
        "o":
            """
        {
            "obj": "object A.",
            "arr": [
                "array nested in object B.",
                {
                    "o": "object nested in array A."
                },
                ["fluff",
                    ["three levels of array nesting A.", "x"]
                ]
            ],
            "on1": {
                "on2": {
                    "on3": "three levels of object nesting B."
                }
            }
        }"""
    },
    'do_not_replace_in_names': {
        'n': [
            'f.json',
            'symbols.json',
        ],
        'i': ['{"${a}":"${a}"}', '{"a":"b"}'],
        'o': '{"${a}":"b"}'
    },
    'order_symbol_set_override': {
        'n': ['animal.json', 'symbols.json'],
        'i': [_ANIMAL_JSON, _CAT_SYMBOLS_JSON],
        'o': '["Kaa has scales and says hiss."]',
        'f': 'snake.mergelist.json',
    },
    # Test error detection starts here
    'more_than_one_symbol_set_files_in_mergelist': {
        'n': [
            'f.json',
            'symbols.json',
            'more.symbols.json',
        ],
        'i': ['["${a}"]', '{"a":"b"}', '{"c":"b"}'],
        'x': ['more.symbols.json', '2nd symbol def file']
    },
    'symbol_set_param_but_no_symbol_set_file': {
        'n': [
            'f.json',
            'g.json',
        ],
        'i': ['{"A":"f"}', '{"a":"g"}'],
        's': 'dog',
        'x': ['dog', 'no symbol definition file']
    },
    'mergelist_has_only_symbol_set_file': {
        'n': ['lonely.symbols.json',],
        'i': ['{"SYMBOL":"value"}'],
        'x': ['lonely.symbols.json', 'no other files']
    },
    'symbol_set_cl_arg_no_set_in_file': {
        'n': ['animal.json', 'symbols.json'],
        'i': [_ANIMAL_JSON, _CAT_SYMBOLS_JSON],
        's': 'fish',
        'x': ['fish', 'No symbol set']
    },
    'symbol_set_from_fname_no_set_in_file': {
        'n': ['animal.json', 'symbols.json'],
        'i': [_ANIMAL_JSON, _CAT_SYMBOLS_JSON],
        'f': 'fish.mergelist.json',
        'x': ['fish', 'No symbol set']
    },
}

logger = logging.getLogger(__name__)


class Error(Exception):
    """Exceptions raised in this module are of this class."""


class TestSymbols(tact.sub4t.JsonArrayIn):

    @classmethod
    def setUpClass(cls):
        logger.debug('in %s.setUpClass(cls).', cls.__name__)
        super().setUpClass()
        cls._td = _MERGE_W_SYMBOLS

    def _doit(self):
        self._testname_root_dir(inspect.stack()[1].function[len('test_'):])
        f = self._td[self._testname].get('f')
        s = self._td[self._testname].get('s')
        mode = act.sub.M4S_NAMED if s else act.sub.M4S_FNAME
        infile = self._set_up_Ddni_mergelist(
            inspect.stack()[1].function[len('test_'):], f)
        target_path = os.path.join(self._root_dir, 'actual.json')
        if 'x' in self._td[self._testname]:
            with self.assertRaises(act.sub.Error) as cm:
                act.mergejson.merge(infile, target_path, mode, s)
            # print(f'Exception msg: "{cm.exception}".')
            for txt in self._td[self._testname]['x']:
                if txt not in str(cm.exception):
                    self.fail(f'No "{txt}" in exception {cm.exception}.')
            if 'o' in self._td[self._testname]:
                self.fail('Test with x must not have o.')
        else:
            fn_act = act.mergejson.merge(infile, target_path, mode, s)
            fn_exp = os.path.join(self._root_dir, 'expected.json')
            with open(fn_exp, 'w', encoding='utf-8') as fp:
                fp.write(self._td[self._testname]['o'])
            self._assert_json_equal(fn_act, fn_exp)
            if 'x' in self._td[self._testname]:
                self.fail('Test with o must not have x.')

    def test_minimal(self):
        self._doit()

    def test_minimal_obj(self):
        self._doit()

    def test_cat(self):
        self._doit()

    def test_dog(self):
        self._doit()

    def test_snake(self):
        self._doit()

    def test_mouse(self):
        self._doit()

    def test_symbol_def_file_name(self):
        self._doit()

    def test_symbol_set_param(self):
        self._doit()

    def test_no_symbol_set(self):
        self._doit()

    def test_nesting(self):
        self._doit()

    def test_do_not_replace_in_names(self):
        self._doit()

    def test_order_symbol_set_override(self):
        self._doit()

    def test_more_than_one_symbol_set_files_in_mergelist(self):
        self._doit()

    def test_symbol_set_param_but_no_symbol_set_file(self):
        self._doit()

    def test_mergelist_has_only_symbol_set_file(self):
        self._doit()

    def test_symbol_set_cl_arg_no_set_in_file(self):
        self._doit()

    def test_symbol_set_from_fname_no_set_in_file(self):
        self._doit()


if __name__ == '__main__':
    tact.sub4t.set_up_root_logging(_LOG_LEVEL)
    act.mergejson.logger.setLevel(_LOG_LEVEL)
    unittest.main()
