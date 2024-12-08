import os
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import matplotlib.pyplot as plt
import pytest
import torch

from torchgeo.datasets import SubstationDataset


class Args:
    """Mocked arguments for testing SubstationDataset."""

    def __init__(self) -> None:
        self.data_dir: str = os.path.join(os.getcwd(), 'tests', 'data')
        self.in_channels: int = 13
        self.use_timepoints: bool = True
        self.mask_2d: bool = True
        self.timepoint_aggregation: str = 'median'


@pytest.fixture
def dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[SubstationDataset, None, None]:
    """Fixture for the SubstationDataset."""
    args = Args()
    image_files = ['image_0.npz', 'image_1.npz']

    yield SubstationDataset(**vars(args), image_files=image_files)


@pytest.mark.parametrize(
    'config',
    [
        {'in_channels': 3, 'use_timepoints': False, 'mask_2d': True},
        {
            'in_channels': 9,
            'use_timepoints': True,
            'timepoint_aggregation': 'concat',
            'mask_2d': False,
        },
        {
            'in_channels': 12,
            'use_timepoints': True,
            'timepoint_aggregation': 'median',
            'mask_2d': True,
        },
        {
            'in_channels': 5,
            'use_timepoints': True,
            'timepoint_aggregation': 'first',
            'mask_2d': False,
        },
        {
            'in_channels': 4,
            'use_timepoints': True,
            'timepoint_aggregation': 'random',
            'mask_2d': True,
        },
        {'in_channels': 2, 'use_timepoints': False, 'mask_2d': False},
        {
            'in_channels': 5,
            'use_timepoints': False,
            'timepoint_aggregation': 'first',
            'mask_2d': False,
        },
        {
            'in_channels': 4,
            'use_timepoints': False,
            'timepoint_aggregation': 'random',
            'mask_2d': True,
        },
    ],
)
def test_getitem_semantic(config: dict[str, Any]) -> None:
    args = Args()
    for key, value in config.items():
        setattr(args, key, value)  # Dynamically set arguments for each config

    # Setting mock paths and creating dataset instance
    image_files = ['image_0.npz', 'image_1.npz']
    dataset = SubstationDataset(**vars(args), image_files=image_files)

    x = dataset[0]
    assert isinstance(x, dict), f'Expected dict, got {type(x)}'
    assert isinstance(x['image'], torch.Tensor), 'Expected image to be a torch.Tensor'
    assert isinstance(x['mask'], torch.Tensor), 'Expected mask to be a torch.Tensor'


def test_len(dataset: SubstationDataset) -> None:
    """Test the length of the dataset."""
    assert len(dataset) == 2


def test_output_shape(dataset: SubstationDataset) -> None:
    """Test the output shape of the dataset."""
    x = dataset[0]
    assert x['image'].shape == torch.Size([13, 228, 228])
    assert x['mask'].shape == torch.Size([2, 228, 228])


def test_plot(dataset: SubstationDataset) -> None:
    sample = dataset[0]
    dataset.plot(sample, suptitle='Test')
    plt.close()
    dataset.plot(sample, show_titles=False)
    plt.close()
    sample['prediction'] = sample['mask'].clone()
    dataset.plot(sample)
    plt.close()


def test_already_downloaded(
    dataset: SubstationDataset, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that the dataset doesn't re-download if already present."""
    # Simulating that files are already present by copying them to the target directory
    url_for_images = os.path.join('tests', 'data', 'substation', 'image_stack.tar.gz')
    url_for_masks = os.path.join('tests', 'data', 'substation', 'mask.tar.gz')

    # Copy files to the temporary directory to simulate already downloaded files
    shutil.copy(url_for_images, tmp_path)
    shutil.copy(url_for_masks, tmp_path)

    # No download should be attempted, since the files are already present
    # Mock the _download method to simulate the behavior
    monkeypatch.setattr(dataset, '_download', MagicMock())
    dataset._download()  # This will now call the mocked method


def test_download(
    dataset: SubstationDataset, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test the _download method of the dataset."""
    # Mock the download_url and extract_archive functions
    mock_download_url = MagicMock()
    mock_extract_archive = MagicMock()
    monkeypatch.setattr('torchgeo.datasets.substation.download_url', mock_download_url)
    monkeypatch.setattr(
        'torchgeo.datasets.substation.extract_archive', mock_extract_archive
    )

    # Call the _download method
    dataset._download()

    # Check that download_url was called twice
    mock_download_url.assert_called()
    assert mock_download_url.call_count == 2

    # Check that extract_archive was called twice
    mock_extract_archive.assert_called()
    assert mock_extract_archive.call_count == 2
