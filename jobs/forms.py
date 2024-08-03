from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import JobPost, JobApplication, CustomUser

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'description', 'company', 'location']

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['resume', 'cover_letter']
        widgets = {
            'resume': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super(JobApplicationForm, self).__init__(*args, **kwargs)
        self.fields['cover_letter'].required = False  # Make cover letter optional

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, required=True)

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

class JobSearchForm(forms.Form):
    query = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search for jobs...',
        'class': 'form-control'
    }))

class ResumeUploadForm(forms.Form):
    resume = forms.FileField(label='Upload Resume (PDF only)')
    job_id = forms.CharField(widget=forms.HiddenInput())

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This username is already taken.')
        return username
