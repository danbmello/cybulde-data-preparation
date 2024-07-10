from shutil import rmtree

from utils.utils import run_shell_command


def get_cmd_to_get_raw_data(
    version: str,
    data_local_save_dir: str,
    dvc_remote_repo: str,
    dvc_data_folder: str,
    github_user_name: str,
    github_access_token: str,
) -> str:
    """
    Get shell

    Parameters
    ----------
    version: str
        Data version
    data_local_save_dir: str
        Where to save the downloaded data locally
    dvc_remote_repo: str
        DVC repository that holds information about the data
    dvc_data_folder: str
        Location where the remote data is stored
    github_user_name: str
        GitHub user name
    github_access_token: str
        GitHub access token

    Returns
    -------
    str
        Shell command to download the raw data from DVC store.
    """

    # We have this
    #   https://github.com/danbmello/
    # We want this:
    #   https://<username>:<access_token>@github.com/danbmello/cybulde-data-preparation.git
    without_https = dvc_remote_repo.replace("https://", "")
    dvc_remote_repo = f"https://{github_user_name}:{github_access_token}@{without_https}"

    command = f"dvc get {dvc_remote_repo} {dvc_data_folder} --rev {version} -o {data_local_save_dir}"

    return command


def get_raw_data_with_version(
    version: str,
    data_local_save_dir: str,
    dvc_remote_repo: str,
    dvc_data_folder: str,
    github_user_name: str,
    github_access_token: str,
) -> None:
    # Remove data_local_save_dir if exists.
    # That's because we don't want to mix the version we want to download with the existing one.
    rmtree(data_local_save_dir, ignore_errors=True)

    command = get_cmd_to_get_raw_data(
        version, data_local_save_dir, dvc_remote_repo, dvc_data_folder, github_user_name, github_access_token
    )
    run_shell_command(command)
