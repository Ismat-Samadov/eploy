from django import forms
from .models import JobPost, JobApplication

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'description', 'company', 'location']

class JobApplicationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=255, label='Full Name', required=True)
    email = forms.EmailField(label='Email', required=True)
    phone = forms.CharField(max_length=15, label='Phone', required=True)
    resume = forms.FileField(label='Upload your CV', required=True)

    class Meta:
        model = JobApplication
        fields = ['full_name', 'email', 'phone', 'cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        

class JobSearchForm(forms.Form):
    query = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search for jobs...',
        'class': 'form-control'
    }))

class ResumeUploadForm(forms.Form):
    resume = forms.FileField()
