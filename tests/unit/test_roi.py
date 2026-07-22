import unittest

from src.domain.roi import RelativeROI, AbsoluteROI, ROIResolver, InvalidROIError


class TestROIResolver(unittest.TestCase):

    def test_relative_roi_resolution_1920x1080(self):
        """Testa a conversão de ROI relativa para pixels em 1920x1080."""
        rel_roi = RelativeROI(x=0.187, y=0.000, width=0.281, height=0.018)
        abs_roi = ROIResolver.resolve(rel_roi, 1920, 1080)

        self.assertIsInstance(abs_roi, AbsoluteROI)
        self.assertEqual(abs_roi.left, 359)
        self.assertEqual(abs_roi.top, 0)
        self.assertEqual(abs_roi.width, 540)
        self.assertEqual(abs_roi.height, 19)

    def test_relative_roi_scaling_different_resolutions(self):
        """Testa o escalonamento proporcional para 1280x720 e 2560x1440."""
        rel_roi = RelativeROI(x=0.5, y=0.5, width=0.2, height=0.1)

        res_720 = ROIResolver.resolve(rel_roi, 1280, 720)
        self.assertEqual(res_720.left, 640)
        self.assertEqual(res_720.top, 360)
        self.assertEqual(res_720.width, 256)
        self.assertEqual(res_720.height, 72)

        res_1440 = ROIResolver.resolve(rel_roi, 2560, 1440)
        self.assertEqual(res_1440.left, 1280)
        self.assertEqual(res_1440.top, 720)
        self.assertEqual(res_1440.width, 512)
        self.assertEqual(res_1440.height, 144)

    def test_invalid_relative_roi_out_of_bounds(self):
        """Testa se estouro dos limites (x + width > 1.0) levanta erro de validação."""
        with self.assertRaises(InvalidROIError):
            RelativeROI(x=0.8, y=0.0, width=0.3, height=0.1)

        with self.assertRaises(InvalidROIError):
            RelativeROI(x=0.0, y=0.9, width=0.1, height=0.2)

    def test_invalid_relative_roi_negative(self):
        """Testa se coordenadas negativas levantam erro de validação."""
        with self.assertRaises(InvalidROIError):
            RelativeROI(x=-0.1, y=0.0, width=0.2, height=0.2)

    def test_legacy_dict_conversion(self):
        """Testa a compatibilidade transparente com dicionários absolutos ou relativos."""
        rel_dict = {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4}
        abs_from_rel = ROIResolver.resolve(rel_dict, 1000, 1000)
        self.assertEqual(abs_from_rel.left, 100)
        self.assertEqual(abs_from_rel.top, 200)

        abs_dict = {"top": 10, "left": 20, "width": 30, "height": 40}
        abs_from_abs = ROIResolver.resolve(abs_dict, 1000, 1000)
        self.assertEqual(abs_from_abs.top, 10)
        self.assertEqual(abs_from_abs.left, 20)

    def test_clamping_to_frame_boundaries(self):
        """Testa se coordenadas que tocam a borda do frame são ajustadas com segurança (clamping)."""
        rel_roi = RelativeROI(x=0.9, y=0.9, width=0.1, height=0.1)
        abs_roi = ROIResolver.resolve(rel_roi, 100, 100)

        self.assertLessEqual(abs_roi.left + abs_roi.width, 100)
        self.assertLessEqual(abs_roi.top + abs_roi.height, 100)


if __name__ == "__main__":
    unittest.main()
