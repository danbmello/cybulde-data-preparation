from cybulde.config_schemas.config_schema import Config
from cybulde.utils.config_utils import get_config
from cybulde.utils.gcp_utils import access_secret_version
from cybulde.utils.data_utils import get_raw_data_with_version, get_cmd_to_get_raw_data

@get_config(config_path="../configs", config_name="config")
def process_data(config: Config) -> None:
    # Later we will set up a config.yaml file, but for now we will just hardcode the parameters values.
    version = "v11"
    data_local_save_dir = "./data/raw"
    dvc_remote_repo = "https://github.com/danbmello/cybulde-data.git"
    dvc_data_folder = "data/raw"
    github_user_name = "danbmello"
    github_access_token = access_secret_version("cybulde-428517","cybulde-data-github-access-token")

    get_raw_data_with_version(
        version=version,
        data_local_save_dir=data_local_save_dir,
        dvc_remote_repo=dvc_remote_repo,
        dvc_data_folder=dvc_data_folder,
        github_user_name=github_user_name,
        github_access_token=github_access_token
    )


if __name__ == "__main__":
    process_data()


