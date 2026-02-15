from unittest.mock import patch

from django.contrib.auth.models import User as AuthUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from applications.models import Application
from jobs.models import Job, JobCategory
from . import views
from .models import JobSeekerProfile, RecruiterProfile, User


class AccountViewsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.recruiter_auth_user = AuthUser.objects.create_user(
            username='recruiter_user',
            email='recruiter@example.com',
            password='StrongPass123',
        )
        self.recruiter_user_profile = User.objects.create(
            user=self.recruiter_auth_user,
            role='recruiter',
            email='recruiter@example.com',
            phone_number='9999999999',
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user_profile=self.recruiter_user_profile
        )

        self.jobseeker_auth_user = AuthUser.objects.create_user(
            username='jobseeker_user',
            email='jobseeker@example.com',
            password='StrongPass123',
        )
        self.jobseeker_user_profile = User.objects.create(
            user=self.jobseeker_auth_user,
            role='jobseeker',
            email='jobseeker@example.com',
            phone_number='8888888888',
        )
        self.jobseeker_profile = JobSeekerProfile.objects.create(
            user=self.jobseeker_user_profile,
            work_experience='Built internal tools in Django.',
        )

        self.category = JobCategory.objects.get(code='it')

        self.job_1 = Job.objects.create(
            recruiter=self.recruiter_profile,
            title='Backend Engineer',
            job_type='full_time',
            job_category=self.category,
            job_description='Build APIs',
            company='Acme',
            location='Remote',
            salary='120000.00',
            education_requirements='Bachelors',
            experience_requirements='3 years',
            skills_required='Python, Django',
        )
        self.job_2 = Job.objects.create(
            recruiter=self.recruiter_profile,
            title='Frontend Engineer',
            job_type='full_time',
            job_category=self.category,
            job_description='Build UI',
            company='Acme',
            location='Remote',
            salary='110000.00',
            education_requirements='Bachelors',
            experience_requirements='2 years',
            skills_required='HTML, CSS, JS',
        )

        Application.objects.create(
            name='Applicant One',
            email='applicant1@example.com',
            resume=SimpleUploadedFile('resume1.pdf', b'pdf-content-1', content_type='application/pdf'),
            experience='2 years',
            job=self.job_1,
            recruiter=self.recruiter_profile,
        )
        Application.objects.create(
            name='Applicant Two',
            email='applicant2@example.com',
            resume=SimpleUploadedFile('resume2.pdf', b'pdf-content-2', content_type='application/pdf'),
            experience='4 years',
            job=self.job_2,
            recruiter=self.recruiter_profile,
        )

    def test_index_redirects_authenticated_users_to_home(self):
        self.client.login(username='recruiter_user', password='StrongPass123')

        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    @patch('accounts.views.render')
    def test_home_context_for_jobseeker(self, mock_render):
        mock_render.return_value = HttpResponse('ok')
        request = self.factory.get(reverse('home'))
        request.user = self.jobseeker_auth_user

        response = views.home(request)

        self.assertEqual(response.status_code, 200)
        render_args = mock_render.call_args[0]
        context = render_args[2]
        self.assertEqual(render_args[1], 'home.html')
        self.assertTrue(context['is_jobseeker'])
        self.assertFalse(context['is_recruiter'])
        self.assertEqual(context['jobs'].count(), 2)

    @patch('accounts.views.render')
    def test_home_context_for_recruiter(self, mock_render):
        mock_render.return_value = HttpResponse('ok')
        request = self.factory.get(reverse('home'))
        request.user = self.recruiter_auth_user

        response = views.home(request)

        self.assertEqual(response.status_code, 200)
        render_args = mock_render.call_args[0]
        context = render_args[2]
        self.assertFalse(context['is_jobseeker'])
        self.assertTrue(context['is_recruiter'])
        self.assertEqual(context['jobseekers'].count(), 1)

    @patch('accounts.views.render')
    def test_recruiter_dashboard_includes_count_metrics(self, mock_render):
        mock_render.return_value = HttpResponse('ok')
        request = self.factory.get(reverse('dashboard'))
        request.user = self.recruiter_auth_user

        response = views.dashboard(request)

        self.assertEqual(response.status_code, 200)
        render_args = mock_render.call_args[0]
        context = render_args[2]
        self.assertEqual(render_args[1], 'dashboard_Recruiter.html')
        self.assertEqual(context['job_post_count'], 2)
        self.assertEqual(context['application_count'], 2)
        self.assertEqual(context['profile_view_count'], 0)
        self.assertEqual(context['message_count'], 0)

    @patch('accounts.views.render')
    def test_recruiter_can_view_jobseeker_profile(self, mock_render):
        mock_render.return_value = HttpResponse('ok')
        request = self.factory.get(
            reverse('view_jobseeker_profile', args=[self.jobseeker_user_profile.id])
        )
        request.user = self.recruiter_auth_user

        response = views.view_jobseeker_profile(request, self.jobseeker_user_profile.id)

        self.assertEqual(response.status_code, 200)
        render_args = mock_render.call_args[0]
        self.assertEqual(render_args[1], 'jobseeker_profile_detail.html')
        context = render_args[2]
        self.assertEqual(context['jobseeker_user_profile'], self.jobseeker_user_profile)
        self.assertEqual(context['jobseeker_profile'], self.jobseeker_profile)

    def test_jobseeker_cannot_open_jobseeker_profile_detail(self):
        self.client.login(username='jobseeker_user', password='StrongPass123')

        response = self.client.get(
            reverse('view_jobseeker_profile', args=[self.jobseeker_user_profile.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('home'))
