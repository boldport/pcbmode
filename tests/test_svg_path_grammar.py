#try:
#    import unittest2 as unittest
#except ImportError:
import unittest

from pcbmode.utils.svg_path_grammar import get_grammar

class TestSvgPathGrammar(unittest.TestCase):
    """
    Test the SVG path grammar module
    """

    def test_svg_path_grammar(self):

        grammar = get_grammar()
        self.assertIsNotNone(grammar, 'should have SVG grammar')

        svg_paths = [
            # M=moveto absolute
            'M 15, -3',
            'M-3,2.0',
            'M 1.2, 3.5',
            'M 3,4 6,5 8 9 10 11',
            # m=moveto relative
            'm 3,0',
            'm1,1',
            ' m 7 8',
            'm -1 -2 -3 -4 5 6 7.8 9',
            # C=curveto absolute (cubic bezier)
            'C1,2,3,4,5,6',
            'C 1,2 3,4 5,6',
            'C -1,3.2 5.6,7 8,0.9',
            # c=curveto relative (cubic bezier)
            'c1,2,3,4,5,6',
            'c 1,2 3,4 5,6',
            ' c -1,3.2 5.6,7 8,0.9',
            # Q=curveto absolute (quadratic bezier)
            'Q1,2,3,4',
            'Q 1,2 3,4',
            'Q -1,3.2 5.6,7',
            # q=curveto relative (quadratic bezier)
            'q1,2,3,4',
            'q 1,2 3,4',
            ' q -1,3.2 5.6,7',
            # T=smooth curveto absolute (quadratic bezier)
            'T 15, -3',
            'T-3,2.0',
            'T 1.2, 3.5',
            # t=smooth curveto relative (quadratic bezier)
            't 3,0',
            't1,1',
            ' t 7 8',
            # S=smooth curveto absolute
            'S1,2,3,4',
            'S 1,2 3,4',
            'S -1,3.2 5.6,7',
            # s=smooth curveto relative
            's1,2,3,4',
            's 1,2 3,4',
            ' s -1,3.2 5.6,7',
            # L=lineto absolute
            'L 15, -3',
            'L-3,2.0',
            'L 1.2, 3.5',
            # l=lineto relative
            'l 3,0',
            'l1,1',
            ' l 7 8',
            # H=horizontal lineto absolute
            'H 15',
            'H-3.2',
            'H 1.2',
            # h=horizontal lineto relative
            'h 3',
            'h1.1',
            ' h 7',
            # V=vertical lineto absolute
            'V 15',
            'V-3.2',
            'V 1.2',
            # v=vertical lineto relative
            'v 3',
            'v1.1',
            ' v 7',
            # A=arcto absolute
            #'A20,20 0 0,0 40,40',
            # a=arcto relative
            # z=closepath
            'z',
            'Z',
            'z ',
            # combined
            'M10,10 L20,5 v-10 h-25 z',
            'M10,10L20,5v-10h-25z',
            'M8-29q17-29 12 29q-7 29-23-11t11-17z',
        ]

        for path in svg_paths:
            with self.subTest(path=path):
                result = grammar.parseString(path)
                