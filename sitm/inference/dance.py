import torch
import numpy as np
from typing import Tuple, List, Generator, Sequence
from simpletransformers.config.model_args import ModelArgs
from simpletransformers.language_representation import RepresentationModel

from sitm.inference.model_skel import HCCD
from sitm.utils.io import get_all_text_files, read_file_lines
from sitm.utils.functions import view_results
from sitm.utils.config import config

from transformers import logging
logging.set_verbosity_error()

class InferenceVul:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.hccd = HCCD()
        self.model = self.load_model()

    def _batch(self, sequence: Sequence[str], steps: int = 1) -> Generator[list[str], None, None]:
        for idx in range(0, len(sequence), steps):
            yield sequence[idx: min(idx + steps, len(sequence))]

    def _repr_model(
        self, sequence: List[str], model_type: str, model_name: str, batch_n: int = 32
    ) -> List[np.ndarray]:
        use_cuda = torch.cuda.is_available()
        model_args = ModelArgs(num_train_epochs = config.epochs_4)
        hidden_states = []
        model = RepresentationModel(
            model_type = model_type, model_name = model_name, args = model_args, use_cuda = use_cuda
        )
        for x in self._batch(sequence, batch_n):
            hidden_states.append(
                model.encode_sentences(x, combine_strategy = config.mean_pooling, batch_size = len(x))
            )
        return [i for vector in hidden_states for i in vector]

    def get_embeddings(self, non_empty_lines: List[str]) -> List[np.ndarray]:
        return self._repr_model(
            sequence = non_empty_lines,
            model_type = config.gpt_model_type,
            model_name = config.gpt_model_name,
            batch_n = config.batch_size_32
        )

    def load_model(self) -> torch.nn.Module:
        model = self.hccd
        model.load_state_dict(torch.load(self.model_path, map_location = torch.device("cpu")))
        model.eval()
        return model

    def run_inference(self, embeddings: List[np.ndarray], raw_lines: List[str]) -> dict:
        if not embeddings:
            raise ValueError("Embeddings are empty — nothing to infer.")
        with torch.no_grad():
            inputs = torch.tensor(np.array(embeddings)).float()
            outputs = self.model(inputs)
            predictions = torch.argmax(outputs, dim = 1).tolist()
        label_map = config.label_map
        result = {}
        for idx, raw_line in enumerate(raw_lines, start = 1):
            if raw_line.strip() == "":
                result[f"Line {idx}"] = {"line_content": "Empty", "credential_type": "Empty"}
            else:
                pred = predictions.pop(0)
                result[f"Line {idx}"] = {
                    "line_content": f"[{raw_line.strip()}]",
                    "credential_type": f"[{label_map[pred]}]"
                }
        return result

    def preprocess_file_lines(self, file_path: str) -> Tuple[List[str], List[str]]:
        raw_lines = read_file_lines(file_path)
        non_empty_lines = []
        line_map = []
        for idx, line in enumerate(raw_lines):
            if line.strip():
                non_empty_lines.append(line.strip())
            line_map.append(idx)
        return raw_lines, non_empty_lines

    def run_detection(self, path: str | List[str]) -> None:
        files = get_all_text_files(path)
        if not files:
            print("No readable text files found.")
            return
        for file_path in files:
            try:
                raw_lines, non_empty_lines = self.preprocess_file_lines(file_path)
                if not raw_lines:
                    print(f"Skipping unreadable or empty file: {file_path}")
                    continue
                embeddings = self.get_embeddings(non_empty_lines)
                result = self.run_inference(embeddings, raw_lines)
                print(f"Results for {file_path}")
                view_results(result)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

    def has_credentials(self, path: str | List[str]) -> bool:
        files = get_all_text_files(path)
        for file_path in files:
            try:
                raw_lines, non_empty_lines = self.preprocess_file_lines(file_path)
                if not raw_lines:
                    continue
                embeddings = self.get_embeddings(non_empty_lines)
                result = self.run_inference(embeddings, raw_lines)
                for details in result.values():
                    if details["credential_type"] != "Empty":
                        return True
            except Exception as e:
                print(f"Error scanning file {file_path}: {e}")
                continue
        return False