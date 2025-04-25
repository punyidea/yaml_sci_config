
import ruamel.yaml

yaml = ruamel.yaml.YAML()

#from pydantic import BaseModel

from dataclasses import dataclass, field,is_dataclass, fields, _MISSING_TYPE
from typing import get_type_hints



def yaml_dataclass(cls=None, yaml=yaml, **dataclass_kwargs):
    def wrapper(cls):
        type_hints = get_type_hints(cls)
        if not is_dataclass(cls) or any(name not in cls.__dataclass_fields__ for name in type_hints):
            cls = dataclass(cls, **dataclass_kwargs)
        yaml.register_class(cls)
        yaml.constructor.add_constructor(f'!{cls.__name__}', make_constructor(cls))
        return cls

    return wrapper if cls is None else wrapper(cls)


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


@dataclass
class SampleDataclass:
    this_field_works: str
    this_also_works: str = '25'
    this_now_works: dict = field(default_factory=dict)


yaml.register_class(SampleDataclass)
yaml.constructor.add_constructor('!SampleDataclass', make_constructor(SampleDataclass))


@yaml_dataclass
class AutoRegisterClass:
    this_field_works: str
    this_also_works: str = 'ye'
    this_now_works: dict = field(default_factory=dict)


test_yaml = \
    '''\
    a: !SampleDataclass
        this_field_works: "a"
    
    b: !AutoRegisterClass
        this_field_works: "a"
    '''

loaded = yaml.load(test_yaml)
print(loaded['b'].this_now_works)
print(loaded['a'].this_now_works)
