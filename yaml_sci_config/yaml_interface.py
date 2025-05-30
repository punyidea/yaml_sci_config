import re
from dataclasses import _MISSING_TYPE, fields
from ruamel.yaml.representer import TaggedScalar

import numpy as np
#import pinn_gencases.utils.domains_interface import yaml_classes

#import pinn_gencases.utils.domains_interface, pinn_gencases.utils.var_form_interface
#from pinn_gencases.interface.general_interface import YAML_struct


from dataclasses import dataclass, is_dataclass

import ruamel.yaml

from typing import get_type_hints

yaml_preset = ruamel.yaml.YAML(typ='rt')


def _complex_re_gen():
    '''
    Because it is complicated, returns a string which parses complex expressions.
    # Gave up and looked for complex number regular expression,
    #   modified to include scientific numbers.
    # See https://web.archive.org/web/20221228150825/https://stackoverflow.com/questions/67818976/regular-expression-for-complex-numbers
    '''
    num = r'(?:[+\-]?(?:\d*\.)?\d+)'
    num_sci = r'(?:{num}(?:e[+\-]?\d+)?)'.format(num=num)
    cx_num = r'(?:{num_sci}?{num_sci}[ij])'.format(num_sci=num_sci)
    cx_match_wrapped= r"^(?:{cx_num}|\({cx_num}\))$".format(cx_num=cx_num)
    return cx_match_wrapped



_tuple_re = r"^(?:\((?:.|\n|\r)*,(?:.|\n|\r)*\){1}(?: |\n|\r)*$)"
_array_re = r"^(?:(np\.|)array\(\[(?:.|\n|\r)*,(?:.|\n|\r)*\]\){1}(?: |\n|\r)*$)"
_complex_re= _complex_re_gen()


def make_constructor(cls):
    def constructor(loader: ruamel.yaml.Loader, node):
        '''
        Patch to include dataclasses fields with default factory.
        '''
        for data in loader.construct_yaml_object(node, cls):
            yield data
        # raw = loader.construct_mapping(node,maptyp=CommentedMap, deep=True)
        # init_kwargs = {}
        if is_dataclass(cls):
            # correct for ruamel.yaml not setting default fields with factories
            for field in fields(cls):
                try:
                    getattr(data, field.name)
                except AttributeError:
                    if not isinstance(field.default_factory, _MISSING_TYPE):
                        setattr(data, field.name, field.default_factory())
                        continue
                    raise (AttributeError(
                        'Unset dataclass field for dataclass of type {}: {}'.format(type(data), field.name)))

    return constructor




def _tuple_constructor_safe(self,node):
    yaml = ruamel.yaml.YAML(typ='safe')
    setup_yaml(yaml,custom_types)
    value = node.value
    value = re.sub("^\(","[",value)
    value = re.sub("\)$","]",value)
    #value = 'placeholder: '+value
    safe_l = yaml.load(value)#['placeholder']
    return tuple(safe_l)


def _complex_constructor(self,node):
    return complex(node.value.replace(' ', '').replace('i','j'))


def _array_constructor_safe(self,node):
    yaml = ruamel.yaml.YAML(typ='safe')
    setup_yaml(yaml,custom_types)
    value = node.value
    value = re.sub("^(?:np\.|)array\(","",value)
    value = re.sub("\)$","",value)
    #value = value.replace(',',', ')
    #value = re.sub(" +"," ",value)
    safe_l = yaml.load(value)
    return np.array(safe_l)


def _tuple_representer(dumper, data):
    repr = str(data)
    return dumper.represent_tagged_scalar(TaggedScalar(repr, style=None, tag='!tuple'))


def _complex_representer(dumper,data):
    repr = str(data)
    repr = re.sub("()","",repr)
    return dumper.represent_tagged_scalar(TaggedScalar(repr, style=None, tag='!complex'))


def _array_representer(dumper, data):
    repr = 'np.array(' + np.array2string(data, max_line_width=np.inf, precision=16, #prefix='np.array(',
                                         separator=', ', #suffix=')'
                                         ) + ')'
    repr = repr.replace(' ', '').replace(',', ', ')
    return dumper.represent_tagged_scalar(TaggedScalar(repr, style=None, tag='!nparray'))


def _complex_resolver(str_resolve,match_re = re.compile(r'[ij]')):
    '''
    For debugging. Sees if the complex constructor allows it.
    '''
    if re.search(match_re,str_resolve):
        try:
            cplx = complex(str_resolve.replace('i','j'))
            return cplx
        except ValueError:
            pass
    return None

custom_types = {
    '!tuple':   {'re':_tuple_re,   'constructor': _tuple_constructor_safe, 'representer': _tuple_representer, 'type': tuple, 'first':list('(')},
    '!nparray': {'re':_array_re,   'constructor': _array_constructor_safe, 'representer': _array_representer, 'type': np.ndarray, 'first':list('an')},
    '!complex': {'re':_complex_re,   'constructor': _complex_constructor, 'representer': _complex_representer, 'type': complex, 'first':None}
}

def yaml_add_custom_types(yaml,custom_types):
    for tag,ct in custom_types.items():
            yaml.Constructor.add_constructor(tag, ct['constructor'])
            yaml.Resolver.add_implicit_resolver(tag, ruamel.yaml.util.RegExp(ct['re']), ct['first'])
            yaml.Representer.add_representer(ct['type'], ct['representer'])


def setup_yaml(yaml,custom_types):
    #register_yaml_classes(yaml, classes_register)
    yaml_add_custom_types(yaml,custom_types)
    #yaml.default_flow_style = False




def register_yaml_classes(yaml,classes_register):
   for class_reg in classes_register:
       yaml.register_class(class_reg)


def yaml_dataclass(cls=None, yaml=yaml_preset, **dataclass_kwargs):
    def wrapper(cls):
        type_hints = get_type_hints(cls)
        if not is_dataclass(cls) or any(name not in cls.__dataclass_fields__ for name in type_hints):
            cls = dataclass(cls, **dataclass_kwargs)
        yaml.register_class(cls)
        yaml.constructor.add_constructor(f'!{cls.__name__}', make_constructor(cls))
        return cls

    return wrapper if cls is None else wrapper(cls)



setup_yaml(yaml_preset,custom_types)

#classes_register = collect_yaml_classes()
