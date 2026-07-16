from django import forms

from .models import JerseyOrder


class JerseyOrderForm(forms.ModelForm):
    item_types = forms.MultipleChoiceField(
        choices=JerseyOrder.ITEM_CHOICES,
        error_messages={'required': 'Choose at least one item.'},
    )

    class Meta:
        model = JerseyOrder
        fields = [
            'for_person',
            'gender',
            'wearer_name',
            'size',
            'jersey_number',
            'notes',
        ]
        widgets = {
            'for_person': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'wearer_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Name on jersey / wearer name',
            }),
            'size': forms.Select(attrs={'class': 'form-select'}),
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
        size = cleaned.get('size')
        for item_type in item_types:
            field_name = f'quantity_{item_type}'
            if not cleaned.get(field_name):
                self.add_error(field_name, 'Enter quantity.')
        if size == JerseyOrder.FREE_SIZE and any(
            item_type not in JerseyOrder.HEADWEAR_ITEMS for item_type in item_types
        ):
            self.add_error('size', 'Free size is only for cap/hat. Choose a numeric size for shirts, pants or shorts.')
        return cleaned

    def clean_jersey_number(self):
        number = (self.cleaned_data.get('jersey_number') or '').strip()
        if not number:
            return ''
        if not number.isdigit():
            raise forms.ValidationError('Use numbers only.')
        return str(int(number))

    def save_orders(self):
        orders = []
        for item_type in self.cleaned_data['item_types']:
            quantity = self.cleaned_data[f'quantity_{item_type}']
            order = JerseyOrder(
                user=self.user,
                for_person=self.cleaned_data['for_person'],
                gender=self.cleaned_data['gender'],
                wearer_name=self.cleaned_data['wearer_name'],
                item_type=item_type,
                size=self.cleaned_data['size'],
                quantity=quantity,
                jersey_number=self.cleaned_data.get('jersey_number') or '',
                notes=self.cleaned_data.get('notes') or '',
            )
            order.full_clean()
            order.save()
            orders.append(order)
        return orders

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
