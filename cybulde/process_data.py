from hydra.utils import instantiate

from pathlib import Path
import os

from cybulde.utils.utils import get_logger
from cybulde.config_schemas.data_processing_config_schema import DataProcessingConfig
from cybulde.utils.config_utils import get_pickle_config
from cybulde.utils.data_utils import get_raw_data_with_version
from cybulde.utils.gcp_utils import access_secret_version
from cybulde.data_processing.dataset_cleaners import DatasetCleanerManager

from dask.distributed import Client
import dask.dataframe as dd


# map_partition() method will call process_raw_data() function for each of the partitions we have in our dataframe
# For each of the partitions, we will run this function in parallel
def process_raw_data(df_partition: dd.core.DataFrame, dataset_cleaner_manager: DatasetCleanerManager) -> dd.core.Series:
    return df_partition["text"].apply(dataset_cleaner_manager)


@get_pickle_config(config_path="cybulde/configs/automatically_generated", config_name="data_processing_config")
def process_data(config: DataProcessingConfig) -> None:
    # print("\n")
    # print(80 * "*")
    # print("\n")
    # from omegaconf import OmegaConf

    # print(OmegaConf.to_yaml(config))
    # return

    logger = get_logger(Path(__file__).name)
    logger.info("Processing raw data...")

    # Output save directory
    processed_data_save_dir = config.processed_data_save_dir

    cluster = instantiate(config.dask_cluster)
    client = Client(cluster)

    try:

        github_access_token = access_secret_version(config.infrastructure.project_id, config.github_access_token_secret_id)

        get_raw_data_with_version(
            version=config.version,
            data_local_save_dir=config.data_local_save_dir,
            dvc_remote_repo=config.dvc_remote_repo,
            dvc_data_folder=config.dvc_data_folder,
            github_user_name=config.github_user_name,
            github_access_token=github_access_token,
        )

        dataset_reader_manager = instantiate(config.dataset_reader_manager)
        dataset_cleaner_manager = instantiate(config.dataset_cleaner_manager)

        df = dataset_reader_manager.read_data(config.dask_cluster.n_workers)
        
        print(100*"#")
        print(f"{df.npartitions=}")
        print(100*"#")
        
        logger.info("Cleaning data...")
        # Parallelizing throughout each partition
        #   process_raw_data: the function each partition will execute
        #   dataset_cleaner_manager=: as a parameter to the function
        df = df.assign(cleaned_text=df.map_partitions(process_raw_data, dataset_cleaner_manager=dataset_cleaner_manager, meta=("text", "object")))
        df = df.compute()

        # Saving outputs (as parquet files)
        train_parquet_path = os.path.join(processed_data_save_dir, "train.parquet")
        dev_parquet_path = os.path.join(processed_data_save_dir, "dev.parquet")
        test_parquet_path = os.path.join(processed_data_save_dir, "test.parquet")
        
        df[df["split"] == "train"].to_parquet(train_parquet_path)
        df[df["split"] == "dev"].to_parquet(dev_parquet_path)
        df[df["split"] == "test"].to_parquet(test_parquet_path)

        logger.info("Data proccessing finished!")

    finally:
        logger.info("Closing dask client and cluster...")
        client.close()
        cluster.close()

if __name__ == "__main__":
    process_data()
