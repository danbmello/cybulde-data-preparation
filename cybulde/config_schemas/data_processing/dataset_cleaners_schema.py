import string

from dataclasses import field

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING
from pydantic.dataclasses import dataclass


@dataclass
class SpellCorrectionModelConfig:
    _target_: str = "cybulde.utils.utils.SpellCorrectionModel"
    max_dictionary_edit_distance: int = 2
    prefix_length: int = 7
    count_threshold: int = 1


@dataclass
class DatasetCleanerConfig:
    _target_: str = MISSING


@dataclass
class StopWordsDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.StopWordsDatasetCleaner"


@dataclass
class ToLowerCaseDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.ToLowerCaseDatasetCleaner"


@dataclass
class URLDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.URLDatasetCleaner"


@dataclass
class PunctuationDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.PunctuationDatasetCleaner"
    punctuation: str = string.punctuation


@dataclass
class NonLettersDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.NonLettersDatasetCleaner"


@dataclass
class NewLineCharacterDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.NewLineCharacterDatasetCleaner"


@dataclass
class NonASCIIDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.NonASCIIDatasetCleaner"


@dataclass
class ReferenceToAccountDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.ReferenceToAccountDatasetCleaner"


@dataclass
class ReTweetDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.ReTweetDatasetCleaner"


@dataclass
class SpellCorrectionDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.SpellCorrectionDatasetCleaner"
    spell_correction_model: SpellCorrectionModelConfig = SpellCorrectionModelConfig()


@dataclass
class CharacterLimiterDatasetCleanerConfig(DatasetCleanerConfig):
    _target_: str = "cybulde.data_processing.dataset_cleaners.CharacterLimiterDatasetCleaner"
    character_limit: int = 300


@dataclass
class DatasetCleanerManagerConfig:
    _target_: str = "cybulde.data_processing.dataset_cleaners.DatasetCleanerManager"
    dataset_cleaners: dict[str, DatasetCleanerConfig] = field(default_factory=lambda: {})


def setup_config() -> None:
    cs = ConfigStore.instance()
    cs.store(name="dataset_cleaner_manager_schema", node=DatasetCleanerManagerConfig, group="dataset_cleaner_manager")

    cs.store(
        name="stop_words_dataset_cleaner_schema",
        node=StopWordsDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="to_lower_case_dataset_cleaner_schema",
        node=ToLowerCaseDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="url_dataset_cleaner_schema", node=URLDatasetCleanerConfig, group="dataset_cleaner_manager/dataset_cleaner"
    )

    cs.store(
        name="punctuation_dataset_cleaner_schema",
        node=PunctuationDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="non_letters_dataset_cleaner_schema",
        node=NonLettersDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="new_line_character_dataset_cleaner_schema",
        node=NewLineCharacterDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="non_ascii_dataset_cleaner_schema",
        node=NonASCIIDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="reference_to_account_dataset_cleaner_schema",
        node=ReferenceToAccountDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="re_tweet_dataset_cleaner_schema",
        node=ReTweetDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="spell_correction_dataset_cleaner_schema",
        node=SpellCorrectionDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )

    cs.store(
        name="character_limiter_dataset_cleaner_schema",
        node=CharacterLimiterDatasetCleanerConfig,
        group="dataset_cleaner_manager/dataset_cleaner",
    )
