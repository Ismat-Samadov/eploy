from django import forms
from .models import JobPost, JobApplication

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = ['title', 'description', 'company', 'location']

class JobApplicationForm(forms.ModelForm):
    cv = forms.FileField(label='Upload your CV', required=True)

    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'cv']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(JobApplicationForm, self).__init__(*args, **kwargs)
        self.fields['cover_letter'].required = False

class JobSearchForm(forms.Form):
    query = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search for jobs...',
        'class': 'form-control'
    }))

class ResumeUploadForm(forms.Form):
    resume = forms.FileField()
