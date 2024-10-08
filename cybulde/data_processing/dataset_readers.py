import os

from abc import ABC, abstractmethod
from typing import Optional

import dask.dataframe as dd

from dask_ml.model_selection import train_test_split
from dvc.api import get_url

from cybulde.utils.data_utils import get_repo_address_with_access_token, repartition_dataframe
from cybulde.utils.utils import get_logger


# Abstract base class in order to have some schma defined for our datase readers
class DatasetReader(ABC):
    # Columns our final df must have.
    required_columns = {"text", "label", "split", "dataset_name"}
    split_names = {"train", "dev", "test"}

    def __init__(
        self,
        dataset_dir: str,
        dataset_name: str,
        gcp_project_id: str,
        gcp_github_access_token_secret_id: str,
        dvc_remote_repo: str,
        github_user_name: str,
        version: str,
    ) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.dataset_dir = dataset_dir
        self.dataset_name = dataset_name
        self.dvc_remote_repo = get_repo_address_with_access_token(
            gcp_project_id, gcp_github_access_token_secret_id, dvc_remote_repo, github_user_name
        )
        self.version = version

    def read_data(self) -> dd.core.DataFrame:
        self.logger.info(f"Reading {self.__class__.__name__}...")
        train_df, dev_df, test_df = self._read_data()
        df = self.assign_split_names_to_data_frames_and_merge(train_df, dev_df, test_df)
        df["dataset_name"] = self.dataset_name
        # Check if all required columns are present in the final df. If not raise ValueError
        if any(required_column not in df.columns.values for required_column in self.required_columns):
            raise ValueError(f"Dataset must contain all required columns: {self.required_columns}")
        # Check if split names are correct
        unique_split_names = set(df["split"].unique().compute().tolist())
        if unique_split_names != self.split_names:
            raise ValueError(f"Dataset must contain all required split names: {self.split_names}")
        final_df: dd.core.DataFrame = df[list(self.required_columns)]
        return final_df

    # @abstractmethod means that each class that inherits from DatasetReader class will have to define _read_data() method.
    @abstractmethod
    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        """
        Read and split into 3 splits: train, dev, test.
        The return value must be a dd.core.DataFrame, with required columns: self.required_columns
        """

    def assign_split_names_to_data_frames_and_merge(
        self, train_df: dd.core.DataFrame, dev_df: dd.core.DataFrame, test_df: dd.core.DataFrame
    ) -> dd.core.DataFrame:
        train_df["split"] = "train"
        dev_df["split"] = "dev"
        test_df["split"] = "test"
        final_df: dd.core.DataFrame = dd.concat([train_df, dev_df, test_df])
        return final_df

    def split_dataset(
        self, df: dd.core.DataFrame, test_size: float, stratify_column: Optional[str] = None
    ) -> tuple[dd.core.DataFrame, dd.core.DataFrame]:
        if stratify_column is None:
            return train_test_split(df, test_size=test_size, random_state=1234, shuffle=True) # type: ignore
        unique_column_values = df[stratify_column].unique()
        first_dfs = []
        second_dfs = []
        for unique_set_values in unique_column_values:
            sub_df = df[df[stratify_column] == unique_set_values]
            sub_first_df, sub_second_df = train_test_split(sub_df, test_size=test_size, random_state=1234, shuffle=True)
            first_dfs.append(sub_first_df)
            second_dfs.append(sub_second_df)

        first_df = dd.concat(first_dfs)
        second_df = dd.concat(second_dfs)
        return first_df, second_df

    # Get the dataset url
    def get_remote_data_url(self, dataset_path: str) -> str:
        dataset_url: str = get_url(path=dataset_path, repo=self.dvc_remote_repo, rev=self.version)
        return dataset_url


class GHCDatasetReader(DatasetReader):
    # As GHC doesn't have dev_df, we will split train_df. For that we need another parameter dev_split_ratio
    def __init__(
        self,
        dataset_dir: str,
        dataset_name: str,
        dev_split_ratio: float,
        gcp_project_id: str,
        gcp_github_access_token_secret_id: str,
        dvc_remote_repo: str,
        github_user_name: str,
        version: str,
    ) -> None:
        super().__init__(
            dataset_dir,
            dataset_name,
            gcp_project_id,
            gcp_github_access_token_secret_id,
            dvc_remote_repo,
            github_user_name,
            version,
        )
        self.dev_split_ratio = dev_split_ratio

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        # ghc_train.tsv local path
        train_tsv_path = os.path.join(self.dataset_dir, "ghc_train.tsv")
        # ghc_train.tsv GCP path
        train_tsv_url = self.get_remote_data_url(train_tsv_path)
        # Read train local
        # train_df = dd.read_csv(train_tsv_path, sep="\t", header=0)
        # Read train GCP
        train_df = dd.read_csv(train_tsv_url, sep="\t", header=0)

        # Read ghc_test.tsv
        test_tsv_path = os.path.join(self.dataset_dir, "ghc_test.tsv")
        test_tsv_url = self.get_remote_data_url(test_tsv_path)

        # test_df = dd.read_csv(test_tsv_path, sep="\t", header=0)
        test_df = dd.read_csv(test_tsv_url, sep="\t", header=0)

        # As it will be a binary classification, we are going to sum train_df["hd"], train_df["cv"], train_df["vo"]
        # If 1 -> Cyberbullying, If 0 -> NO Cyberbullying
        train_df["label"] = (train_df["hd"] + train_df["cv"] + train_df["vo"]).astype(int)
        test_df["label"] = (test_df["hd"] + test_df["cv"] + test_df["vo"]).astype(int)

        # Split train_df in train_df and dev_df
        # We use stratify to maintain the 1's and 0's proportion
        train_df, dev_df = self.split_dataset(train_df, self.dev_split_ratio, stratify_column="label")

        return train_df, dev_df, test_df


class JigsawToxicCommentsDatasetReader(DatasetReader):
    # As JTC doesn't have dev_df, we will split train_df. For that we need another parameter dev_split_ratio
    def __init__(
        self,
        dataset_dir: str,
        dataset_name: str,
        dev_split_ratio: float,
        gcp_project_id: str,
        gcp_github_access_token_secret_id: str,
        dvc_remote_repo: str,
        github_user_name: str,
        version: str,
    ) -> None:
        super().__init__(
            dataset_dir,
            dataset_name,
            gcp_project_id,
            gcp_github_access_token_secret_id,
            dvc_remote_repo,
            github_user_name,
            version,
        )
        self.dev_split_ratio = dev_split_ratio
        self.columns_for_label = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        # Join test data with its labels.
        test_csv_path = os.path.join(self.dataset_dir, "test.csv")
        test_csv_url = self.get_remote_data_url(test_csv_path)

        # test_df = dd.read_csv(test_csv_path)
        test_df = dd.read_csv(test_csv_url)

        test_labels_csv_path = os.path.join(self.dataset_dir, "test_labels.csv")
        test_labels_csv_url = self.get_remote_data_url(test_labels_csv_path)

        # test_labels_df = dd.read_csv(test_labels_csv_path)
        test_labels_df = dd.read_csv(test_labels_csv_url)

        test_df = test_df.merge(test_labels_df, on=["id"])

        # Deleting -1 rows
        test_df = test_df[test_df["toxic"] != -1]

        test_df = self.get_text_and_label_columns(test_df)
        # The JTC test_df was to large, here we resized it to 10% and to_train_df will be concatenated with the final train_df
        to_train_df, test_df = self.split_dataset(test_df, 0.1, stratify_column="label")

        train_csv_path = os.path.join(self.dataset_dir, "train.csv")
        train_csv_url = self.get_remote_data_url(train_csv_path)

        # train_df = dd.read_csv(train_csv_path)
        train_df = dd.read_csv(train_csv_url)
        train_df = self.get_text_and_label_columns(train_df)
        train_df = dd.concat([train_df, to_train_df])

        # Split train_df into train_df and dev_df
        train_df, dev_df = self.split_dataset(train_df, self.dev_split_ratio, stratify_column="label")

        return train_df, dev_df, test_df

    def get_text_and_label_columns(self, df: dd.core.DataFrame) -> dd.core.DataFrame:
        # As it will be a binary classification, we are going to sum the classification columns
        # If 1 -> Cyberbullying, If 0 -> NO Cyberbullying
        df["label"] = (df[self.columns_for_label].sum(axis=1) > 0).astype(int)
        df = df.rename(columns={"comment_text": "text"})
        return df


class TwitterDatasetReader(DatasetReader):
    # As JTC doesn't have dev_df, we will split train_df. For that we need another parameter dev_split_ratio
    def __init__(
        self,
        dataset_dir: str,
        dataset_name: str,
        test_split_ratio: float,
        dev_split_ratio: float,
        gcp_project_id: str,
        gcp_github_access_token_secret_id: str,
        dvc_remote_repo: str,
        github_user_name: str,
        version: str,
    ) -> None:
        super().__init__(
            dataset_dir,
            dataset_name,
            gcp_project_id,
            gcp_github_access_token_secret_id,
            dvc_remote_repo,
            github_user_name,
            version,
        )
        self.test_split_ratio = test_split_ratio
        self.dev_split_ratio = dev_split_ratio

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        df_csv_path = os.path.join(self.dataset_dir, "cyberbullying_tweets.csv")
        df_csv_url = self.get_remote_data_url(df_csv_path)

        # df = dd.read_csv(df_csv_path)
        df = dd.read_csv(df_csv_url)

        df["label"] = (
            df["cyberbullying_type"]
            .apply(lambda x: 0 if x == "not_cyberbullying" else 1, meta=("label", "int"))
            .astype(int)
        )
        df = df.rename(columns={"tweet_text": "text"})
        # Spliting df into train_df and test_df
        train_df, test_df = self.split_dataset(df, self.test_split_ratio, stratify_column="label")
        # Spliting train_df into train_df and dev_df
        train_df, dev_df = self.split_dataset(train_df, self.dev_split_ratio, stratify_column="label")

        return train_df, dev_df, test_df


# *** MANAGER ***
class DatasetReaderManager:
    def __init__(
        self,
        dataset_readers: dict[str, DatasetReader],
        repartition: bool = True,
        available_memory: Optional[float] = None,
    ) -> None:
        self.dataset_readers = dataset_readers
        self.repartition = repartition
        self.available_memory = available_memory

    def read_data(self, nrof_workers: int) -> dd.core.DataFrame:
        dfs = [dataset_reader.read_data() for dataset_reader in self.dataset_readers.values()]
        df: dd.core.DataFrame = dd.concat(dfs)
        if self.repartition:
            df = repartition_dataframe(df, nrof_workers=nrof_workers, available_memory=self.available_memory)
        return df
