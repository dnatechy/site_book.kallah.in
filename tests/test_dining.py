"""Checks for connected group seating, stock and authoritative menu pricing."""
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from app import create_app
from app.dining import load_dining, quote_dining

DIRECTORY = Path(__file__).resolve().parents[1] / 'content/locations/india/tamil-nadu/trichy/restaurants/business-01'
NOW = datetime(2026, 11, 18, 10, 0, tzinfo=ZoneInfo('Asia/Kolkata'))


class DiningTests(unittest.TestCase):
    def setUp(self):
        self.config = load_dining(DIRECTORY, {'name': 'Demo restaurant', 'is_demo': True})
        self.input = {'guests': 20, 'date': '2026-11-19', 'time': '14:00', 'items': []}

    def quote(self, values=None, reservations=()):
        return quote_dining(self.config, values or self.input, reservations, now=NOW)

    def test_fragmented_free_seats_do_not_count_as_connected(self):
        q = self.quote({**self.input, 'time': '12:30'})
        self.assertFalse(q['available'])
        self.assertEqual(q['largest_available_group'], 12)

    def test_overlap_end_boundary_and_shared_tables(self):
        q = self.quote()
        self.assertTrue(q['available'])  # Seeded booking ends at 14:00.
        self.assertEqual(q['table_ids'], ['a1', 'a2', 'a3', 'a4', 'a5'])
        reservation = {**q, 'time': '14:00'}
        self.assertFalse(self.quote(reservations=[reservation])['available'])
        self.assertFalse(self.quote({**self.input, 'time': '14:30'}, [reservation])['available'])

    def test_menu_price_overrides_client_amount(self):
        q = self.quote({**self.input, 'items': [{'dish_id': 'south-indian-thali', 'quantity': 20, 'price_paise': 1}, {'dish_id': 'fresh-lime-soda', 'quantity': 20}]})
        self.assertEqual(q['food_total_paise'], 500000)
        self.assertEqual(q['pay_now_paise'], 500000)

    def test_bad_quantities_unknown_dishes_and_sold_out(self):
        for item in [{'dish_id': 'unknown', 'quantity': 1}, {'dish_id': 'fruit-custard', 'quantity': 1}, {'dish_id': 'butter-naan', 'quantity': -1}, {'dish_id': 'butter-naan', 'quantity': 1.5}, {'dish_id': 'butter-naan', 'quantity': True}]:
            with self.subTest(item=item), self.assertRaises(ValueError):
                self.quote({**self.input, 'items': [item]})
        with self.assertRaises(ValueError):
            self.quote({**self.input, 'items': [{'dish_id': 'butter-naan', 'quantity': 20}] * 2})

    def test_stock_is_consumed_for_the_selected_service_slot(self):
        reservation = {**self.input, 'table_ids': ['b1'], 'items': [{'dish_id': 'butter-naan', 'quantity': 60}]}
        with self.assertRaises(ValueError):
            self.quote({**self.input, 'items': [{'dish_id': 'butter-naan', 'quantity': 1}]}, [reservation])
        self.assertTrue(self.quote()['available'])  # Cancelled reservation omitted.

    def test_party_size_lead_time_slot_and_window(self):
        for override in [{'guests': 0}, {'guests': 21}, {'guests': 2.5}, {'date': '2026-11-18', 'time': '10:30'}, {'date': '2026-12-25'}, {'time': '14:45'}, {'time': '15:00'}]:
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.quote({**self.input, **override})

    def test_non_demo_does_not_get_demo_busy_tables(self):
        config = load_dining(DIRECTORY, {'name': 'Restaurant'})
        self.assertFalse(config['demo_daily_reservations'])

    def test_api_and_empty_reviews(self):
        client = create_app({'TESTING': True}).test_client()
        base = '/api/v1/locations/trichy/restaurants/businesses/demo-restaurant-01'
        self.assertEqual(client.get(base+'/dining').status_code, 200)
        self.assertEqual(client.get(base+'/professionals').json['professionals'], [])
        self.assertEqual(client.post(base+'/dining/quote', json={'guests': 'x'}).status_code, 400)
        self.assertEqual(client.post(base+'/dining/quote', json={**self.input, 'date': '2020-01-01'}).status_code, 400)
        self.assertEqual(client.get('/trichy/restaurants/demo-restaurant-01/demo-restaurants-person-01').status_code, 404)


if __name__ == '__main__':
    unittest.main()
