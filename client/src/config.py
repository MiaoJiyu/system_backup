import json
import os
from dataclasses import dataclass, field


@dataclass
class ClientConfig:
    server_address: str = "localhost"
    server_port: int = 8000
    use_tls: bool = False
    server_fingerprint: str = ""
    auto_start: bool = True
    minimize_to_tray: bool = True
    log_level: str = "INFO"
    local_db_path: str = "fingerprints.db"
    key_path: str = "client_key.pem"

    def save(self, path: str = "config.json"):
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls, path: str = "config.json") -> "ClientConfig":
        cfg = cls()
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
        return cfg


global_config = ClientConfig.load()
