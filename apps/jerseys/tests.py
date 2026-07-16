from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import JerseyOrder

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
        self.assertEqual(resp['Content-Type'], 'text/csv')
        self.assertContains(resp, 'Kid')
        self.assertContains(resp, 'Girl')
