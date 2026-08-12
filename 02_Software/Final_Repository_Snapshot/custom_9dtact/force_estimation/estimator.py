import argparse
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

import cv2
import numpy as np
import torch
import yaml

from model import *
from force_estimation.wrench import (
    WrenchConfigurationError,
    denormalize_wrench,
    load_inference_metadata,
    vector6,
)


np.set_printoptions(suppress=True)


def configured_weights_path(cfg, model_type):
    sensor_id = cfg.get("sensor_id", "X")
    model_choice = cfg.get("model_choice")
    weights = cfg.get("weights")
    selected = None
    if isinstance(model_choice, int) and isinstance(weights, list):
        if 0 <= model_choice < len(weights):
            selected = weights[model_choice]

    suffix = selected[0] if isinstance(selected, (list, tuple)) and len(selected) > 0 else None
    epoch = selected[1] if isinstance(selected, (list, tuple)) and len(selected) > 1 else None
    if suffix is None or str(suffix).strip() == "" or epoch is None or str(epoch).strip() == "":
        raise SystemExit(
            f"Model weights are not configured for Sensor {sensor_id}. Complete training and "
            f"update configs/force_sensor_{sensor_id}.yaml before inference."
        )

    model_dir = Path(cfg["save_dir"]) / f"{model_type}{suffix}"
    weights_path = model_dir / f"epoch_{epoch}.pt"
    if not weights_path.is_file():
        raise SystemExit(
            f"The model-weights file for Sensor {sensor_id} does not exist: {weights_path}. "
            f"Complete training and update configs/force_sensor_{sensor_id}.yaml."
        )
    return model_dir, weights_path


class Estimator:
    def __init__(self, cfg):
        parser = argparse.ArgumentParser()
        parser.add_argument("--model_name", default=None, type=str)
        parser.add_argument("--model_layer", default=None, type=str)
        parser.add_argument("--cuda_index", default=None, type=int)
        args, _unknown = parser.parse_known_args()

        model_name = (
            args.model_name
            if args.model_name is not None
            else cfg["model_list"][cfg["model_choice"]][0]
        )
        model_layer = (
            args.model_layer
            if args.model_layer is not None
            else cfg["model_list"][cfg["model_choice"]][1]
        )
        model_type = model_name + "-" + str(model_layer)
        cuda_index = args.cuda_index if args.cuda_index is not None else cfg["cuda_index"]
        model_dir, weights_path = configured_weights_path(cfg, model_type)
        try:
            metadata = load_inference_metadata(
                model_dir,
                cfg,
                allow_legacy_fallback=bool(
                    cfg.get("allow_legacy_metadata_fallback", True)
                ),
            )
            self.wrench_min = vector6(metadata["wrench_min"], "wrench_min")
            self.wrench_max = vector6(metadata["wrench_max"], "wrench_max")
            self.wrench_frame = str(metadata["wrench_frame"])
            self.img_size = tuple(int(value) for value in metadata["img_size"])
        except WrenchConfigurationError as exc:
            raise SystemExit("Model physical-unit metadata check failed: {}".format(exc))

        self.device = torch.device(f"cuda:{cuda_index}" if torch.cuda.is_available() else "cpu")
        if model_name == "Resnet":
            self.model = Resnet(layer=int(model_layer), pretrained=False).to(self.device)
        elif model_name == "Densenet":
            self.model = Densenet(layer=int(model_layer), pretrained=False).to(self.device)
        else:
            raise SystemExit(f"Unsupported model type: {model_name}")

        self.save_dir = str(model_dir)
        self.model.load_state_dict(torch.load(str(weights_path), map_location=self.device))
        self.model.eval()
        with torch.no_grad():
            two_img = np.ones((2, 3, self.img_size[0], self.img_size[1]))
            representation = torch.from_numpy(two_img).float().to(self.device)
            self.model(representation)
        print("Ready to predict the 6D force!")

    def predict_normalized(self, representation):
        """Return the clipped network output in the component-wise unit range."""

        representation = representation.transpose([2, 0, 1])
        input_batch = 2
        if input_batch == 2:
            two_img = np.array([representation, representation])
            representation = torch.from_numpy(two_img).float().to(self.device)
            with torch.no_grad():
                force = self.model(representation)
                force[force < 0] = 0
                force[force > 1] = 1
                force = force.cpu().numpy()[0]
        else:
            representation = torch.from_numpy(np.array(representation)).float().to(self.device)
            with torch.no_grad():
                force = self.model(representation)
                force[force < 0] = 0
                force[force > 1] = 1
                force = force.cpu().numpy()
        return force

    def predict_force(self, representation):
        """Return physical ``Fx,Fy,Fz,Tx,Ty,Tz`` in N and N*m."""

        normalized = self.predict_normalized(representation)
        return self.denormalize(normalized)

    def denormalize(self, normalized):
        """Convert one network-output six-vector to physical units."""

        return denormalize_wrench(normalized, self.wrench_min, self.wrench_max)


if __name__ == "__main__":
    with open("force_config.yaml", "r", encoding="utf-8") as handle:
        config = yaml.load(handle, Loader=yaml.FullLoader)
    estimator = Estimator(config)
    image = cv2.imread("test.png")
    input_image = np.zeros_like(image)
    input_image[:, :, 0] = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    predicted_force = estimator.predict_force(input_image)
    print("Physical wrench [Fx,Fy,Fz,Tx,Ty,Tz] (N,N*m):", predicted_force)
