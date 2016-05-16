import unittest
import copy

from netlistx.scan.partial_esgraph import *
class Test_upaths_constraints(unittest.TestCase):
    u'''产生测试三种产生不平衡路径约束的方法，
        simple, upaths_contraints_simple
        complex, upaths_contraints_complex
        stupid, upaths_contraints_stupid
    '''

    def setUp(self):
        nodes = ("abcdefghxyzmn")
        self.node2x = {node:node for node in nodes}
        self.upaths = {
            ("a","b"):[
                ['a','b'],
                ['a','c','b'],
                ['a','d','b']
                ]
            }

    def test_Complex(self):
        u'''相交的UNP，所有组的约束全部产生，不相交的UNP，直接是起点加终点约束
        '''
        upaths = copy.deepcopy(self.upaths)
        upaths.update({
            ('d','e'):[
                ['d','f', 'e'],
                ['d','c','e'],
                ['d','g','h','e']    
            ],
            ('x','y'):[
                ['x','z','y'],
                ['x','m','n','y']
                ]
            })
        constraints = upaths_contraints_complex(upaths, self.node2x)
        self.assertListEqual(constraints, [
            "a+c+b<= 2;...",
            "a+b+d<= 2;...",
            'e+d+g+f+h<= 4;...',
            "c+e+d+g+h<= 4;...",
            'x+y<= 1;...'
            ])

    def test_Simple(self):
        u'''对一个UNP，只产生一个约束， 起点+终点<= 1;...
        '''
        upaths = upaths_contraints_simple(self.upaths, self.node2x)
        self.assertListEqual(upaths, ["a+b<= 1;..."])
    
    def test_Stupid(self):
        u'''列举每一组长度的所有约束
        '''
        upaths = copy.deepcopy(self.upaths)
        upaths.update({
        ('d','e'):[
            ['d','f', 'e'],
            ['d','c','e'],
            ['d','g','h','e']    
        ]})
        constrints = upaths_contraints_stupid(upaths, self.node2x)
        self.assertListEqual(constrints, [
            "a+c+b<= 2;...",
            "a+b+d<= 2;...",
            'e+d+g+f+h<= 4;...',
            "c+e+d+g+h<= 4;..."
            ])

    def test_MoreComplex(self):
        upaths = copy.deepcopy(self.upaths)
        upaths.update({
            ('e','f'):[
                ['e','f'],
                ['e','g','f'],
                ['e','h','f'],
                ['e','x','y','f'],
                ['e','d','z','f']
                ]
            })
        constrints = upaths_contraints_more_complex(upaths, self.node2x)
        self.assertListEqual(constrints, [
            "a+c+b<= 2;...",
            "a+b+d<= 2;...",
            'e+g+f<= 2;...',
            "e+f+y+x<= 3;...",
            "e+d+f+z<= 3;...",
            "e+g+f+y+x<= 4;...",
            "e+d+g+f+z<= 4;...",
            ])
    
    def test_merge_group(self):
        node2x = {
            'a':'x1',
            'b':'x2',
            'c':'x3',
            'd':'x4',
            'e':'x5',
            }
        group = [
            ['a','b','c'],
            ['a','d','c'],
            ['a','e','c']
            ]
        group = merge_group(group, node2x)
        self.assertDictEqual(
            node2x,
            {'a':'x1',
             'b':'x2',
             'c':'x3',
             'd':'x2',
             'e':'x2',
            })
        self.assertListEqual(group, [['a','b','c']])

    def test_merge_group_failed(self):
        #测试如果一个组内的几个路径长度不想等，则merge_group无法正常工作，报assertion
        node2x = {
            'a':'x1',
            'b':'x2',
            'c':'x3',
            'd':'x4',
            'e':'x5',
            }
        group = [
            ['a','b'],
            ['a','d','c'],
            ['a','e','c']
            ]
        with self.assertRaises(AssertionError):
            merge_group(group,node2x)

if __name__ == '__main__':
    unittest.main()
