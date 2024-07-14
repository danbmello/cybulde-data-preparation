# Creating 4 functions on cybulde/utils/config_utils.py
#   - config_arg_parser() -> Argument parser to parse some arguments from command line.
#   - compose_config() -> Hydra function to compose your config.
#   - save_config_as_yaml() -> Save config file as .yaml
#   - save_config_as_pickle() -> Save config file as .pickle


import argparse
from pathlib import Path

from cybulde.utils.config_utils import compose_config, config_args_parser, save_config_as_yaml, save_config_as_pickle



def generate_final_config(args: argparse.Namespace) -> None:
    config_path = args.config_path
    config_name = args.config_name
    overrides = args.overrides

    config = compose_config(config_path=config_path, config_name=config_name, overrides=overrides)

    # Save config file into disk

    # Define directory path
    config_save_dir = Path("./cybulde/configs/automatically_generated")
    # Creates the directory
    config_save_dir.mkdir(parents=True, exist_ok=True)
    # Save file as .yaml and .pickle
    save_config_as_yaml(config, str(config_save_dir / f"{config_name}.yaml"))
    save_config_as_pickle(config, str(config_save_dir / f"{config_name}.pickle"))




if __name__ == "__main__":
    generate_final_config(config_args_parser())
