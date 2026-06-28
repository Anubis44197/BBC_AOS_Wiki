"""
BBC-AOS Configuration Module
Provides centralized configuration parameters and helper utilities for project directory structure.
"""

import os
import logging
from typing import Dict, Any

from bbc_aos.runtime_paths import runtime_dir, runtime_file

# Set up logging
logger = logging.getLogger("bbc_aos.config.config")


class BBCConfig:
    """
    Centralized configuration class for the BBC-AOS system.
    Provides directory paths and policy configuration settings.
    """
    LOG_LEVEL: str = os.getenv("BBC_LOG_LEVEL", "INFO").upper()
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # State Drift Gate
    STATE_DRIFT_TOLERANCE: float = 0.05
    STATE_DRIFT_FAIL_THRESHOLD: float = 0.20
    
    # Healing Limits
    HEAL_HARD_LIMIT: int = 3
    
    # Analysis Limits
    MAX_FILES: int = 2000
    
    # Incremental Analysis
    CHANGE_INDEX_FILE: str = "change_index.json"
    CONTEXT_SEGMENTS_FILE: str = "context_segments.json"
    INCREMENTAL_HASH_ALGO: str = "sha256"
    
    # Logical BBC isolation directory, physically stored in the ghost workspace.
    BBC_DIR: str = "runtime"
    
    # BBC Policy Defaults
    BBC_INSTRUCTIONS_VERSION: str = "1.0"
    CONTEXT_SCHEMA_VERSION: str = "8.5"
    DEFAULT_FAIL_POLICY: str = "fail_closed"
    DEFAULT_ENFORCEMENT: str = "strict"
    
    @staticmethod
    def get_bbc_dir(project_root: str = ".") -> str:
        """
        Gets or creates the BBC-AOS ghost runtime directory.

        Args:
            project_root: The root path of the project. Defaults to current directory.

        Returns:
            The absolute path to the ghost runtime directory.
        """
        bbc_dir = runtime_dir(project_root)
        bbc_dir.mkdir(parents=True, exist_ok=True)
        return str(bbc_dir)

    @staticmethod
    def get_context_path(project_root: str = ".") -> str:
        """
        Gets the path to bbc_context.json inside the ghost runtime directory.

        Args:
            project_root: The root path of the project.

        Returns:
            The path to the context JSON file.
        """
        return str(runtime_file(project_root, "bbc_context.json"))
