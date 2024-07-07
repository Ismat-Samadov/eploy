# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=[('HR', 'HR/Recruiter'), ('Candidate', 'Candidate')], required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user
