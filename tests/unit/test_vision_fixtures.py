import unittest
from pathlib import Path
import cv2
import numpy as np

from src.domain.roi import RelativeROI
from src.utils.screen import get_hp_percentage, get_mp_percentage

HP_ROI = RelativeROI(0.187, 0.000, 0.281, 0.018)
MANA_ROI = RelativeROI(0.531, 0.000, 0.281, 0.018)


class TestVisionFixtures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def test_hp_fixtures(self):
        """Verifica a leitura de porcentagem de vida sobre fixtures PNG de teste."""
        img_100 = cv2.imread(str(self.fixtures_dir / "hp" / "hp_100.png"))
        hp_100 = get_hp_percentage(img_100, roi=HP_ROI)
        self.assertGreaterEqual(hp_100, 0.95)

        img_50 = cv2.imread(str(self.fixtures_dir / "hp" / "hp_50.png"))
        hp_50 = get_hp_percentage(img_50, roi=HP_ROI)
        self.assertAlmostEqual(hp_50, 0.50, delta=0.1)

        img_20 = cv2.imread(str(self.fixtures_dir / "hp" / "hp_20.png"))
        hp_20 = get_hp_percentage(img_20, roi=HP_ROI)
        self.assertAlmostEqual(hp_20, 0.20, delta=0.1)

    def test_mana_fixtures(self):
        """Verifica a leitura de porcentagem de mana sobre fixtures PNG de teste."""
        img_100 = cv2.imread(str(self.fixtures_dir / "mana" / "mana_100.png"))
        mana_100 = get_mp_percentage(img_100, roi=MANA_ROI)
        self.assertGreaterEqual(mana_100, 0.95)

        img_30 = cv2.imread(str(self.fixtures_dir / "mana" / "mana_30.png"))
        mana_30 = get_mp_percentage(img_30, roi=MANA_ROI)
        self.assertAlmostEqual(mana_30, 0.30, delta=0.1)


if __name__ == "__main__":
    unittest.main()
