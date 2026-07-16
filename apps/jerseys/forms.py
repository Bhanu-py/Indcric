from django import forms

from .models import JerseyOrder


class JerseyOrderForm(forms.ModelForm):
    class Meta:
        model = JerseyOrder
        fields = [
            'for_person',
            'gender',
            'wearer_name',
            'item_type',
            'size',
            'quantity',
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
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'inputmode': 'numeric',
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

    def clean_jersey_number(self):
        number = (self.cleaned_data.get('jersey_number') or '').strip()
        if not number:
            return ''
        if not number.isdigit():
            raise forms.ValidationError('Use numbers only.')
        return str(int(number))

    def save(self, commit=True):
        order = super().save(commit=False)
        if self.user and not order.user_id:
            order.user = self.user
        if commit:
            order.full_clean()
            order.save()
        return order
