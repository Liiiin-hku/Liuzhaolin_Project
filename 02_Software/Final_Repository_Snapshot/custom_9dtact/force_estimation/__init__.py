"""Force-estimation package with lazy optional visualization dependencies."""

__all__ = ["Estimator", "Visualizer"]


def __getattr__(name):
    if name == "Estimator":
        from .estimator import Estimator

        return Estimator
    if name == "Visualizer":
        from .force_visualizer import Visualizer

        return Visualizer
    raise AttributeError(name)
