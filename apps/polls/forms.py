from django import forms
from .models import Poll


class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['question', 'is_open']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-green-600'}),
        }
