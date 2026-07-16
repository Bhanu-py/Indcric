from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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
        ('umpire_cap', 'Umpire Hat'),
        ('player_cap', 'Player Cap'),
    ]
    SHIRT_ITEMS = {'collar_half', 'collar_full', 'round_half', 'round_full'}

    SIZE_CHOICES = [(str(size), str(size)) for size in (20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44)]
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jersey_orders',
    )
    for_person = models.CharField(max_length=10, choices=FOR_CHOICES, default=FOR_SELF)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default=GENDER_UNISEX)
    wearer_name = models.CharField(max_length=80)
    item_type = models.CharField(max_length=20, choices=ITEM_CHOICES)
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    jersey_number = models.CharField(
        max_length=3,
        blank=True,
        help_text="Optional. Duplicates are allowed for family/kids.",
    )
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__username', 'wearer_name', 'item_type']

    def __str__(self):
        return f"{self.wearer_name} - {self.get_item_type_display()} #{self.jersey_number or '-'}"

    @classmethod
    def rate_for(cls, item_type):
        return cls.ITEM_RATES.get(item_type, Decimal('0.00'))

    @property
    def unit_price(self):
        return self.rate_for(self.item_type)

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def clean(self):
        super().clean()
        self.jersey_number = (self.jersey_number or '').strip()
        if self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1.'})
        if self.jersey_number and not self.jersey_number.isdigit():
            raise ValidationError({'jersey_number': 'Use numbers only.'})
