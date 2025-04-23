
from dataclasses import _MISSING_TYPE

#import pinn_gencases.utils.domains_interface import yaml_classes

#import pinn_gencases.utils.domains_interface, pinn_gencases.utils.var_form_interface
from ruamel.yaml import RoundTripConstructor
import argparse
#from pinn_gencases.interface.general_interface import YAML_struct
import inspect


from dataclasses import dataclass, field, is_dataclass
from typing import Callable, Any
import datetime
import sys

import numpy as np
import ruamel.yaml

from custom_num_parse import my_construct_yaml_object, custom_types, setup_yaml

from typing import get_type_hints


yaml_preset = ruamel.yaml.YAML(typ='rt')

# The following code fragment is based on work from the following stackoverflow post:
# https://web.archive.org/web/20221228150343/https://stackoverflow.com/questions/73749807/implicit-resolvers-and-robust-representers-for-human-friendly-tuple-and-np-array

import importlib

from nptyping import NDArray
from functools import partial
from copy import deepcopy
from inspect import isclass

## Following code is for correcting deficiency in ruamel.yaml


#RoundTripConstructor.org_construct_yaml_object = RoundTripConstructor.construct_yaml_object
#RoundTripConstructor.construct_yaml_object = my_construct_yaml_object


# def _tuple_constructor(self, node):
#    return eval(self.construct_scalar(node))


# def collect_yaml_classes(module_names = interface_mods):
#     module_list = []
#     for module_name in module_names:
#         if  inspect.ismodule(module_name):
#             module_list.append(module_name)
#         else:
#             try: # try to import the module and add it to the list.
#                 module_list.append(importlib.import_module(module_name))
#             except ModuleNotFoundError:
#                 Warning('The Interface file ({}) was not found'.format(module_name))
#
#     yaml_class_list = []
#     for module in module_list:
#         yaml_class_list.extend(find_yaml_classes_mod(module))
#     return yaml_class_list


 


#def register_yaml_classes(yaml,classes_register):
#    for class_reg in classes_register:
#        yaml.register_class(class_reg)

def yaml_load_fname(fname):
    with open(fname,'r') as filep:
        par_obj = yaml_load(filep)
    return par_obj


def yaml_save_fname(yaml_obj,fname):
    with open(fname,'w') as fout:
        yaml_dump(yaml_obj,fout)


def yaml_load(fin,yaml = yaml_preset, custom_setup=True):
    '''
    Assumes globally setup yaml is used. 
    If we want to start from scratch and configure new YAML instance,
        we set yaml=None. custom_setup 
        then will setup yaml to deal with custom types
    '''
    if yaml is None:
        yaml = ruamel.yaml.YAML(typ='rt')
    if custom_setup:
        setup_yaml(yaml, custom_types)
    return yaml.load(fin)


def yaml_dump(obj,fout, yaml= yaml_preset,custom_setup=True):
    '''
    Assumes globally setup yaml is used. 
    If we want to start from scratch and configure new YAML instance,
        we set yaml=None. custom_setup 
        then will setup yaml to deal with custom types
    '''
    if yaml is None:
        yaml = ruamel.yaml.YAML(typ='rt')
    if custom_setup:
        setup_yaml(yaml, custom_types)
    return yaml.dump(obj,fout)

def yaml_dumps(obj,options=None):
    if options == None: options = {}

    from io import StringIO
    string_stream = StringIO()
    yaml_preset.dump(obj, string_stream, **options)
    output_str = string_stream.getvalue()
    string_stream.close()
    return output_str



def parse_args_cli():
    '''
    Adds functionality to a file, to read in parameters from a yaml file.
    Adds requirement to file, that it is executed with either "-y FNAME" or "--yaml_fname FNAME,"
        where FNAME is the name of the YAML parameter file where parameters are stored
    :return: params_yml: the native output of PYYAML after
            args: list of all arguments provided to the script
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-y','--yaml_fname',required=True)
    args = parser.parse_args()
    params_yml = yaml_load_fname(args.yaml_fname)
    return params_yml,args


def yaml_dataclass(cls=None, yaml=yaml_preset, **dataclass_kwargs):
    def wrapper(cls):
        type_hints = get_type_hints(cls)
        if not is_dataclass(cls) or any(name not in cls.__dataclass_fields__ for name in type_hints):
            cls = dataclass(cls, **dataclass_kwargs)
        yaml.register_class(cls)
        return cls

    return wrapper if cls is None else wrapper(cls)


class YAML_struct:
    pass

class YAML_struct_old:
    '''
    An object that will be read in with the YAML interface.
    This object helpfully gives itself an attribute called "yaml_tag"
    which is the same as the class name, prepended by an exclamation point.
    '''

    def __init_subclass__(cls) -> None:
        tag = f"!{cls.__name__}"
        yaml_preset.register_class(cls)
        yaml_preset.constructor.add_constructor(tag, my_construct_yaml_object)
        cls.yaml_tag = tag  # Save for internal use if needed

#    @classmethod
#    def to_yaml(cls, representer, data):
#        return representer.represent_mapping(f'!{cls.__name__}', data.__dict__)

#    @classmethod
#    def from_yaml(cls, constructor, node):
#        values = constructor.construct_mapping(node, deep=True)
#        return cls(**values)
@yaml_dataclass
class FunctionHandle:
    '''
    A Class which allows one to read in a function with yaml and special arguments and keyword arguments.

    Gives a convenient method for reading and writing from files.
    Additionally, the function may be called as if it were a normal function.

    Example:
    f = FunctionHandle(module_name = 'numpy',
                        class_name= 'log10')

    f(100) == 2
    '''
    module_name: str  # The module inside of which the function is defined
    function_name: str  # The name of the function inside of the module.
    _fn_hand: Callable = None

    def __post_init__(self) -> None:
        self._fn_hand = self.get_function_handle()

    def to_function_handle(self) -> Callable:
        return self._fn_hand

    def get_function_handle(self) -> Callable:
        module = importlib.import_module(self.module_name)
        try:
            fn = getattr(module, self.function_name)
            if not callable(fn):
                raise ValueError(
                    'The function given: (module: {.module_name}, function: {.function_name}) is not callable'.format(
                        self, self))

        except AttributeError:
            fn = None
            warnings.warn('{.function_name} not found in module {.module_name}'.format(self, self))

        return fn

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self._fn_hand is not None:
            return self._fn_hand(*args, **kwds)
        else:
            raise RuntimeError('No Function assigned to FunctionHandle. '
                               'Check warnings to see which function was not found.')

    @classmethod
    def init_from_function_handle(cls, fn_handle):
        assert (callable(fn_handle))  # did we give this a function?

        module_name = fn_handle.__module__
        function_name = fn_handle.__name__
        return cls(module_name=module_name, function_name=function_name)

    def __getstate__(self):
        # Added for yaml representation to ignore certain information.
        # See https://web.archive.org/web/20230117100148/https://stackoverflow.com/questions/49905287/how-to-ignore-attributes-when-using-yaml-dump
        state = self.__dict__.copy()
        try:
            del state['_fn_hand']
        except:
            pass
        return state

    def __deepcopy__(self, memo):
        # In case you need to perform a deepcopy.  Note that getstate is ignored and instead we copy all items.
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    # def check_equal(self,other):
    #     def print_ne():
    #         warnings.warn('arg: {}, LHS: {},RHS:{}'.format(var,val,other_vars[var]))
    #     if not isinstance(other, FunctionHandle):
    #         return False
    #     other_vars = other.__getstate__()
    #     for var,val in self.__getstate__().items():
    #         if isinstance(other[val],(FunctionHandle)):
    #             if not val.check_equal(other_vars[var]):
    #                 print_ne(); return False
    #         elif isinstance(val,np.ndarray):
    #             if not np.array_equiv(val,other_vars[var]):
    #                 print_ne();return False
    #         else:
    #             try:
    #                 if not val == other_vars[var]:
    #                     print_ne();return False
    #             except ValueError:
    #                 # maybe its a sequence. Last ditch effort
    #                 if not np.array_equiv(np.array(val),np.array(other_vars[var])):
    #                     print_ne(); return False


@yaml_dataclass
class PartialFunctionHandle(FunctionHandle):
    '''
    A Class which allows one to read in a function with yaml and special arguments and keyword arguments.

    The argument and keyword argument are analogous to Python's functools.partial()

    For example,
    frac_part = PartialFunctionHandle(module_name='numpy',
                          func_name= 'mod'
                          kwargs = {'x2':1} )

    could be used to represent a function handle which the fractional part of a positive number x:
    (by computing the number x mod 1)

    frac_part(2.4) == 0.4
    '''

    kwargs: dict = field(default_factory=dict)  #
    args: list = field(default_factory=list)  #

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return super().__call__(*args, *self.args, **kwds, **self.kwargs)

    @classmethod
    def init_from_function_handle(cls, fn_handle, *args, **kwargs):
        if kwargs is None:
            kwargs = {}
        FnHand = super().init_from_function_handle(fn_handle)
        FnHand.args = args
        FnHand.kwargs = kwargs
        return FnHand

    def to_function_handle(self) -> Callable:
        return partial(self._fn_hand, *self.args, **self.kwargs)


@yaml_dataclass
class ClassObject:
    '''
        A Class which allows one to read in an abitrary class with yaml and special arguments and keyword arguments.

        The argument and keyword argument are analogous to Python's functools.partial()

        For example,
        frac_part = PartialFunctionHandle(module_name='numpy',
                              func_name= 'mod'
                              kwargs = {'x2':1} )

        could be used to represent a function handle which the fractional part of a positive number x:
        (by computing the number x mod 1)

        frac_part(2.4) == 0.4
    '''
    module_name: str  # The module inside of which the function is defined
    class_name: str  # The name of the function inside of the module.

    def __post_init__(self) -> None:
        self._cls = self.get_class_obj()

    def to_class(self) -> Callable:
        return self._cls

    def get_class_obj(self) -> Callable:
        module = importlib.import_module(self.module_name)
        try:
            cls = getattr(module, self.class_name)
            if not isclass(cls):
                raise ValueError(
                    'The class given: (module: {.module_name}, class: {.function_name}) does not seem to be a class'.format(
                        self, self))
            return cls
        except AttributeError:
            raise NameError('Class {.function_name} not found in module {.module_name}'.format(self, self))

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self._cls(*args, **kwds)  # return instance of the class with relevant arguments.

    @classmethod
    def init_from_class(cls, class_passed):
        assert (isclass(class_passed))  # did we give this a function?

        module_name = class_passed.__module__
        class_name = class_passed.__name__
        return cls(module_name=module_name, class_name=class_name)

    def __getstate__(self):
        # Added for yaml representation to ignore certain information.
        # See https://web.archive.org/web/20230117100148/https://stackoverflow.com/questions/49905287/how-to-ignore-attributes-when-using-yaml-dump
        state = self.__dict__.copy()
        del state['_cls']
        return state

    def __deepcopy__(self, memo):
        # In case you need to perform a deepcopy.  Note that getstate is ignored and instead we copy all items.
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result


@yaml_dataclass
class PartialClassObject(ClassObject):
    '''
    A Class which allows one to read in an abitrary object with yaml and special arguments and keyword arguments.

    The argument and keyword argument are analogous to Python's functools.partial()

    For example,
    frac_part = PartialFunctionHandle(module_name='numpy',
                          func_name= 'mod'
                          kwargs = {'x2':1} )

    could be used to represent a function handle which the fractional part of a positive number x:
    (by computing the number x mod 1)

    frac_part(2.4) == 0.4
    '''

    kwargs: dict = field(default_factory=dict)  #
    args: list = field(default_factory=list)  #

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return super().__call__(*args, *self.args, **kwds, **self.kwargs)

    @classmethod
    def init_from_class(cls, class_given, *args, **kwargs):
        if kwargs is None:
            kwargs = {}
        ClsObj = super().init_from_class(class_given)
        ClsObj.args = args
        ClsObj.kwargs = kwargs
        return ClsObj

    def to_class(self) -> Callable:
        raise NotImplementedError('This method has not been implemented because the extra calling '
                                  'arguments change signature of __init__.')
        # return partial(self._fn_hand, *self.args, **self.kwargs)


@yaml_dataclass
class RunInfoParams:
    in_file: str  # path to parameter file that ran this.
    exec_file: str = None  # file that ran the code.
    time_exec: datetime.datetime = None

    def __init__(self, in_file, time_exec=None, exec_file=None):
        if time_exec is None:
            self.time_exec = datetime.datetime.now()
        elif isinstance(self.time_exec, str):
            self.time_exec = datetime.datetime.strptime(time_exec, '%Y-%m-%d %H:%M:%S.%f')

        if exec_file is None:
            self.exec_file = sys.argv[0]

        self.in_file = in_file


@yaml_dataclass
class IOParams:
    '''
    Simple struct which stores output parameters.

    :param out_dir: str
      directory where everything will be saved.
    :param prefix: str
      everything output by this program will have this common prefix added in its filename.
    '''
    out_dir: str
    prefix: str


@yaml_dataclass
class ArrayParams:
    def to_np_array(self):
        raise (NotImplementedError('Abstract Class has no method'))


@yaml_dataclass
class ArbitraryNpArray(ArrayParams):
    arr: list

    def __post_init__(self):
        try:
            arr = np.array(self.arr)
        except:
            raise (ValueError('Input {} is not valid for a numpy array'.format(arr)))

    def to_np_array(self):
        return np.array(self.arr)


@yaml_dataclass
class LogspaceParams(ArrayParams):
    '''
    Class which is helpful for creating a logspace grid.
    Contains a .to_np_array() method for generating the numpy array.

    :param log_start: (float) log10 of where we want to start in our logspace grid
    :param log_stop: (float) log10 of where we want to stop
    :param n_logspace: (int) number of points
      we want in the logarithmically spaced grid.
    '''

    log_start: float
    log_stop: float
    n_logspace: int

    def __post_init__(self):
        assert (self.log_start < self.log_stop)
        assert (self.n_logspace > 0 and self.n_logspace == int(self.n_logspace))

    def to_np_array(self):
        return np.logspace(self.log_start, self.log_stop, self.n_logspace)


@yaml_dataclass
class LinspaceParams(ArrayParams):
    '''
    Class which is helpful for creating a logspace grid.
    Contains a .to_np_array() method for generating the numpy array.

    :param log_start: (float) log10 of where we want to start in our logspace grid
    :param log_stop: (float) log10 of where we want to stop
    :param n_logspace: (int) number of points
      we want in the logarithmically spaced grid.
    '''

    lin_start: float
    lin_stop: float
    n_linspace: int

    def __post_init__(self):
        # assert(self.log_start < self.log_stop)
        assert (self.n_linspace > 0 and self.n_linspace == int(self.n_linspace))

    def to_np_array(self):
        return np.linspace(self.lin_start, self.lin_stop, self.n_linspace)

#classes_register = collect_yaml_classes()
setup_yaml(yaml_preset, custom_types)
