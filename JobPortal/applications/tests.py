from django.contrib.auth.models import User as AuthUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import RecruiterProfile, User
from jobs.models import Job, JobCategory

from .models import Application


class ApplyJobViewTests(TestCase):
    def setUp(self):
        self.recruiter_auth_user = AuthUser.objects.create_user(
            username='recruiter1',
            email='recruiter1@example.com',
            password='StrongPass123',
        )
        self.recruiter_user_profile = User.objects.create(
            user=self.recruiter_auth_user,
            role='recruiter',
            email='recruiter1@example.com',
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user_profile=self.recruiter_user_profile
        )

        self.jobseeker_auth_user = AuthUser.objects.create_user(
            username='jobseeker1',
            email='jobseeker1@example.com',
            password='StrongPass123',
        )
        self.jobseeker_user_profile = User.objects.create(
            user=self.jobseeker_auth_user,
            role='jobseeker',
            email='jobseeker1@example.com',
        )

        self.category = JobCategory.objects.get(code='it')
        self.job = Job.objects.create(
            recruiter=self.recruiter_profile,
            title='Python Developer',
            job_type='full_time',
            job_category=self.category,
            job_description='Develop APIs',
            company='Acme Corp',
            location='Remote',
            salary='120000.00',
            education_requirements='Bachelors',
            experience_requirements='2+ years',
            skills_required='Python, Django',
        )
        self.apply_url = reverse('apply_job', args=[self.job.id])

    def _resume_file(self):
        return SimpleUploadedFile(
            'resume.pdf',
            b'%PDF-1.4 fake resume content',
            content_type='application/pdf',
        )

    def test_apply_job_requires_login(self):
        response = self.client.get(self.apply_url)

        expected_login_url = f"{reverse('login')}?next={self.apply_url}"
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], expected_login_url)

    def test_recruiter_cannot_apply_to_job(self):
        self.client.login(username='recruiter1', password='StrongPass123')

        response = self.client.get(self.apply_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('home'))
        self.assertEqual(Application.objects.count(), 0)

    def test_jobseeker_apply_creates_application_with_correct_recruiter(self):
        self.client.login(username='jobseeker1', password='StrongPass123')

        response = self.client.post(
            self.apply_url,
            {
                'name': 'Job Seeker',
                'email': 'jobseeker1@example.com',
                'resume': self._resume_file(),
                'experience': 'Built multiple Django projects.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('home'))
        self.assertEqual(Application.objects.count(), 1)

        application = Application.objects.get()
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.recruiter, self.recruiter_profile)
