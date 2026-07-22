from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class JerseyOrder(models.Model):
    FOR_SELF = 'self'
    FOR_KID = 'kid'
    FOR_FAMILY = 'family'
    FOR_GUEST = 'guest'
    FOR_CHOICES = [
        (FOR_SELF, 'Self'),
        (FOR_KID, 'Kid'),
        (FOR_FAMILY, 'Family'),
        (FOR_GUEST, 'Guest'),
    ]
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_BOY = 'boy'
    GENDER_GIRL = 'girl'
    GENDER_UNISEX = 'unisex'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_BOY, 'Boy'),
        (GENDER_GIRL, 'Girl'),
        (GENDER_UNISEX, 'Unisex / not specific'),
    ]

    ITEM_RATES = {
        'collar_half': Decimal('450.00'),
        'collar_full': Decimal('500.00'),
        'round_half': Decimal('420.00'),
        'round_full': Decimal('460.00'),
        'pant': Decimal('500.00'),
        'shorts': Decimal('450.00'),
        'umpire_cap': Decimal('290.00'),
        'player_cap': Decimal('260.00'),
    }
    ITEM_CHOICES = [
        ('collar_half', '180 GSM Collar Half Sleeve'),
        ('collar_full', '180 GSM Collar Full Sleeve'),
        ('round_half', '180 GSM Round Neck Half Sleeve'),
        ('round_full', '180 GSM Round Neck Full Sleeve'),
        ('pant', '220 GSM 4-Way Lycra Pant'),
        ('shorts', '220 GSM 4-Way Lycra Shorts'),
        ('umpire_cap', 'Wide-Brim Hat'),
        ('player_cap', 'Player Cap'),
    ]
    SHIRT_ITEMS = {'collar_half', 'collar_full', 'round_half', 'round_full'}
    PANT_ITEMS = {'pant', 'shorts'}
    HEADWEAR_ITEMS = {'umpire_cap', 'player_cap'}
    FREE_SIZE = 'Free size - cap/hat'
    ITEM_META = {
        'collar_half': {'visual': 'Polo', 'group': 'T-shirt', 'note': 'Collar, half sleeve'},
        'collar_full': {'visual': 'Polo', 'group': 'T-shirt', 'note': 'Collar, full sleeve'},
        'round_half': {'visual': 'Tee', 'group': 'T-shirt', 'note': 'Round neck, half sleeve'},
        'round_full': {'visual': 'Tee', 'group': 'T-shirt', 'note': 'Round neck, full sleeve'},
        'pant': {'visual': 'Pant', 'group': 'Bottom wear', 'note': '4-way lycra pant'},
        'shorts': {'visual': 'Short', 'group': 'Bottom wear', 'note': '4-way lycra shorts'},
        'umpire_cap': {'visual': 'Hat', 'group': 'Headwear', 'note': 'Wide-brim hat, not umpire-only'},
        'player_cap': {'visual': 'Cap', 'group': 'Headwear', 'note': 'Player cap'},
    }

    NUMERIC_SIZES = (20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44)
    SHIRT_SIZE_CHOICES = [(str(size), str(size)) for size in NUMERIC_SIZES]
    SIZE_MEASUREMENTS = [
        {'size': '20', 'full_chest': '22', 'half_chest': '11', 'length': '16', 'shoulder': '10'},
        {'size': '22', 'full_chest': '24', 'half_chest': '12', 'length': '17', 'shoulder': '11'},
        {'size': '24', 'full_chest': '26', 'half_chest': '13', 'length': '18', 'shoulder': '11'},
        {'size': '26', 'full_chest': '28', 'half_chest': '14', 'length': '18.5', 'shoulder': '11.8'},
        {'size': '28', 'full_chest': '30', 'half_chest': '15', 'length': '21', 'shoulder': '13'},
        {'size': '30', 'full_chest': '32', 'half_chest': '16', 'length': '23', 'shoulder': '13'},
        {'size': '32', 'full_chest': '34', 'half_chest': '17', 'length': '24', 'shoulder': '14'},
        {'size': '34', 'full_chest': '36', 'half_chest': '18', 'length': '25', 'shoulder': '15'},
        {'size': '36', 'full_chest': '36', 'half_chest': '18', 'length': '26', 'shoulder': '16'},
        {'size': '38', 'full_chest': '38', 'half_chest': '19', 'length': '27', 'shoulder': '16'},
        {'size': '40', 'full_chest': '40', 'half_chest': '20', 'length': '28', 'shoulder': '16'},
        {'size': '42', 'full_chest': '42', 'half_chest': '21', 'length': '28', 'shoulder': '17'},
        {'size': '44', 'full_chest': '44', 'half_chest': '22', 'length': '29', 'shoulder': '17'},
    ]
    PANT_SIZE_MEASUREMENTS = [
        {'size': '20', 'length': '20', 'relaxed_waist': '18', 'half_hip': '20'},
        {'size': '22', 'length': '22', 'relaxed_waist': '18', 'half_hip': '22'},
        {'size': '24', 'length': '24', 'relaxed_waist': '19', 'half_hip': '24'},
        {'size': '26', 'length': '26', 'relaxed_waist': '20', 'half_hip': '26'},
        {'size': '28', 'length': '28', 'relaxed_waist': '21', 'half_hip': '28'},
        {'size': '30', 'length': '30', 'relaxed_waist': '22', 'half_hip': '30'},
        {'size': '32', 'length': '32', 'relaxed_waist': '23', 'half_hip': '32'},
        {'size': '34', 'length': '34', 'relaxed_waist': '24', 'half_hip': '34'},
        {'size': '36', 'length': '36', 'relaxed_waist': '25', 'half_hip': '36'},
        {'size': '38', 'length': '38', 'relaxed_waist': '26', 'half_hip': '38'},
        {'size': '40', 'length': '40', 'relaxed_waist': '27', 'half_hip': '40'},
        {'size': '42', 'length': '42', 'relaxed_waist': '28', 'half_hip': '42'},
        {'size': '44', 'length': '42', 'relaxed_waist': '29', 'half_hip': '42'},
    ]
    PANT_SIZE_CHOICES = [
        ('20', 'Size 20 - length 20", relaxed waist 18", half hip 20"'),
        ('22', 'Size 22 - length 22", relaxed waist 18", half hip 22"'),
        ('24', 'Size 24 - length 24", relaxed waist 19", half hip 24"'),
        ('26', 'Size 26 - length 26", relaxed waist 20", half hip 26"'),
        ('28', 'Size 28 - length 28", relaxed waist 21", half hip 28"'),
        ('30', 'Size 30 - length 30", relaxed waist 22", half hip 30"'),
        ('32', 'Size 32 - length 32", relaxed waist 23", half hip 32"'),
        ('34', 'Size 34 - length 34", relaxed waist 24", half hip 34"'),
        ('36', 'Size 36 - length 36", relaxed waist 25", half hip 36"'),
        ('38', 'Size 38 - length 38", relaxed waist 26", half hip 38"'),
        ('40', 'Size 40 - length 40", relaxed waist 27", half hip 40"'),
        ('42', 'Size 42 - length 42", relaxed waist 28", half hip 42"'),
        ('44', 'Size 44 - length 42", relaxed waist 29", half hip 42"'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jersey_orders',
    )
    # Numbers permanently booked to a specific member (username), independent of
    # actual orders — reserved for them, blocked for everyone else.
    MANUAL_NUMBER_RESERVATIONS = {'10': 'bhanu', '8': 'Akhil_Reddy'}

    for_person = models.CharField(max_length=10, choices=FOR_CHOICES, default=FOR_SELF)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default=GENDER_UNISEX)
    wearer_name = models.CharField(max_length=80)
    item_type = models.CharField(max_length=20, choices=ITEM_CHOICES)
    size = models.CharField(max_length=160, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    jersey_number = models.CharField(
        max_length=3,
        blank=True,
        help_text="Number printed ON the jersey. Blank = no number on the jersey.",
    )
    # Tracking reference for the wearer's order batch. Equals the jersey number
    # when one is picked; otherwise a 3-digit temporary code (NOT on the jersey).
    reference = models.CharField(max_length=3, blank=True, default='')
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__username', 'wearer_name', 'item_type']

    def __str__(self):
        return f"{self.wearer_name} - {self.get_item_type_display()} #{self.jersey_number or '-'}"

    @classmethod
    def _new_reference(cls):
        """A random unused 3-digit code (100–999), avoiding existing references,
        jersey numbers and manually-booked numbers."""
        import random
        used = (
            set(cls.objects.exclude(reference='').values_list('reference', flat=True))
            | set(cls.objects.exclude(jersey_number='').values_list('jersey_number', flat=True))
            | set(cls.MANUAL_NUMBER_RESERVATIONS.keys())
        )
        pool = [str(n) for n in range(100, 1000) if str(n) not in used]
        return random.choice(pool) if pool else str(random.randint(100, 999))

    @classmethod
    def sync_reference(cls, user, wearer_name):
        """Recompute the shared reference for a wearer's orders: the picked
        jersey number if any exists, else a stable 3-digit temporary code."""
        qs = cls.objects.filter(user=user, wearer_name__iexact=(wearer_name or '').strip())
        if not qs.exists():
            return
        number = (
            qs.exclude(jersey_number='').order_by('id')
            .values_list('jersey_number', flat=True).first()
        )
        if number:
            ref = number
        else:
            ref = (
                qs.exclude(reference='').values_list('reference', flat=True).first()
                or cls._new_reference()
            )
        qs.update(reference=ref)

    @classmethod
    def rate_for(cls, item_type):
        return cls.ITEM_RATES.get(item_type, Decimal('0.00'))

    @property
    def unit_price(self):
        return self.rate_for(self.item_type)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def display_size(self):
        if self.size == 'FS':
            return self.FREE_SIZE
        return self.size or '-'

    def clean(self):
        super().clean()
        self.jersey_number = (self.jersey_number or '').strip()
        self.size = (self.size or '').strip()
        if self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1.'})
        if self.jersey_number and not self.jersey_number.isdigit():
            raise ValidationError({'jersey_number': 'Use numbers only.'})
        if self.size in (self.FREE_SIZE, 'FS') and self.item_type and self.item_type not in self.HEADWEAR_ITEMS:
            raise ValidationError({'size': 'Free size is only for cap/hat orders.'})
        if self.item_type and self.item_type not in self.HEADWEAR_ITEMS and not self.size:
            raise ValidationError({'size': 'Size or measurements are required for shirts, pants and shorts.'})


class JerseyOrderWindow(models.Model):
    name = models.CharField(max_length=80, default='Jersey order window')
    is_enabled = models.BooleanField(
        default=False,
        help_text='Enable this to restrict member ordering to the dates below.',
    )
    opens_at = models.DateTimeField(blank=True, null=True)
    closes_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        verbose_name = 'Jersey order window'
        verbose_name_plural = 'Jersey order window'

    def __str__(self):
        return self.name

    @classmethod
    def current(cls):
        return cls.objects.first()

    @classmethod
    def ordering_is_open(cls, at=None):
        window = cls.current()
        if not window:
            return True
        return window.is_open(at=at)

    def is_open(self, at=None):
        if not self.is_enabled:
            return True
        at = at or timezone.now()
        if self.opens_at and at < self.opens_at:
            return False
        if self.closes_at and at > self.closes_at:
            return False
        return True

    def status_text(self, at=None):
        if not self.is_enabled:
            return 'Ordering is open. No cutoff period is currently enabled.'
        at = at or timezone.now()
        if self.opens_at and at < self.opens_at:
            return f'Ordering opens on {self.opens_at_label()}.'
        if self.closes_at and at > self.closes_at:
            return f'Ordering closed on {self.closes_at_label()}.'
        if self.closes_at:
            return f'Ordering is open until {self.closes_at_label()}.'
        return 'Ordering is open.'

    def opens_at_label(self):
        if not self.opens_at:
            return ''
        return timezone.localtime(self.opens_at).strftime('%d %b %Y, %H:%M')

    def closes_at_label(self):
        if not self.closes_at:
            return ''
        return timezone.localtime(self.closes_at).strftime('%d %b %Y, %H:%M')

    def clean(self):
        super().clean()
        if self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError({'closes_at': 'Close time must be after open time.'})
