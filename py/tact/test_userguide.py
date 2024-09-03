"""
Unit teste for examples in json-tools-user-guide.txt.
"""
# own imports
import act.sub
import tact.sub4t


class TestMergelistUserGuide(tact.sub4t.TestMergelistBase):

    _td = {
        'ex1_hello_world': {
            'n': [
                'filelist.json',
                'a.json',
                'b.json',
                'symbols.json',
            ],
            'i': [
                '["a.json","b.json","symbols.json"]',
                '{"greeting":"Hello ${planet}!","sky": "The moon is full."}',
                '{"sky":"The sky is blue.","answer": "42"}',
                '{"planet": "world"}',
            ],
            'o': ('{"greeting":"Hello world!","sky":"The sky is blue.",'
                  '"answer":"42"}')
        },
        'ex2_objects_and_arrays': {
            'n': [
                'maininput.json',
                'a.json',
                'b.json',
            ],
            'i': [
                '["a.json","b.json"]', '''
                    {"greeting": ["Hello","universe!"]
                    ,"sky": ["The moon","is full."]
                    ,"hitchhiker": {"question":"Forgotten"}}               
                ''', '''
                    {"sky": ["The","sky","is","blue."]
                    ,"greeting": "Hello world!"
                    ,"hitchhiker": {"answer":"42"}}
                '''
            ],
            'o':
                '''
                    {"greeting": "Hello world!"
                    ,"sky": ["The","sky","is","blue."]
                    ,"hitchhiker": {
                    "question": "Forgotten",
                    "answer": "42"}}
            '''
        },
        'ex3_array_alone': {
            'n': [
                'filelist.json',
                'x.json',
                'symbols.json',
            ],
            'i': [
                '["x.json","symbols.json"]',
                '["${name}","I seek ${quest}.","Favorite colour ${colour}."]',
                '''
                    {"name": "King Arthur"
                    ,"quest": "the holy grail"
                    ,"colour": "blue"}                
                '''
            ],
            'o': ('["King Arthur","I seek the holy grail.",'
                  '"Favorite colour blue."]')
        },
        'ex4_rel_paths': {
            # Couldn't really do the absolute path case.
            'd': ['/some/where/else', '/example/a/b'],
            'n': [
                '/example/a/mergelist.json',
                '/some/where/else/file2merge.json',
                '/example/file2merge.json',
                '/example/a/file2merge.json',
                '/example/a/b/file2merge.json',
            ],
            'i': [
                '''
                    ["../../some/where/else/file2merge.json"
                    ,"../file2merge.json"
                    ,"file2merge.json"
                    ,"b/file2merge.json"]
                ''', '{"a":"absolute path"}', '{"b":"in parent dir"}',
                '{"c":"in same dir"}', '{"d":"in child dir"}'
            ],
            'o':
                '''
                {"a": "absolute path"
                ,"b": "in parent dir"
                ,"c": "in same dir"
                ,"d": "in child dir"}
            '''
        },
        'ex5_nested_mergelists': {
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
        'ex6_named_symbol_sets': {
            'n': [
                'mergelist.json',
                'symbols.json',
                'animal.json',
            ],
            'i': [
                '["symbols.json", "animal.json"]', '''
                    {"dog" : {"name":"Fido", "noise":"woof"}
                    ,"mouse" : {"name":"Mickey" }
                    ,"snake" : {"name":"Kaa", "noise":"hiss", "skin":"scales"}
                    ,"skin" : "fur"}                
                ''', '["${name} has ${skin} and says ${noise}."]'
            ],
            'o': {
                'dog': '["Fido has fur and says woof."]',
                'mouse': '["Mickey has fur and says ${noise}."]',
                'snake': ' ["Kaa has scales and says hiss."]'
            }
        },
    }

    def test_ex1_hello_world(self):
        self._doit()

    def test_ex2_objects_and_arrays(self):
        self._doit()

    def test_ex3_array_alone(self):
        self._doit()

    def test_ex4_rel_paths(self):
        self._doit()

    def test_ex5_nested_mergelists(self):
        self._doit()

    def test_ex6_named_symbol_sets(self):
        tk = 'ex6_named_symbol_sets'
        o = self._td[tk]['o']
        for k, v in o.items():
            self._td[tk]['o'] = v
            self._doit((
                act.sub.M4S_NAMED,
                k,
            ))
        self._td[tk]['o'] = o  # restore


class TestMergeallUserGuide(tact.sub4t.TestMergeallBase):
    _td = {
        'ex7_dir_mode_d4s': {
            'n': [
                'mergelist.json',
                'z.json',
                'symbols.json',
            ],
            'i': [
                '["z.json","symbols.json"]',
                '["${name}" ,"I seek ${quest}."]',
                '''
                    {"king":  {"name":  "King Arthur"
                              ,"quest": "the holy grail"}
                    ,"knight":{"name":  "Sir Lancelot"
                              ,"quest": "Guinevere"}
                    ,"name":  "Serf Bob"
                    ,"quest": "subsistence"}                
                ''',
            ],
            'N': [
                'merged.json',
                'king/merged.json',
                'knight/merged.json',
            ],
            'I': [
                '["Serf Bob", "I seek subsistence."]',
                '["King Arthur", "I seek the holy grail."]',
                '["Sir Lancelot", "I seek Guinevere."]',
            ]
        },
        'ex8_merge_all': {
            'n': [
                'a.mergelist.json',
                'common.json',
                'symbols.json',
                'left/a.mergelist.json',
                'left/mergeall.args.json',
                'left/depth2/a.mergelist.json',
                'left/depth2/mergelist.json',
                'left/depth2/mergeall.exclude.json',
                'right/a.mergelist.json',
                'right/b.mergelist.json',
            ],
            'i': [
                '["common.json","symbols.json"]',
                '["${x}"]',
                '{"a":{"x":"1"},"b":{"x":"2"}}',
                '["../common.json","../symbols.json"]',
                '{"--mode4symbols":"NAMED", "--symset":"b"}',
                '["../../common.json","../../symbols.json"]',
                '["no_such_file_yet.json","../../symbols.json"]',
                '["mergelist.json"]',
                '["../common.json","../symbols.json"]',
                '["../common.json","../symbols.json"]',
            ],
            'N': [
                'a.merged.json',
                'left/a.merged.json',
                'left/depth2/a.merged.json',
                'right/a.merged.json',
                'right/b.merged.json',
            ],
            'I': ['["1"]', '["2"]', '["2"]', '["1"]', '["2"]'],
        }
    }

    def test_ex7_dir_mode_d4s(self):
        self._doit()

    def test_ex8_merge_all(self):
        self._doit()
