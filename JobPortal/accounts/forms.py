from django import forms
from .models import (
    GENDER_CHOICES,
    ROLE_CHOICES,
    JobSeekerProfile,
    RecruiterProfile,
    User,
)

class RegistrationForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

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
