from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    resume = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )

    experience = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Application
        fields = ['name', 'email', 'resume', 'experience']
