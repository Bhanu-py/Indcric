from django import forms
from django.utils import timezone

from .models import JerseyOrder, JerseyOrderWindow


class JerseyOrderForm(forms.ModelForm):
    item_types = forms.MultipleChoiceField(
        choices=JerseyOrder.ITEM_CHOICES,
        error_messages={'required': 'Choose at least one item.'},
    )
    # Opt-out of picking a specific number — we auto-assign a random 3-digit
    # reference on save so the order is still trackable.
    no_number = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-stone-300 text-pitch-600 focus:ring-pitch-500',
            'x-model': 'noNum',
        }),
    )
    shirt_size = forms.ChoiceField(
        choices=[('', 'Choose adult shirt size')] + JerseyOrder.SHIRT_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    pant_size = forms.ChoiceField(
        choices=[('', 'Choose adult pant/shorts size')] + JerseyOrder.PANT_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    kid_shirt_full_chest = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 30'}))
    kid_shirt_half_chest = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 15'}))
    kid_shirt_length = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 21'}))
    kid_shirt_shoulder = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 13'}))
    kid_pant_length = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 28'}))
    kid_pant_relaxed_waist = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 21'}))
    kid_pant_half_hip = forms.DecimalField(required=False, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 28'}))

    class Meta:
        model = JerseyOrder
        fields = [
            'for_person',
            'gender',
            'wearer_name',
            'jersey_number',
            'notes',
        ]
        widgets = {
            'for_person': forms.Select(attrs={'class': 'form-select', 'x-model': 'forPerson'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'wearer_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Name on jersey / wearer name',
                '@input': 'wearer = $event.target.value',
            }),
            'jersey_number': forms.TextInput(attrs={
                'class': 'form-input',
                'maxlength': '3',
                'inputmode': 'numeric',
                'placeholder': 'e.g. 7',
                '@input': 'num = $event.target.value',
                ':disabled': 'noNum',
                ':class': "noNum ? 'form-input opacity-50' : 'form-input'",
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Optional notes',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for code, label in JerseyOrder.ITEM_CHOICES:
            self.fields[f'quantity_{code}'] = forms.IntegerField(
                required=False,
                min_value=0,
                widget=forms.NumberInput(attrs={
                    'class': 'form-input text-center',
                    'min': '0',
                    'step': '1',
                    'inputmode': 'numeric',
                    'pattern': '[0-9]*',
                    'placeholder': '0',
                    'aria-label': f'{label} quantity',
                }),
            )

    def clean(self):
        cleaned = super().clean()
        item_types = cleaned.get('item_types') or []
        is_kid = self._uses_kid_measurements(cleaned)
        has_shirt = any(item_type in JerseyOrder.SHIRT_ITEMS for item_type in item_types)
        has_pant = any(item_type in JerseyOrder.PANT_ITEMS for item_type in item_types)
        for item_type in item_types:
            field_name = f'quantity_{item_type}'
            qty = cleaned.get(field_name)
            if not qty or qty < 1:
                self.add_error(field_name, 'Enter quantity at least 1.')
        if is_kid:
            if has_shirt:
                self._require_fields(cleaned, [
                    'kid_shirt_full_chest',
                    'kid_shirt_half_chest',
                    'kid_shirt_length',
                    'kid_shirt_shoulder',
                ], 'Enter kid shirt measurements.')
            if has_pant:
                self._require_fields(cleaned, [
                    'kid_pant_length',
                    'kid_pant_relaxed_waist',
                    'kid_pant_half_hip',
                ], 'Enter kid pant/shorts measurements.')
        else:
            if has_shirt and not cleaned.get('shirt_size'):
                self.add_error('shirt_size', 'Choose an adult shirt size from the maker chart.')
            if has_pant and not cleaned.get('pant_size'):
                self.add_error('pant_size', 'Choose an adult pant/shorts size from the maker chart.')

        # Number: mandate a choice. Either opt out (auto-assign a reference on
        # save) or pick a number that isn't already reserved by another member.
        # A member may reuse their own number across their own items/family.
        no_number = cleaned.get('no_number')
        number = cleaned.get('jersey_number') or ''
        if no_number:
            cleaned['jersey_number'] = ''  # cleared; a reference is assigned on save
        elif not number:
            self.add_error('jersey_number', 'Pick a number, or tick “No specific number”.')
        else:
            reserved_to = JerseyOrder.MANUAL_NUMBER_RESERVATIONS.get(number)
            if reserved_to and (not self.user or self.user.username != reserved_to):
                self.add_error(
                    'jersey_number',
                    f'#{number} is reserved for {reserved_to}. '
                    'Pick another, or tick “No specific number”.',
                )
            else:
                clash = (
                    JerseyOrder.objects
                    .filter(jersey_number=number)
                    .exclude(user=self.user)
                    .select_related('user')
                    .first()
                )
                if clash:
                    owner = clash.wearer_name or (clash.user.username if clash.user else 'another member')
                    self.add_error(
                        'jersey_number',
                        f'#{number} is already reserved by {owner}. '
                        'Pick another, or tick “No specific number”.',
                    )
                else:
                    # One number per wearer: can't pick a different number than
                    # one this wearer already has.
                    wearer = (cleaned.get('wearer_name') or '').strip()
                    other = (
                        JerseyOrder.objects
                        .filter(user=self.user, wearer_name__iexact=wearer)
                        .exclude(jersey_number='')
                        .exclude(jersey_number=number)
                        .values_list('jersey_number', flat=True)
                        .first()
                    )
                    if other:
                        self.add_error(
                            'jersey_number',
                            f'You already have #{other}. '
                            'Use the same number, tick “No specific number”, or remove that number.',
                        )
        return cleaned

    @staticmethod
    def _uses_kid_measurements(cleaned):
        return cleaned.get('for_person') == JerseyOrder.FOR_KID

    def _require_fields(self, cleaned, field_names, message):
        for field_name in field_names:
            if not cleaned.get(field_name):
                self.add_error(field_name, message)

    def clean_jersey_number(self):
        number = (self.cleaned_data.get('jersey_number') or '').strip()
        if not number:
            return ''
        if not number.isdigit():
            raise forms.ValidationError('Use numbers only.')
        return str(int(number))

    def save_orders(self):
        orders = []
        is_kid = self._uses_kid_measurements(self.cleaned_data)
        # "No specific number" → the order has no number at all (left blank).
        number = self.cleaned_data.get('jersey_number') or ''
        for item_type in self.cleaned_data['item_types']:
            quantity = self.cleaned_data[f'quantity_{item_type}']
            order = JerseyOrder(
                user=self.user,
                for_person=self.cleaned_data['for_person'],
                gender=self.cleaned_data['gender'],
                wearer_name=self.cleaned_data['wearer_name'],
                item_type=item_type,
                size=self._size_for_item(item_type, is_kid),
                quantity=quantity,
                jersey_number=number,
                notes=self.cleaned_data.get('notes') or '',
            )
            order.full_clean()
            order.save()
            orders.append(order)
        # Set the shared reference for this wearer (picked number, or 3-digit code).
        JerseyOrder.sync_reference(self.user, self.cleaned_data['wearer_name'])
        return orders

    def _size_for_item(self, item_type, is_kid):
        if item_type in JerseyOrder.HEADWEAR_ITEMS:
            return JerseyOrder.FREE_SIZE
        if item_type in JerseyOrder.SHIRT_ITEMS:
            if is_kid:
                return (
                    'Kid custom shirt - '
                    f"full chest {self.cleaned_data['kid_shirt_full_chest']} in, "
                    f"half chest {self.cleaned_data['kid_shirt_half_chest']} in, "
                    f"length {self.cleaned_data['kid_shirt_length']} in, "
                    f"shoulder {self.cleaned_data['kid_shirt_shoulder']} in"
                )
            return self.cleaned_data['shirt_size']
        if item_type in JerseyOrder.PANT_ITEMS:
            if is_kid:
                return (
                    'Kid custom pant - '
                    f"length {self.cleaned_data['kid_pant_length']} in, "
                    f"relaxed waist {self.cleaned_data['kid_pant_relaxed_waist']} in, "
                    f"half hip {self.cleaned_data['kid_pant_half_hip']} in"
                )
            return self.cleaned_data['pant_size']
        return ''

    def item_rows(self):
        selected = set(self.data.getlist('item_types')) if self.is_bound else set()
        rows = []
        for code, label in JerseyOrder.ITEM_CHOICES:
            field_name = f'quantity_{code}'
            rows.append({
                'code': code,
                'label': label,
                'rate': JerseyOrder.rate_for(code),
                'checked': code in selected,
                'quantity_field': self[field_name],
            })
        return rows


class JerseyOrderWindowForm(forms.Form):
    is_enabled = forms.BooleanField(
        required=False,
        label='Use order close date',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-stone-300 text-pitch-600 focus:ring-pitch-500',
        }),
    )
    closes_at = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-input',
            'type': 'datetime-local',
        }, format='%Y-%m-%dT%H:%M'),
        label='Order close date',
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        initial = kwargs.pop('initial', {})
        if instance:
            initial.setdefault('is_enabled', instance.is_enabled)
            if instance.closes_at:
                initial.setdefault(
                    'closes_at',
                    timezone.localtime(instance.closes_at).strftime('%Y-%m-%dT%H:%M'),
                )
        super().__init__(*args, initial=initial, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_enabled') and not cleaned.get('closes_at'):
            self.add_error('closes_at', 'Choose an order close date.')
        return cleaned

    def save(self):
        window = self.instance or JerseyOrderWindow.objects.first() or JerseyOrderWindow()
        window.name = window.name or 'Jersey order window'
        window.is_enabled = self.cleaned_data.get('is_enabled', False)
        window.closes_at = self.cleaned_data.get('closes_at')
        window.opens_at = None
        window.full_clean()
        window.save()
        return window
