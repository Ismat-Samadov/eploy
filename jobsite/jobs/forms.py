# froms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import JobPost, JobApplication
from users.models import CustomUser 

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'description', 'company', 'location']

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['resume', 'cover_letter']

class HRUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, required=True)

    class Meta:
        model = CustomUser  # Use CustomUser model
        fields = ('username', 'email', 'user_type', 'password1', 'password2')

    def save(self, commit=True):
        user = super(HRUserCreationForm, self).save(commit=False)
        if commit:
            user.save()
        return user
