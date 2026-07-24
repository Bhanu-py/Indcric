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
            'shirt_size': '38',
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
        self.assertEqual(order.size, '38')
        self.assertEqual(order.jersey_number, '7')
        self.assertEqual(order.line_total,
                         JerseyOrder.rate_for('collar_half') * 2)
        self.assertEqual(JerseyOrder.objects.get(
            item_type='player_cap').quantity, 1)
        self.assertEqual(JerseyOrder.objects.get(
            item_type='player_cap').size, JerseyOrder.FREE_SIZE)

    def test_adult_shirt_and_pant_use_separate_standard_sizes(self):
        resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'self',
            'gender': 'male',
            'wearer_name': 'Adult',
            'item_types': ['collar_half', 'pant'],
            'shirt_size': '40',
            'pant_size': '32',
            'quantity_collar_half': '1',
            'quantity_pant': '1',
            'jersey_number': '9',
            'notes': '',
        })

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.get(
            item_type='collar_half').size, '40')
        self.assertEqual(JerseyOrder.objects.get(item_type='pant').size, '32')

    def test_duplicate_number_is_allowed_for_non_self_orders(self):
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
            'kid_shirt_full_chest': '30',
            'kid_shirt_half_chest': '15',
            'kid_shirt_length': '21',
            'kid_shirt_shoulder': '13',
            'quantity_round_half': '1',
            'jersey_number': '10',
            'notes': '',
        })

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.filter(
            jersey_number='10').count(), 2)

    def test_self_number_must_be_unique_across_players(self):
        other = User.objects.create_user(username='other-player', password='x')
        JerseyOrder.objects.create(
            user=other,
            for_person='self',
            gender='male',
            wearer_name='Other Player',
            item_type='collar_half',
            size='38',
            quantity=1,
            jersey_number='25',
        )

        resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'self',
            'gender': 'male',
            'wearer_name': 'Current Player',
            'item_types': ['round_half'],
            'shirt_size': '40',
            'quantity_round_half': '1',
            'jersey_number': '25',
            'notes': '',
        })

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already used by another player')
        self.assertEqual(JerseyOrder.objects.filter(
            user=self.user, jersey_number='25').count(), 0)

    def test_headwear_does_not_require_size(self):
        cap_resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'family',
            'gender': 'unisex',
            'wearer_name': 'Family',
            'item_types': ['umpire_cap'],
            'quantity_umpire_cap': '1',
            'jersey_number': '7',
            'notes': '',
        })

        self.assertEqual(cap_resp.status_code, 302)
        self.assertEqual(JerseyOrder.objects.get(
            item_type='umpire_cap').size, JerseyOrder.FREE_SIZE)

        shirt_resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'self',
            'gender': 'male',
            'wearer_name': 'Member',
            'item_types': ['collar_half'],
            'quantity_collar_half': '1',
            'jersey_number': '',
            'notes': '',
        })

        self.assertEqual(shirt_resp.status_code, 200)
        self.assertContains(
            shirt_resp, 'Choose an adult shirt size from the maker chart.')
        self.assertEqual(JerseyOrder.objects.count(), 1)

    def test_kid_custom_measurements_are_saved(self):
        resp = self.client.post(reverse('jersey-orders'), {
            'for_person': 'kid',
            'gender': 'girl',
            'wearer_name': 'Kid',
            'item_types': ['round_full', 'shorts'],
            'kid_shirt_full_chest': '28',
            'kid_shirt_half_chest': '14',
            'kid_shirt_length': '20',
            'kid_shirt_shoulder': '12',
            'kid_pant_length': '26',
            'kid_pant_relaxed_waist': '20',
            'kid_pant_half_hip': '26',
            'quantity_round_full': '1',
            'quantity_shorts': '1',
            'jersey_number': '21',
            'notes': '',
        })

        self.assertEqual(resp.status_code, 302)
        self.assertIn('Kid custom shirt', JerseyOrder.objects.get(
            item_type='round_full').size)
        self.assertIn('Kid custom pant', JerseyOrder.objects.get(
            item_type='shorts').size)

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

    def test_number_reference_excludes_non_self_orders(self):
        JerseyOrder.objects.create(
            user=self.user,
            for_person='kid',
            gender='boy',
            wearer_name='Kid One',
            item_type='round_half',
            size='Kid custom shirt',
            quantity=1,
            jersey_number='66',
        )

        refs = _taken_numbers()
        self.assertEqual(refs, [])

    def test_member_page_shows_cart_total(self):
        JerseyOrder.objects.create(
            user=self.user,
            for_person='self',
            gender='male',
            wearer_name='Member',
            item_type='collar_half',
            size='38',
            quantity=2,
            jersey_number='7',
        )
        JerseyOrder.objects.create(
            user=self.user,
            for_person='self',
            gender='unisex',
            wearer_name='Member',
            item_type='player_cap',
            size=JerseyOrder.FREE_SIZE,
            quantity=1,
            jersey_number='7',
        )

        resp = self.client.get(reverse('jersey-orders'))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '3 items selected')
        self.assertContains(resp, 'Cart total')
        self.assertContains(resp, '&#8377;1160.00')

    def test_staff_delete_from_member_page_returns_to_member_form(self):
        staff = User.objects.create_user(
            username='staff-owner', password='x', is_staff=True)
        self.client.force_login(staff)
        order = JerseyOrder.objects.create(
            user=staff,
            for_person='self',
            gender='male',
            wearer_name='Staff',
            item_type='collar_half',
            size='38',
            quantity=1,
            jersey_number='17',
        )

        resp = self.client.post(reverse('jersey-order-delete', args=[order.id]), {
            'next': reverse('jersey-orders'),
        })

        self.assertRedirects(resp, reverse('jersey-orders'))
        self.assertFalse(JerseyOrder.objects.filter(id=order.id).exists())

    def test_staff_delete_without_next_still_returns_to_admin(self):
        staff = User.objects.create_user(
            username='staff-admin', password='x', is_staff=True)
        self.client.force_login(staff)
        order = JerseyOrder.objects.create(
            user=staff,
            for_person='self',
            gender='male',
            wearer_name='Staff',
            item_type='collar_half',
            size='38',
            quantity=1,
            jersey_number='18',
        )

        resp = self.client.post(
            reverse('jersey-order-delete', args=[order.id]))

        self.assertRedirects(resp, reverse('jersey-orders-admin'))
        self.assertFalse(JerseyOrder.objects.filter(id=order.id).exists())

    def test_order_page_shows_product_and_size_guides(self):
        resp = self.client.get(reverse('jersey-orders'))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Wide-Brim Hat')
        self.assertContains(
            resp, 'Family and kids can reuse a jersey number')
        self.assertContains(resp, 'How to choose the right size')
        self.assertContains(resp, 'Adult shirt standard size chart')
        self.assertContains(resp, 'Adult pant / shorts standard size chart')
        self.assertContains(resp, 'Kids custom measurements')

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
            'shirt_size': '38',
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
        delete_resp = self.client.post(
            reverse('jersey-order-delete', args=[order.id]))

        self.assertEqual(delete_resp.status_code, 302)
        self.assertTrue(JerseyOrder.objects.filter(id=order.id).exists())

        page_resp = self.client.get(reverse('jersey-orders'))
        self.assertContains(page_resp, 'Jersey ordering is closed.')
        self.assertContains(page_resp, 'Locked')

    def test_staff_can_set_close_date_shown_bold_to_members(self):
        staff = User.objects.create_user(
            username='window-staff', password='x', is_staff=True)
        self.client.force_login(staff)
        closes_at = timezone.localtime(
            timezone.now() + timedelta(days=3)).replace(second=0, microsecond=0)

        resp = self.client.post(reverse('jersey-orders-admin'), {
            'action': 'update_order_window',
            'is_enabled': 'on',
            'closes_at': closes_at.strftime('%Y-%m-%dT%H:%M'),
        })

        self.assertEqual(resp.status_code, 302)
        window = JerseyOrderWindow.objects.get()
        self.assertTrue(window.is_enabled)
        self.assertEqual(window.closes_at_label(),
                         closes_at.strftime('%d %b %Y, %H:%M'))

        self.client.force_login(self.user)
        page_resp = self.client.get(reverse('jersey-orders'))

        self.assertContains(page_resp, 'Open')
        self.assertContains(page_resp, 'Please order before that.')
        self.assertContains(
            page_resp,
            f'<strong class="font-extrabold text-red-700">{window.closes_at_label()}</strong>',
            html=True,
        )
        self.assertNotContains(page_resp, 'Order close date:')

    def test_staff_can_export_orders(self):
        staff = User.objects.create_user(
            username='staff', password='x', is_staff=True)
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
        self.assertEqual(worksheet['F1'].value, 'Size / measurement')
        self.assertEqual(worksheet['I1'].value, 'Kid Measurements')
        self.assertEqual(worksheet['F2'].value, '28')
