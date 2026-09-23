import unittest

from preset_test_distribution import DistributionInstallTests
from preset_test_install import PresetInstallTests
from preset_test_source import PresetSourceTests

__all__ = [
    "DistributionInstallTests",
    "PresetInstallTests",
    "PresetSourceTests",
]


if __name__ == "__main__":
    unittest.main()
