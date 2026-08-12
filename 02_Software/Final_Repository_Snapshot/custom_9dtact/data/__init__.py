"""Dataset package with lazy OpenCV/PyTorch loading."""

__all__ = ["DTactDataset"]


def __getattr__(name):
    if name == "DTactDataset":
        from .dtact_dataset import DTactDataset

        return DTactDataset
    raise AttributeError(name)
