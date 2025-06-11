
import app.settings as settings
import shutil
from pathlib import Path
from app.lib.utils.logger import logger


def ensure_file(original: Path, reserve: Path) -> None:
    """
    Ensures the file exists otherwise copy it from the reserve location
    :param original: original file location
    :param reserve: rserve file location
    :return: None
    """
    if not original.exists():
        logger.warning(f'File {original} is not found. Try to create')
        shutil.copy(reserve, original)
    else:
        logger.debug(f'File {original} is in place. Do nothing.')


# Tuple of ensuree to check
ensuree = (
    (settings.VEHICLES_LOC,       settings.VEHICLES_RESERVE_LOC),
    (settings.STATEPARK_LOC,      settings.STATEPARK_RESERVE_LOC),
    (settings.DEPOTPARK_LOC,      settings.DEPOTPARK_RESERVE_LOC),
    (settings.CACHE_LOC,          settings.CACHE_RESERVE_LOC),
    (settings.QUERYLOG_DB_LOC,    settings.QUERYLOG_DB_RESERVE_LOC),
    (settings.BLACKLIST_FILE_LOC, settings.BLACKLIST_RESERVE_LOC),
    (settings.AI_MODEL_LOC,       settings.AI_MODEL_RESERVE_LOC)
)


def ensure_all() -> None:
    """
    Ensures all necessary files are present in the storage directory
    Creates them if not.
    :return: None
    """
    for item in ensuree:
        ensure_file(Path(item[0]), Path(item[1]))
