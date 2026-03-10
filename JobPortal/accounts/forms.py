from django import forms
from django.contrib.auth.models import User as AuthUser

from .models import (
    GENDER_CHOICES,
    ROLE_CHOICES,
    JobSeekerProfile,
    RecruiterProfile,
    User,
)


def _validate_pdf_file(upload):
    if not upload:
        return upload

    file_name = (upload.name or '').lower()
    content_type = getattr(upload, 'content_type', '')
    allowed_content_types = {'application/pdf', 'application/x-pdf'}

    if not file_name.endswith('.pdf'):
        raise forms.ValidationError("Resume must be a PDF file.")

    if content_type and content_type not in allowed_content_types:
        raise forms.ValidationError("Resume must be uploaded as a PDF file.")

    return upload


class RegistrationForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if AuthUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if AuthUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class UpdateUserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone_number',
            'email',
            'address',
            'city',
            'state',
            'country',
            'zip_code',
        ]
        widgets = {
            'address': forms.Textarea,
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class UpdateJobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            'profile_picture',
            'resume',
            'work_experience',
            'linkedin',
            'github',
        ]
        widgets = {
            'work_experience': forms.Textarea,
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        return _validate_pdf_file(resume)


class UpdateRecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = [
            'profile_picture',
            'experience',
            'company_position',
            'company_logo',
            'company_name',
            'company_website',
            'company_description',
            'company_address',
            'company_phone',
            'company_email',
        ]
        widgets = {
            'experience': forms.Textarea,
            'company_description': forms.Textarea,
            'company_address': forms.Textarea,
        }
