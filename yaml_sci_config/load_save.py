import argparse

import ruamel.yaml
from ruamel.yaml import CommentedMap

from yaml_sci_config.interface_classes import RunInfoParams, IOParams
from yaml_sci_config.yaml_interface import yaml_preset, setup_yaml, custom_types
import os

def parse_args_cli(parser=None):
    '''
    Adds functionality to a file, to read in parameters from a yaml file.
    Adds requirement to file, that it is executed with either "-y FNAME" or "--yaml_fname FNAME,"
        where FNAME is the name of the YAML parameter file where parameters are stored
    :return: params_yml: the native output of PYYAML after
            args: list of all arguments provided to the script
    '''
    if parser is None: parser = argparse.ArgumentParser()

    parser.add_argument('-y','--yaml_fname',required=True)
    args = parser.parse_args()
    params_yml = yaml_load_fname(args.yaml_fname)
    return params_yml,args


def get_run_info(yaml_fname)->RunInfoParams:
    return RunInfoParams(yaml_fname)


def save_config(params_yml,io_params:IOParams,run_info:RunInfoParams):
    if not isinstance(params_yml,(dict,CommentedMap)):
        raise TypeError('params_yml must be mappable')
    out_params = params_yml.copy()
    out_params['run_info'] = run_info
    out_params['io_params'] = io_params
    out_dir = io_params.out_dir
    prefix = io_params.prefix
    save_filename = '{}_{}_params.yaml'.format(prefix, run_info.time_exec.strftime('%Y-%m-%d_%H%M%S'))
    out_fname = os.path.join(out_dir, save_filename)
    yaml_save_fname(out_params,out_fname)

def yaml_load_fname(fname):
    with open(fname,'r') as filep:
        par_obj = yaml_load(filep)
    return par_obj


def yaml_save_fname(yaml_obj,fname):
    with open(fname,'w') as fout:
        yaml_dump(yaml_obj,fout)


def yaml_load(fin,yaml = yaml_preset, custom_setup=True):
    '''
    A convenient wrapper around yaml.load().
    Note that fin, just as for yaml.load(), accepts strings as well as file objects.
    Assumes globally setup yaml is used.
    If we want to start from scratch and configure new YAML instance,
        we set yaml=None. custom_setup
        then will setup yaml to deal with custom types
    '''
    if yaml is None: # note: not default.
        yaml = ruamel.yaml.YAML(typ='rt')
        if custom_setup:
            setup_yaml(yaml, custom_types)
        #TODO: register the extra classes too.
    return yaml.load(fin)


def yaml_dump(obj,fout, yaml= yaml_preset,custom_setup=True):
    '''
    Assumes globally setup yaml is used.
    If we want to start from scratch and configure new YAML instance,
        we set yaml=None. custom_setup
        then will setup yaml to deal with custom types
    '''
    if yaml is None: # note: not default.
        yaml = ruamel.yaml.YAML(typ='rt')
    if custom_setup:
        setup_yaml(yaml, custom_types)
    return yaml.dump(obj,fout)


def yaml_dumps(obj,options=None):
    '''
    Dump yaml into a string instead of a file object
    '''
    if options == None: options = {}

    from io import StringIO
    string_stream = StringIO()
    yaml_preset.dump(obj, string_stream, **options)
    output_str = string_stream.getvalue()
    string_stream.close()
    return output_str
