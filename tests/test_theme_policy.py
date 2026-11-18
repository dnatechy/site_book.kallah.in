import unittest
from unittest.mock import patch
from app.content import get_theme, theme_css


class ThemePolicyTests(unittest.TestCase):
    def test_global_palette_is_identical_on_every_business_type(self):
        expected = get_theme()['colors']
        for category in ('clinics', 'salons', 'hotels', 'restaurants'):
            with self.subTest(category=category):
                actual = get_theme('trichy', category, {'theme': {'colors': {'primary': '#000000'}}})
                self.assertEqual(actual['colors'], expected)

    def test_category_palette_is_explicit_and_never_recolors_the_brand(self):
        config = {'mode': 'category', 'category_colors': {'restaurants': {
            'primary': '#123456', 'brand_accent': '#000000'}}}
        with patch('app.content.global_config', return_value=config):
            base = get_theme()['colors']
            category = get_theme('trichy', 'restaurants')['colors']
        self.assertEqual(category['primary'], '#123456')
        self.assertEqual(category['brand_accent'], base['brand_accent'])

    def test_theme_css_rejects_unsafe_values_and_names(self):
        css = theme_css({'colors': {'primary': '#123456', 'brand_accent': '#E53935',
                                    'text': 'red; display:none', 'bad;name': '#000000'}})
        self.assertIn('--color-brand-accent: #E53935', css)
        self.assertNotIn('display', css)
        self.assertNotIn('bad', css)


if __name__ == '__main__':
    unittest.main()
