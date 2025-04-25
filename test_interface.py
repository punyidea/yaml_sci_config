import unittest

from nptyping.ndarray import NDArray

import yaml_sci_config.interface_classes
from yaml_sci_config import yaml_interface
from yaml_sci_config.yaml_interface import yaml_dataclass
from yaml_sci_config.interface_classes import FunctionHandle, PartialFunctionHandle, LogspaceParams
import re
import numpy as np

@yaml_dataclass
class TestYamlSubtype(object):
    test_type1: float
    test_type2: float


@yaml_dataclass
class TestYamlPostinit(object):
    test_type1: float
    test_type2: float
    def __post_init__(self):
        self.test_type3 = self.test_type1 + self.test_type2

@yaml_dataclass
class TestYamlSubsubclass(TestYamlSubtype):
    a: int

@yaml_dataclass
class T(object):
    a: LogspaceParams
    b: NDArray
    def __post_init__(self):
        self.b = np.asarray(self.b)


class MyTestCase(unittest.TestCase):
    def test_simple_subtype(self):
        test_yaml_a = '''
        test_a: !TestYamlSubtype
            test_type1: 24
            test_type2: 25
        '''
        test_yaml_b = '''
        test_b: !TestYamlPostinit
            test_type1: 24
            test_type2: 25
        '''
        test_yaml_c = '''
        test_c: !TestYamlSubsubclass
            test_type1: 24
            test_type2: 25
            a: 4
        '''

        test_yaml = test_yaml_a + test_yaml_b  + test_yaml_c
        test_read =  yaml_interface.yaml_load(test_yaml)

        comparison = TestYamlSubtype(test_type1=24,test_type2=25)
        self.assertEqual(test_read['test_a'],comparison)

        comparison_b = TestYamlPostinit(test_type1=24,test_type2=25)
        self.assertEqual(test_read['test_b'].test_type3,49)
        self.assertEqual(test_read['test_b'],comparison_b)
        test_yaml_dump = yaml_interface.yaml_dumps({'test_a':comparison})

        comparison_c = TestYamlSubsubclass(a=4, test_type1=24,test_type2=25)
        self.assertEqual(test_read['test_c'],comparison_c)
        self.assertEqual(re.sub(' +',' ',test_yaml_a).strip(),
                         re.sub(' +',' ',test_yaml_dump).strip())
    def test_function_subtype(self):
        test_yaml = \
'''
a: 2

partial_func: !PartialFunctionHandle
    module_name: "numpy"
    function_name: "sum"
    kwargs: 
        axis: -1

func: !FunctionHandle
    module_name: "numpy"
    function_name: "sum"
    
b: 3
'''

        test_read = yaml_interface.yaml_load(test_yaml)
        sum_axis = test_read['partial_func'](np.array([[1,2,3],[4,5,6]]))
        np.testing.assert_array_equal(sum_axis,[6,15])
        sum_no_axis= test_read['func'](np.array([[1,2,3],[4,5,6]]))
        np.testing.assert_array_equal(sum_no_axis,[21])


    def test_function_subtype_print(self):
        s = np.sum
        func_hand = FunctionHandle.init_from_function_handle(s)
        part_func = PartialFunctionHandle.init_from_function_handle(s, axis=-1)
        dict_out = {'func': func_hand, 'partial_func': part_func}
        str_out = yaml_interface.yaml_dumps(dict_out)
        loaded_obj = yaml_interface.yaml_load(str_out)
        self.assertEqual(loaded_obj['func'],func_hand)
        self.assertEqual(loaded_obj['partial_func'],part_func)
        #print(str_out)

    def test_class_subtype(self):
        A = TestYamlPostinit(test_type1=24,test_type2=25)
        B = yaml_sci_config.interface_classes.PartialClassObject.init_from_class(TestYamlPostinit, test_type1=24)
        str_out = yaml_interface.yaml_dumps({'B':B})
        loaded_obj = yaml_interface.yaml_load(str_out)
        assert not loaded_obj['B'].args
        loaded_obj['B'].args =  tuple()
        self.assertEqual(loaded_obj['B'],B)
        a_clone = loaded_obj['B'](test_type2=25)
        self.assertEqual(A,a_clone)

    def test_numeric_parse(self):
        yaml_str = \
        '''\
        list_elem: [2,3, 36]
        np_arr_explicit: np.array([2, 3, 26])
        complex_val: 5+2.3i
        np_complex_arr: np.array([2,3,2e4+5j])
        other_var: !FunctionHandle
            module_name: "numpy"
            function_name: "sum"
        '''

        loaded = yaml_interface.yaml_load(yaml_str)
        assert (loaded['list_elem'] ==[2,3, 36])
        np.testing.assert_array_almost_equal(loaded['np_arr_explicit'],np.array([2,3,26]))
        assert (loaded['complex_val'] == (5+2.3j))
        np.testing.assert_array_almost_equal(loaded['np_complex_arr'],np.array([2,3,2e4+5j]))



if __name__ == '__main__':
    unittest.main()
