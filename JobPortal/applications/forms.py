from django import forms
from .models import Application


def _validate_pdf_file(upload):
    if not upload:
        return upload

    file_name = (upload.name or '').lower()
    content_type = getattr(upload, 'content_type', '')
    allowed_content_types = {'application/pdf', 'application/x-pdf'}

    if not file_name.endswith('.pdf'):
        raise forms.ValidationError('Resume must be a PDF file.')

    if content_type and content_type not in allowed_content_types:
        raise forms.ValidationError('Resume must be uploaded as a PDF file.')

    return upload


class ApplicationForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    resume = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control-file',
                'accept': '.pdf,application/pdf',
            }
        )
    )

    experience = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Application
        fields = ['name', 'email', 'resume', 'experience']

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        return _validate_pdf_file(resume)

    def clean(self):
        cleaned_data = super().clean()
        resume = cleaned_data.get('resume')

        if not resume and not (self.instance and self.instance.pk and self.instance.resume):
            self.add_error('resume', 'Please upload a resume.')

        return cleaned_data
