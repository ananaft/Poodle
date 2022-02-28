## Add test for SyntaxError (e.g. [1a,2])
## Add test for NameError (e.g. {a: 12})

import context
from core import smart_input

from unittest import TestCase
from unittest.mock import patch


class TestSmartInput(TestCase):

    # Test booleans
    @patch('builtins.input', return_value='True')
    def test_bool_true_1(self, input):
        self.assertTrue(smart_input())

    @patch('builtins.input', return_value='True ')
    def test_bool_true_2(self, input):
        self.assertEqual(smart_input(), 'True ')

    @patch('builtins.input', return_value=' True')
    def test_bool_true_3(self, input):
        self.assertEqual(smart_input(), ' True')

    @patch('builtins.input', return_value='true')
    def test_bool_true_4(self, input):
        self.assertEqual(smart_input(), 'true')

    @patch('builtins.input', return_value='TRUE')
    def test_bool_true_5(self, input):
        self.assertEqual(smart_input(), 'TRUE')

    @patch('builtins.input', return_value='False')
    def test_bool_false_1(self, input):
        self.assertFalse(smart_input())

    @patch('builtins.input', return_value='False ')
    def test_bool_false_2(self, input):
        self.assertEqual(smart_input(), 'False ')

    @patch('builtins.input', return_value=' False')
    def test_bool_false_3(self, input):
        self.assertEqual(smart_input(), ' False')

    @patch('builtins.input', return_value='false')
    def test_bool_false_4(self, input):
        self.assertEqual(smart_input(), 'false')

    @patch('builtins.input', return_value='FALSE')
    def test_bool_false_5(self, input):
        self.assertEqual(smart_input(), 'FALSE')


    # Test integers
    @patch('builtins.input', return_value='123')
    def test_int_1(self, input):
        self.assertEqual(smart_input(), 123)

    @patch('builtins.input', return_value='123 ')
    def test_int_2(self, input):
        self.assertEqual(smart_input(), '123 ')

    @patch('builtins.input', return_value=' 123')
    def test_int_3(self, input):
        self.assertEqual(smart_input(), ' 123')

    @patch('builtins.input', return_value='123 456')
    def test_int_4(self, input):
        self.assertEqual(smart_input(), '123 456')

    @patch('builtins.input', return_value='1a')
    def test_int_5(self, input):
        self.assertEqual(smart_input(), '1a')

    # Test floats
    @patch('builtins.input', return_value='3.14')
    def test_float_1(self, input):
        self.assertEqual(smart_input(), 3.14)

    @patch('builtins.input', return_value='3.')
    def test_float_2(self, input):
        self.assertEqual(smart_input(), 3.)

    @patch('builtins.input', return_value='3. ')
    def test_float_3(self, input):
        self.assertEqual(smart_input(), '3. ')

    @patch('builtins.input', return_value=' 3.')
    def test_float_4(self, input):
        self.assertEqual(smart_input(), ' 3.')

    @patch('builtins.input', return_value='3. 14')
    def test_float_5(self, input):
        self.assertEqual(smart_input(), '3. 14')

    @patch('builtins.input', return_value='3.1a')
    def test_float_6(self, input):
        self.assertEqual(smart_input(), '3.1a')


    # Test placeholders
    # new placeholder = ~~x~~

    # Test lists
    @patch('builtins.input', return_value='[1,2,3]')
    def test_list_simple(self, input):
        self.assertEqual(smart_input(), [1,2,3])

    @patch('builtins.input', return_value='[1, 2,  3]')
    def test_list_whitespace(self, input):
        self.assertEqual(smart_input(), [1,2,3])

    @patch('builtins.input', return_value='[(1,2), (3,4), (5,6)]')
    def test_list_of_tuples(self, input):
        self.assertEqual(smart_input(), [(1,2), (3,4), (5,6)])

    @patch('builtins.input', return_value='[{"one": 2}, {"three": 4}]')
    def test_list_of_dicts(self, input):
        self.assertEqual(smart_input(), [{'one': 2}, {'three': 4}])

    @patch('builtins.input', return_value='[1, "two", (3,4), {"five": 6}]')
    def test_list_mixed(self, input):
        self.assertEqual(smart_input(), [1, 'two', (3,4), {'five': 6}])

    @patch('builtins.input', return_value='[[1,2], [3,4]]')
    def test_list_nested(self, input):
        self.assertEqual(smart_input(), [[1,2], [3,4]])


    # Test tuples
    @patch('builtins.input', return_value='(1,2,3)')
    def test_tuple_simple(self, input):
        self.assertEqual(smart_input(), (1,2,3))

    @patch('builtins.input', return_value='([1,2], [3,4], [5,6])')
    def test_tuple_of_lists(self, input):
        self.assertEqual(smart_input(), ([1,2], [3,4], [5,6]))

    @patch('builtins.input', return_value='({"one": 2}, {"three": 4})')
    def test_tuple_of_dicts(self, input):
        self.assertEqual(smart_input(), ({'one': 2}, {'three': 4}))

    @patch('builtins.input', return_value='(1, "two", [3,4], {"five": 6})')
    def test_tuple_mixed(self, input):
        self.assertEqual(smart_input(), (1, 'two', [3,4], {'five': 6}))

    
    # Test dicts
    @patch('builtins.input', return_value='{"A": "B", "C": "D"}')
    def test_dict_simple(self, input):
        self.assertEqual(smart_input(), {'A': 'B', 'C': 'D'})

    @patch('builtins.input', return_value='{"l1": [1,2,3], "l2": [4,5,6]}')
    def test_dict_of_lists(self, input):
        self.assertEqual(smart_input(), {'l1': [1,2,3], 'l2': [4,5,6]})

    @patch('builtins.input', return_value='{"t1": (1,2,3), "t2": (4,5,6)}')
    def test_dict_of_tuples(self, input):
        self.assertEqual(smart_input(), {'t1': (1,2,3), 't2': (4,5,6)})

    @patch('builtins.input', return_value='{"A": {"a": 1, "b": 2}, "B": {"a": 1, "b": 2}}')
    def test_dict_of_dicts(self, input):
        self.assertEqual(smart_input(), {'A': {'a': 1, 'b': 2}, 'B': {'a': 1, 'b': 2}})

    @patch('builtins.input', return_value='{"A": "string", "B": [1,2], "C": (3,4), "D": {"a": 1, "b": 2}}')
    def test_dict_mixed(self, input):
        self.assertEqual(smart_input(), {'A': 'string', 'B': [1,2], 'C': (3,4), 'D': {'a': 1, 'b': 2}})


    # Test for wanted errors
    # Lists
    @patch('builtins.input', return_value='[[]')
    def test_error_list_SyntaxError_1(self, input):
        self.assertRaises(expected_exception=SyntaxError)

    @patch('builtins.input', return_value='[(]')
    def test_error_list_SyntaxError_2(self, input):
        self.assertRaises(expected_exception=SyntaxError)

    @patch('builtins.input', return_value='[{]')
    def test_error_list_SyntaxError_3(self, input):
        self.assertRaises(expected_exception=SyntaxError)

    @patch('builtins.input', return_value='[{]')
    def test_error_list_SyntaxError_4(self, input):
        self.assertRaises(expected_exception=SyntaxError)

    # Tuples

    # Dicts
    @patch('builtins.input', return_value='{a: 1}')
    def test_error_dict_NameError_1(self, input):
        self.assertRaises(expected_exception=NameError)

if __name__ == '__main__':
    unittest.main()
