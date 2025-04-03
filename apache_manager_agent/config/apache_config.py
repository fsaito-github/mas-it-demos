import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ApacheConfig:
    config_path: str
    log_path: str
    backup_path: str
    allowed_directives: List[str]
    sensitive_directives: List[str]

class ApacheConfigManager:
    def __init__(self, config: ApacheConfig):
        self.config = config
        self._validate_paths()

    def _validate_paths(self):
        """Validate all required paths exist and are accessible"""
        for path in [self.config.config_path, self.config.log_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Required path does not exist: {path}")

    def backup_config(self) -> str:
        """Create a backup of the current Apache configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.config.backup_path}/apache2.conf.{timestamp}"
        
        with open(self.config.config_path, 'r') as source:
            with open(backup_file, 'w') as target:
                target.write(source.read())
        
        return backup_file

    def validate_directive(self, directive: str) -> bool:
        """Check if a directive is allowed and properly formatted"""
        return directive in self.config.allowed_directives

    def is_sensitive_directive(self, directive: str) -> bool:
        """Check if a directive is sensitive and requires special handling"""
        return directive in self.config.sensitive_directives 