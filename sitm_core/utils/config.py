from pathlib import Path
from typing import Dict, Any
import yaml


class Config:
    def __init__(self) -> None:
        base_path = Path(__file__).resolve().parent.parent.parent
        config_path = base_path / "sitm_core" / "configs" / "config.yaml"

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        self.label_map: Dict[int, str] = config_data["label_map"]
        self.gpt_model_type: str = config_data["gpt_model_type"]
        self.gpt_model_name: str = config_data["gpt_model_name"]
        self.batch_size_32: int = config_data["batch_size_32"]
        self.epochs_4: int = config_data["epochs_4"]
        self.mean_pooling: str = config_data["mean_pooling"]
        self.dance_model_path: Path = base_path / config_data["dance_model_path"]
        self.vulstyle_model_path: Path = base_path / config_data["vulstyle_model_path"]

config = Config()
