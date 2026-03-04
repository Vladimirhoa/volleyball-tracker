from django import forms
from .models import Match
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['title', 'description', 'my_score', 'opponent_score', 'date']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ""
        if 'password1' in self.fields:
            self.fields['password1'].help_text = ""
        if 'password2' in self.fields:
            self.fields['password2'].help_text = ""