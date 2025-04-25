'''
small script that reads the example runfile given in the command line argument.


To run it, make sure the argument -y or --yaml_fname is called from the command line
python sample_run_config_script.py -y config.yaml.

In pycharm these arguments can be set by right-clicking on the run arrow and selecting
"Edit Run Configuration". Works for debug too.
'''
from yaml_sci_config.load_save import parse_args_cli, get_run_info,save_config
from yaml_sci_config.yaml_interface import yaml_dataclass
import os

@yaml_dataclass
class CustomScriptConfig:
    r: float

if __name__ == '__main__':
    params_yaml, args = parse_args_cli() # script must be called with argument -y or --yaml_fname. Other arguments
    run_info = get_run_info(args.yaml_fname)
    io_params = params_yaml['io_params']

    custom_config=params_yaml['script_config']
    print(f'file has run with radius {custom_config.r}')

    save_config(params_yaml, io_params, run_info)

