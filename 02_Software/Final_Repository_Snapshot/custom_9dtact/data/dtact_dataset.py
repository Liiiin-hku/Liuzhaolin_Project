import cv2
import numpy as np
import warnings
from pathlib import Path
from torch.utils.data import Dataset

from .path_utils import resolve_dataset_entry


class DTactDataset(Dataset):
    def __init__(self, mode='train', root_path='../Dataset', image_type='RGB',
                 test_object=False, mixed_image=True) -> None:
        super().__init__()
        self.root_path = Path(root_path).expanduser().resolve()
        self.mode = mode
        self.image_type = image_type
        self.mixed_image = mixed_image
        if mode == 'train':
            if test_object:
                if mixed_image:
                    self.images = self._load_index('train_mixed_images_object.npy')
                else:
                    self.images = self._load_index('train_images_object.npy')
                self.wrenches = self._load_index('train_wrench_object.npy')
            else:
                if mixed_image:
                    self.images = self._load_index('train_mixed_images.npy')
                else:
                    self.images = self._load_index('train_images.npy')
                self.wrenches = self._load_index('train_wrench.npy')
        else:
            if test_object:
                if mixed_image:
                    self.images = self._load_index('test_mixed_images_object.npy')
                else:
                    self.images = self._load_index('test_images_object.npy')
                self.wrenches = self._load_index('test_wrench_object.npy')
            else:
                if mixed_image:
                    self.images = self._load_index('test_mixed_images.npy')
                else:
                    self.images = self._load_index('test_images.npy')
                self.wrenches = self._load_index('test_wrench.npy')

        if len(self.images) != len(self.wrenches):
            raise ValueError(
                'Image and wrench index lengths differ: {} versus {}'.format(
                    len(self.images), len(self.wrenches)
                )
            )

    def _load_index(self, name):
        return np.load(str(self.root_path / name), allow_pickle=False)

    def _resolve_entry(self, value):
        path = resolve_dataset_entry(self.root_path, value)
        try:
            path.resolve().relative_to(self.root_path)
        except ValueError:
            warnings.warn(
                'Legacy split entry resolves outside the active dataset root: {}. '
                'Regenerate relative split indexes before packaging.'.format(path),
                RuntimeWarning,
            )
        return path

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image_path = self._resolve_entry(self.images[index])
        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError('Dataset image is unreadable: {}'.format(image_path))
        image = image.astype('float32')
        if self.image_type != 'RGB':
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        image = image.transpose([2, 0, 1])
        force_path = self._resolve_entry(self.wrenches[index])
        force = np.load(str(force_path), allow_pickle=False)
        if np.asarray(force).shape != (6,) or not np.all(np.isfinite(force)):
            raise ValueError('Wrench label must be a finite six-vector: {}'.format(force_path))
        if self.mode == 'train':
            return image, force
        else:
            return image, force, str(image_path)


if __name__ == '__main__':
    dataset_path = '../Dataset'
    dataset = DTactDataset(mode='train', root_path=dataset_path)
    print(dataset.__len__())
    for i in range(dataset.__len__()):
        print(dataset.__getitem__(i)[0])
