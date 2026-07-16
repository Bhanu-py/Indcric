from io import BytesIO
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from .models import JerseyOrder, JerseyOrderWindow
from .views import _taken_numbers

User = get_user_model()


class JerseyOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member', password='x')
        self.client.force_login(self.user)

    def test_member_can_create_order(self):
        resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'self',
            'gender': 'male',
            'wearer_name': 'Kural',
            'item_types': ['collar_half', 'player_cap'],
            'size': '38',
            'quantity_collar_half': '2',
            'quantity_player_cap': '1',
            'jersey_number': '7',
            'notes': '',
        })

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.count(), 2)
        order = JerseyOrder.objects.get(item_type='collar_half')
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.gender, 'male')
        self.assertEqual(order.jersey_number, '7')
        self.assertEqual(order.line_total, JerseyOrder.rate_for('collar_half') * 2)
        self.assertEqual(JerseyOrder.objects.get(item_type='player_cap').quantity, 1)

    def test_duplicate_jersey_number_is_allowed(self):
        other = User.objects.create_user(username='other', password='x')
        JerseyOrder.objects.create(
            user=other,
            for_person='self',
            gender='male',
            wearer_name='Other',
            item_type='collar_half',
            size='38',
            quantity=1,
            jersey_number='10',
        )

        resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'kid',
            'gender': 'boy',
            'wearer_name': 'Kural',
            'item_types': ['round_half'],
            'size': '40',
            'quantity_round_half': '1',
            'jersey_number': '10',
            'notes': '',
        })

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.filter(jersey_number='10').count(), 2)

    def test_free_size_is_allowed_for_headwear_only(self):
        cap_resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'family',
            'gender': 'unisex',
            'wearer_name': 'Family',
            'item_types': ['umpire_cap'],
            'size': JerseyOrder.FREE_SIZE,
            'quantity_umpire_cap': '1',
            'jersey_number': '7',
            'notes': '',
        })

        self.assertEqual(cap_resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.get(item_type='umpire_cap').size, JerseyOrder.FREE_SIZE)

        shirt_resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'self',
            'gender': 'male',
            'wearer_name': 'Member',
            'item_types': ['collar_half'],
            'size': JerseyOrder.FREE_SIZE,
            'quantity_collar_half': '1',
            'jersey_number': '',
            'notes': '',
        })

        self.assertEqual(shirt_resp.status_code, 200)
        self.assertContains(shirt_resp, 'Free size is only for cap/hat')
        self.assertEqual(JerseyOrder.objects.count(), 1)

    def test_number_reference_deduplicates_multiple_items_for_same_wearer(self):
        for item_type in ['collar_half', 'collar_full', 'player_cap']:
            JerseyOrder.objects.create(
                user=self.user,
                for_person='self',
                gender='male',
                wearer_name='Akhil Reddy',
                item_type=item_type,
                size='40',
                quantity=1,
                jersey_number='8',
            )

        resp = self.client.get(reverse('jersey-orders'))
        references = _taken_numbers()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0]['jersey_number'], '8')
        self.assertEqual(references[0]['wearer_name'], 'Akhil Reddy')
        self.assertEqual(references[0]['item_count'], 3)
        self.assertContains(resp, '1 shown')
        self.assertContains(resp, '3 items')

    def test_order_page_shows_product_and_size_guides(self):
        resp = self.client.get(reverse('jersey-orders'))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Wide-Brim Hat')
        self.assertContains(resp, 'Family/kids may reuse the same number')
        self.assertContains(resp, 'T-shirt maker size chart')
        self.assertContains(resp, 'Pants/shorts maker size template')

    def test_closed_ordering_window_blocks_member_changes(self):
        JerseyOrderWindow.objects.create(
            name='Closed window',
            is_enabled=True,
            opens_at=timezone.now() - timedelta(days=7),
            closes_at=timezone.now() - timedelta(days=1),
        )

        create_resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'self',
            'gender': 'male',
            'wearer_name': 'Late',
            'item_types': ['collar_half'],
            'size': '38',
            'quantity_collar_half': '1',
            'jersey_number': '11',
            'notes': '',
        })

        self.assertEqual(create_resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.count(), 0)

        order = JerseyOrder.objects.create(
            user=self.user,
            for_person='self',
            gender='male',
            wearer_name='Existing',
            item_type='collar_half',
            size='38',
            quantity=1,
            jersey_number='12',
        )
        delete_resp = self.client.post(reverse('jersey-order-delete', args=[order.id]))

        self.assertEqual(delete_resp.status_code, 302)
        self.assertTrue(JerseyOrder.objects.filter(id=order.id).exists())

        page_resp = self.client.get(reverse('jersey-orders'))
        self.assertContains(page_resp, 'Jersey ordering is closed.')
        self.assertContains(page_resp, 'Locked')

    def test_staff_can_export_orders(self):
        staff = User.objects.create_user(username='staff', password='x', is_staff=True)
        JerseyOrder.objects.create(
            user=self.user,
            for_person='kid',
            gender='girl',
            wearer_name='Kid',
            item_type='round_full',
            size='28',
            quantity=1,
            jersey_number='21',
        )
        self.client.force_login(staff)

        resp = self.client.get(reverse('jersey-orders-export'))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('jersey_orders.xlsx', resp['Content-Disposition'])

        workbook = load_workbook(BytesIO(resp.content))
        worksheet = workbook['Jersey Orders']
        self.assertEqual(worksheet['A1'].value, 'Member')
        self.assertEqual(worksheet['D2'].value, 'Kid')
        self.assertEqual(worksheet['C2'].value, 'Girl')
