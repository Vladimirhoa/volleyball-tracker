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