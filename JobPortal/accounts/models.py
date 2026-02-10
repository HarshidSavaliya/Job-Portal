from django.db import models
from django.contrib.auth.models import User as AuthUser

ROLE_CHOICES = (
    ('jobseeker', 'Job Seeker'),
    ('recruiter', 'Recruiter'),
)

GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
)


class User(models.Model):
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jobseeker')
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')

    # Personal details
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # Contact details
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='jobseeker_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)

    # Resume
    resume = models.FileField(upload_to='resumes/', blank=True)
    work_experience = models.TextField(blank=True)

    # Links
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    
    def __str__(self):
        return f"{self.user.user.username}'s Job Seeker Profile"


class RecruiterProfile(models.Model):
    user_profile = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)

    # Details
    experience = models.TextField(blank=True)
    company_position = models.CharField(max_length=200, blank=True)

    # Company
    company_logo = models.ImageField(upload_to='company_logos/', blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    company_website = models.URLField(blank=True)
    company_description = models.TextField(blank=True)
    company_address = models.TextField(blank=True)
    company_phone = models.CharField(max_length=20, blank=True)
    company_email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.user_profile.user.username}'s Recruiter Profile"


# Backward-compatible alias for existing imports/usages.
UserProfile = User
