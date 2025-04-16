import os 
import torch
import numpy as np
from simpletransformers.config.model_args import ModelArgs
from simpletransformers.language_representation import RepresentationModel

from model_skel import HCCD

from transformers import logging 
logging.set_verbosity_error()

class InferenceVul:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.hccd = HCCD()
        self.model = self.load_model()

    def _batch(self, sequence, steps = 1):
        for idx in range(0, len(sequence), steps):
            yield sequence[idx: min(idx + steps, len(sequence))]

    def _repr_model(self, sequence, model_type, model_name, batch_n = 32):
        use_cuda = True if torch.cuda.is_available() else False
        model_args = ModelArgs(num_train_epochs = 4)
        hidden_states = []
        model = RepresentationModel(
            model_type = model_type, model_name = model_name, args = model_args, use_cuda = use_cuda
        )
        for x in self._batch(sequence, batch_n):
            hidden_states.append(model.encode_sentences(x, combine_strategy = "mean", batch_size = len(x)))
        return [i for vector in hidden_states for i in vector]

    def _process_files(self, file_path: str):
        with open(file_path) as f:
            raw_lines = f.readlines()
        non_empty_lines = []
        line_map = []
        for idx, line in enumerate(raw_lines):
            if line.strip():
                non_empty_lines.append(line.strip()) 
                line_map.append(idx) 
            else:
                line_map.append(idx)
        return raw_lines, non_empty_lines

    def get_text_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                return b"\0" not in f.read(1024)
        except:
            return False

    def get_all_text_files(self, path):
        files = []

        if isinstance(path, list):
            paths = path
        else:
            paths = [path]
        for p in paths:
            if os.path.isfile(p) and self.get_text_file(p):
                files.append(p)
            elif os.path.isdir(p):
                for root, _, filenames in os.walk(p):
                    for name in filenames:
                        full_path = os.path.join(root, name)
                        if self.get_text_file(full_path):
                            files.append(full_path)

        return files

    def get_embeddings(self, non_empty_lines):
        embeddings = self._repr_model(
            sequence = non_empty_lines,
            model_type = "gpt2",
            model_name = "gpt2",
            batch_n = 32
        )
        return embeddings

    def load_model(self):
        model = self.hccd
        model.load_state_dict(torch.load(self.model_path, map_location = torch.device("cpu")))
        model.eval()
        return model

    def run_inference(self, embeddings, raw_lines):
        if len(embeddings) == 0:
            raise ValueError("Embeddings are empty — nothing to infer.")
        with torch.no_grad():
            inputs = torch.tensor(np.array(embeddings)).float()
            outputs = self.model(inputs)
            predictions = torch.argmax(outputs, dim=1).tolist()

        label_map = {
            0: "Password",
            1: "Generic Secret",
            2: "Private Key",
            3: "Generic Token",
            4: "Predefined Pattern",
            5: "Auth Key Token",
            6: "Seed/Salt/Nonce",
            7: "Other",
            8: "Benign"
        }

        result = {}
        for idx, raw_line in enumerate(raw_lines, start = 1):
            if raw_line.strip() == "":
                result[f"Line {idx}"] = {"line_content": "Empty", "credential_type": "Empty"}
            else:
                pred = predictions.pop(0)
                result[f"Line {idx}"] = {"line_content": f"[{raw_line.strip()}]", "credential_type": f"[{label_map[pred]}]"}
        return result

    def _view_results(self, result):
        for line_number, details in result.items():
            print(f"{line_number} Content: {details['line_content']}, Credential type: {details['credential_type']}")

    # def run_detection(self, file_path: str):
    #     raw_lines, non_empty_lines = self._process_files(file_path)
    #     if not non_empty_lines:
    #         print("Skipping empty file — no content to scan.")
    #         return
    #     embeddings = self.get_embeddings(non_empty_lines)
    #     result = self.run_inference(embeddings, raw_lines)
    #     self._view_results(result)

    def run_detection(self, path):
        files = self.get_all_text_files(path)
        if not files:
            print("No readable text files found.")
            return
        for file_path in files:
            raw_lines, non_empty_lines = self._process_files(file_path)
            if not non_empty_lines:
                print(f"Skipping empty file: {file_path}")
                continue
            embeddings = self.get_embeddings(non_empty_lines)
            result = self.run_inference(embeddings, raw_lines)
            print(f"\n📄 Results for {file_path}")
            self._view_results(result)

    
    def has_credentials(self, path: str | list[str]) -> bool:
        files = self.get_all_text_files(path)
        for file_path in files:
            raw_lines, non_empty_lines = self._process_files(file_path)
            if not non_empty_lines:
                continue
            embeddings = self.get_embeddings(non_empty_lines)
            result = self.run_inference(embeddings, raw_lines)
            for details in result.values():
                if details["credential_type"] != "Empty":
                    return True
        return False


# # Usage Example:
# model_path = f"{os.getcwd()}/models/m2.pth"
# detector = InferenceVul(model_path)
# test_path = "/Users/Gabriel/Projects/sitm/test.py"
# print(detector.run_detection(test_path))
# # print(detector.has_credentials(test_path))
