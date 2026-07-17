from django import forms

from .models import JerseyOrder


class JerseyOrderForm(forms.ModelForm):
    item_types = forms.MultipleChoiceField(
        choices=JerseyOrder.ITEM_CHOICES,
        error_messages={'required': 'Choose at least one item.'},
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
            }),
            'jersey_number': forms.TextInput(attrs={
                'class': 'form-input',
                'maxlength': '3',
                'inputmode': 'numeric',
                'placeholder': 'e.g. 7',
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
                min_value=1,
                widget=forms.NumberInput(attrs={
                    'class': 'form-input text-center',
                    'min': '1',
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
            if not cleaned.get(field_name):
                self.add_error(field_name, 'Enter quantity.')
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
                jersey_number=self.cleaned_data.get('jersey_number') or '',
                notes=self.cleaned_data.get('notes') or '',
            )
            order.full_clean()
            order.save()
            orders.append(order)
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
