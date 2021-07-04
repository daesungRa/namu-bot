"""
Provide config object created based on yaml file info.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
import yaml

from pathlib import Path

LOGGER = logging.getLogger(__name__)


class Config:
    def __init__(self, config_file: Path):
        self._config = self._load_config(config_file)
        self._sample_config = self._load_config(
            config_file.with_suffix(f'{config_file.suffix}.sample'))

        assert self._check_version(self._config, self._sample_config)

    @staticmethod
    def _check_version(config, sample_config) -> bool:
        check_result = False
        LOGGER.info(f'Check version between config and sample_config... -> {config}')
        conf_version = config.get('VERSION', 'undefined')
        conf_smpl_version = sample_config.get('VERSION', 'undefined')
        if conf_version == conf_smpl_version:
            check_result = True
        LOGGER.info(f'{conf_version} vs {conf_smpl_version} -> {check_result}')
        return check_result

    @staticmethod
    def _load_config(config_file: Path) -> dict:
        if config_file.exists():
            LOGGER.info(f'Load config file... -> {config_file}')
            with config_file.open(encoding='utf-8') as f:
                try:
                    config = yaml.safe_load(f)
                except yaml.YAMLError as ye:
                    LOGGER.error(f'[CONFIG-ERROR][YAMLError] {config_file}')
                    raise yaml.YAMLError(f'[FILE-PATH] {config_file}') from ye
        else:
            LOGGER.error(f'[CONFIG-ERROR][FileNotFoundError] {config_file}')
            raise FileNotFoundError(f'[FILE-PATH] {config_file}')
        return config

    @property
    def config(self) -> dict:
        return self._config

    # --- Unnecessary function --- #
    # @property
    # def sample_config(self) -> dict:
    #     return self._sample_config


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG = Config(PROJECT_ROOT / 'conf.d/namu-bot.yaml').config
