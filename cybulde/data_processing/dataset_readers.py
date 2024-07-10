import os

from abc import ABC, abstractmethod
from typing import Optional

import dask.dataframe as dd

from dask_ml.model_selection import train_test_split

from cybulde.utils.utils import get_logger


# Abstract base class in order to have some schma defined for our datase readers
class DatasetReader(ABC):
    # Columns our final df must have.
    required_columns = {"text", "label", "split", "dataset_name"}
    split_names = {"train", "dev", "test"}

    def __init__(self, dataset_dir: str, dataset_name: str) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.dataset_dir = dataset_dir
        self.dataset_name = dataset_name

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
            return train_test_split(df, test_size=test_size, random_state=1234, shuffle=True)
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


class GHCDatasetReader(DatasetReader):
    # As GHC doesn't have dev_df, we will split train_df. For that we need another parameter dev_split_ratio
    def __init__(self, dataset_dir: str, dataset_name: str, dev_split_ratio: float) -> None:
        # Call __init__ method of the parent class
        super().__init__(dataset_dir, dataset_name)
        self.dev_split_ratio = dev_split_ratio

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        # Read ghc_train.tsv
        train_tsv_path = os.path.join(self.dataset_dir, "ghc_train.tsv")
        train_df = dd.read_csv(train_tsv_path, sep="\t", header=0)
        # Read ghc_test.tsv
        test_tsv_path = os.path.join(self.dataset_dir, "ghc_test.tsv")
        test_df = dd.read_csv(test_tsv_path, sep="\t", header=0)

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
    def __init__(self, dataset_dir: str, dataset_name: str, dev_split_ratio: float) -> None:
        # Call __init__ method of the parent class
        super().__init__(dataset_dir, dataset_name)
        self.dev_split_ratio = dev_split_ratio
        self.columns_for_label = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        # Join test data with its labels.
        test_csv_path = os.path.join(self.dataset_dir, "test.csv")
        test_df = dd.read_csv(test_csv_path)

        test_labels_csv_path = os.path.join(self.dataset_dir, "test_labels.csv")
        test_labels_df = dd.read_csv(test_labels_csv_path)

        test_df = test_df.merge(test_labels_df, on=["id"])

        # Deleting -1 rows
        test_df = test_df[test_df["toxic"] != -1]

        test_df = self.get_text_and_label_columns(test_df)

        train_csv_path = os.path.join(self.dataset_dir, "train.csv")
        train_df = dd.read_csv(train_csv_path)
        train_df = self.get_text_and_label_columns(train_df)
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
    def __init__(self, dataset_dir: str, dataset_name: str, test_split_ratio: float, dev_split_ratio: float) -> None:
        # Call __init__ method of the parent class
        super().__init__(dataset_dir, dataset_name)
        self.test_split_ratio = test_split_ratio
        self.dev_split_ratio = dev_split_ratio

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        df_csv_path = os.path.join(self.dataset_dir, "cyberbullying_tweets.csv")
        df = dd.read_csv(df_csv_path)
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
    def __init__(self, dataset_readers: dict[str, DatasetReader]) -> None:
        self.dataset_readers = dataset_readers

    def read_data(self) -> dd.core.DataFrame:
        dfs = [dataset_reader.read_data() for dataset_reader in self.dataset_readers.values()]
        df: dd.core.DataFrame = dd.concat(dfs)
        return df
