import argparse
import importlib
import logging
import logging.config
import os
import pickle

from dataclasses import asdict
from functools import partial
from io import BytesIO, StringIO
from typing import Any, Optional

import hydra
import yaml

from hydra import compose, initialize
from hydra.types import TaskFunction
from omegaconf import DictConfig, OmegaConf

from cybulde.config_schemas import data_processing_config_schema
from cybulde.utils.io_utils import open_file


def get_config(config_path: str, config_name: str) -> TaskFunction:
    setup_config()
    setup_logger()

    def main_decorator(task_function: TaskFunction) -> Any:
        @hydra.main(config_path=config_path, config_name=config_name, version_base=None)
        def decorated_main(dict_config: Optional[DictConfig] = None) -> Any:
            config = OmegaConf.to_object(dict_config)
            return task_function(config)

        return decorated_main

    return main_decorator

# Is similar to the get_config() function, but instead of creating a new config, it will load the automatically generated configs.
def get_pickle_config(config_path: str, config_name: str) -> TaskFunction:
    setup_config()
    setup_logger()

    def main_decorator(task_function: TaskFunction) -> Any:
        def decorated_main() -> Any:
            config = load_pickle_config(config_path, config_name)
            return task_function(config)

        return decorated_main

    return main_decorator

def load_pickle_config(config_path: str, config_name: str) -> Any:
    with open_file(os.path.join(config_path, f"{config_name}.pickle"), "rb") as f:
        config = pickle.load(f)
    return config

def setup_config() -> None:
    data_processing_config_schema.setup_config()


def setup_logger() -> None:
    with open("./cybulde/configs/hydra/job_logging/custom.yaml", "r") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)


def config_args_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--config-path", type=str, default="../configs/", help="Directory of the config files")
    parser.add_argument("--config-name", type=str, required=True, help="Name of the config file")
    parser.add_argument("--overrides", nargs="*", help="Hydra config overrides", default=[])

    return parser.parse_args()


def compose_config(config_path: str, config_name: str, overrides: Optional[list[str]] = None) -> Any:
    setup_config()
    setup_logger()

    if overrides is None:
        overrides = []

    with initialize(version_base=None, config_path=config_path, job_name="config_compose"): # job_name can be any name
        dict_config = compose(config_name=config_name, overrides=overrides)
        config = OmegaConf.to_object(dict_config)
    return config


# For that function we will create another function to load and save files.
# Even Python having a function for this, this new function will allow us to save files on our local disk or on the cloud.
# cybulde/utils/io_utils.py
def save_config_as_yaml(config: Any, save_path: str) -> None:
    # Define a StringIO()
    text_io = StringIO()
    # Use OmegaConf to save config to our text_io
    #   resolve = True -> All of the reference parameters will be resolved before we save ou .yaml file
    OmegaConf.save(config, text_io, resolve=True)
    with open_file(save_path, "w") as f:
        f.write(text_io.getvalue())


def save_config_as_pickle(config: Any, save_path: str) -> None:
    # Define a BytesIO()
    bytes_io = BytesIO()
    # Use pickle to save config to our bytes_io
    pickle.dump(config, bytes_io)
    with open_file(save_path, "wb") as f:
        f.write(bytes_io.getvalue())