
"""Module to set correct project and file paths.
Also contains any string literals.

@author: Daniel Levie
"""

from pathlib import Path

def get_project_root() -> Path:
    """Returns the root directory of the application. 
    Returns:
        [pathlib.Path]: path to root
    """
    ROOT_DIR = Path(__file__).parent.resolve().parent
    return ROOT_DIR

def log_dir() -> Path:
    """Returns the log directory of the application. 
    Returns:
        [pathlib.Path]: path to log dir
    """
    logs_folder =  get_project_root().parent.joinpath("logs")
    logs_folder.mkdir(exist_ok=True)
    return logs_folder

def input_dir() -> Path:
    """Returns the input directory of the application. 
    Returns:
        [pathlib.Path]: path to input dir
    """
    input_folder = get_project_root().joinpath('input_files')
    return input_folder

ROOT_DIR: Path = get_project_root()
LOG_DIR: Path = log_dir()
INPUT_DIR: Path = input_dir()


INCORRECT_ENTRY_POINT = ("Beginning in Marmot v0.10.0, the abilty to run "
    "'python {}' directly has been removed. To run "
    "the code as before, run 'python bin/run_marmot_plotter.py' from " 
    "Marmot Package directory")

PLEXOS_YEAR_WARNING = ("Please Note: Year properties can not "
    "be checked for duplicates.\n"
    "Overlaping data cannot be removed from "
    "'Year' grouped data.\nThis will effect "
    "Year data that differs between partitions "
    "such as cost results.\nIt will not effect "
    "Year data that is equal in all partitions "
    "such as Installed Capacity or "
    "Line Limit results")