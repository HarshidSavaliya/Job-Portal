from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as AuthUser
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from applications.models import Application
from jobs.models import Job

from .forms import (
    LoginForm,
    RegistrationForm,
    UpdateJobSeekerProfileForm,
    UpdateRecruiterProfileForm,
    UpdateUserProfileForm,
)
from .models import JobSeekerProfile, RecruiterProfile, UserProfile


def _resolve_request_profile(request, *, missing_redirect='home', logout_on_missing=False):
    try:
        return request.user.profile, None
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile record does not exist for this account.')
        if logout_on_missing:
            auth_logout(request)
        return None, redirect(missing_redirect)


def _display_name(user_profile):
    return user_profile.get_full_name() or user_profile.user.username


def _get_location_text(user_profile):
    location_parts = [user_profile.city, user_profile.state, user_profile.country]
    return ", ".join(part for part in location_parts if part) or "Not provided"


def _get_jobseeker_profile(user_profile):
    return JobSeekerProfile.objects.get_or_create(user=user_profile)[0]


def _get_recruiter_profile(user_profile):
    return RecruiterProfile.objects.get_or_create(user_profile=user_profile)[0]


def _get_jobseeker_applications(user_profile):
    return Application.objects.select_related(
        'job',
        'recruiter__user_profile__user',
    ).filter(
        Q(applicant=user_profile) |
        Q(applicant__isnull=True, email__iexact=user_profile.email)
    ).distinct()


def _calculate_profile_completion(user_profile, detail_profile=None):
    fields = [
        user_profile.first_name,
        user_profile.last_name,
        user_profile.email,
        user_profile.phone_number,
        user_profile.gender,
        user_profile.address,
        user_profile.city,
        user_profile.state,
        user_profile.country,
        user_profile.zip_code,
    ]

    if isinstance(detail_profile, JobSeekerProfile):
        fields.extend(
            [
                detail_profile.profile_picture,
                detail_profile.resume,
                detail_profile.work_experience,
                detail_profile.linkedin,
                detail_profile.github,
            ]
        )
    elif isinstance(detail_profile, RecruiterProfile):
        fields.extend(
            [
                detail_profile.profile_picture,
                detail_profile.experience,
                detail_profile.company_position,
                detail_profile.company_logo,
                detail_profile.company_name,
                detail_profile.company_website,
                detail_profile.company_description,
                detail_profile.company_address,
                detail_profile.company_phone,
                detail_profile.company_email,
            ]
        )

    completed_fields = sum(1 for value in fields if value)
    return int((completed_fields / len(fields)) * 100) if fields else 0


def _build_jobseeker_home_context(user_profile, search_query):
    jobs = Job.objects.select_related(
        'recruiter__user_profile__user',
        'job_category',
    ).order_by('-created_at')

    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(job_category__name__icontains=search_query)
        )

    applications = _get_jobseeker_applications(user_profile)
    return {
        'jobs': jobs,
        'applied_job_ids': list(applications.values_list('job_id', flat=True)),
        'search_result_count': jobs.count(),
    }


def _build_recruiter_home_context(search_query):
    jobseekers = UserProfile.objects.filter(role='jobseeker').select_related('user').order_by('-id')

    if search_query:
        jobseekers = jobseekers.filter(
            Q(user__username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    jobseeker_cards = []
    for seeker in jobseekers:
        jobseeker_cards.append(
            {
                'profile': seeker,
                'jobseeker_profile': getattr(seeker, 'jobseeker_profile', None),
                'display_name': _display_name(seeker),
            }
        )

    return {
        'jobseekers': jobseekers,
        'jobseeker_cards': jobseeker_cards,
        'search_result_count': len(jobseeker_cards),
    }


def _build_home_context(user_profile, search_query):
    context = {
        'user_profile': user_profile,
        'is_jobseeker': user_profile.role == 'jobseeker',
        'is_recruiter': user_profile.role == 'recruiter',
        'jobs': Job.objects.none(),
        'jobseekers': UserProfile.objects.none(),
        'jobseeker_cards': [],
        'applied_job_ids': [],
        'search_query': search_query,
        'search_result_count': 0,
        'has_active_filters': bool(search_query),
    }

    if user_profile.role == 'jobseeker':
        context.update(_build_jobseeker_home_context(user_profile, search_query))
    elif user_profile.role == 'recruiter':
        context.update(_build_recruiter_home_context(search_query))

    return context


def _build_recruiter_dashboard(user_profile):
    recruiter_profile = _get_recruiter_profile(user_profile)
    my_jobs = Job.objects.filter(recruiter=recruiter_profile).order_by('-created_at')

    context = {
        'user_profile': user_profile,
        'display_name': _display_name(user_profile),
        'recruiter_profile': recruiter_profile,
        'my_jobs': my_jobs,
        'job_post_count': my_jobs.count(),
        'application_count': Application.objects.filter(recruiter=recruiter_profile).count(),
        'profile_completion': _calculate_profile_completion(user_profile, recruiter_profile),
        'profile_view_count': 0,
        'message_count': 0,
    }
    return 'dashboard_Recruiter.html', context


def _build_jobseeker_dashboard(user_profile):
    jobseeker_profile = _get_jobseeker_profile(user_profile)
    applications = _get_jobseeker_applications(user_profile)

    context = {
        'user_profile': user_profile,
        'display_name': _display_name(user_profile),
        'jobseeker_profile': jobseeker_profile,
        'application_count': applications.count(),
        'recent_applications': applications[:5],
        'profile_completion': _calculate_profile_completion(user_profile, jobseeker_profile),
    }
    return 'dashboard_JobSeeker.html', context


def _create_user_profile(auth_user, cleaned_data):
    profile = UserProfile.objects.create(
        user=auth_user,
        role=cleaned_data['role'],
        email=cleaned_data['email'],
        phone_number=cleaned_data['phone_number'],
        gender=cleaned_data['gender'],
    )

    if profile.role == 'recruiter':
        RecruiterProfile.objects.create(user_profile=profile)
    else:
        JobSeekerProfile.objects.create(user=profile)

    return profile


def _get_update_profile_forms(user_profile, *, data=None, files=None):
    user_form = UpdateUserProfileForm(data=data, instance=user_profile)

    if user_profile.role == 'jobseeker':
        return (
            user_form,
            UpdateJobSeekerProfileForm(
                data=data,
                files=files,
                instance=_get_jobseeker_profile(user_profile),
            ),
            None,
        )

    if user_profile.role == 'recruiter':
        return (
            user_form,
            None,
            UpdateRecruiterProfileForm(
                data=data,
                files=files,
                instance=_get_recruiter_profile(user_profile),
            ),
        )

    return user_form, None, None


def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'index.html')


@login_required(login_url='login')
def home(request):
    user_profile, error_response = _resolve_request_profile(
        request,
        missing_redirect='login',
        logout_on_missing=True,
    )
    if error_response:
        return error_response

    context = _build_home_context(user_profile, request.GET.get('q', '').strip())
    return render(request, 'home.html', context)


@login_required(login_url='login')
def view_jobseeker_profile(request, profile_id):
    viewer_profile, error_response = _resolve_request_profile(
        request,
        missing_redirect='login',
        logout_on_missing=True,
    )
    if error_response:
        return error_response

    if viewer_profile.role != 'recruiter':
        messages.error(request, 'Only recruiters can view jobseeker profiles.')
        return redirect('home')

    jobseeker_user_profile = get_object_or_404(
        UserProfile.objects.select_related('user').filter(role='jobseeker'),
        pk=profile_id,
    )

    context = {
        'jobseeker_user_profile': jobseeker_user_profile,
        'jobseeker_profile': _get_jobseeker_profile(jobseeker_user_profile),
        'full_name': _display_name(jobseeker_user_profile),
        'location': _get_location_text(jobseeker_user_profile),
    }
    return render(request, 'jobseeker_profile_detail.html', context)


@login_required(login_url='login')
def dashboard(request):
    user_profile, error_response = _resolve_request_profile(request)
    if error_response:
        return error_response

    if user_profile.role == 'recruiter':
        template_name, context = _build_recruiter_dashboard(user_profile)
        return render(request, template_name, context)

    if user_profile.role == 'jobseeker':
        template_name, context = _build_jobseeker_dashboard(user_profile)
        return render(request, template_name, context)

    messages.error(request, 'Invalid role for dashboard.')
    return redirect('home')


def register(request):
    form = RegistrationForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            auth_user = AuthUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            profile = _create_user_profile(auth_user, form.cleaned_data)
            request.session['role'] = profile.role
            auth_login(request, auth_user)
            return redirect('home')

        return render(
            request,
            'register.html',
            {
                'form': form,
                'error': 'Please correct the errors below',
            },
        )

    return render(request, 'register.html', {'form': form})


def login(request):
    form = LoginForm(request.POST or None)
    error = None

    if request.method == 'POST':
        if not form.is_valid():
            error = 'All fields are required'
        else:
            auth_user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )

            if auth_user is None:
                error = 'Invalid username or password'
            else:
                auth_login(request, auth_user)
                if hasattr(auth_user, 'profile'):
                    request.session['role'] = auth_user.profile.role
                return redirect('home')

    context = {'form': form}
    if error:
        context['error'] = error
    return render(request, 'login.html', context)


def logout(request):
    auth_logout(request)
    return redirect('index')


@login_required(login_url='login')
def update_profile(request):
    user_profile, error_response = _resolve_request_profile(request)
    if error_response:
        return error_response

    user_form, jobseeker_form, recruiter_form = _get_update_profile_forms(
        user_profile,
        data=request.POST or None,
        files=request.FILES or None,
    )
    detail_form = jobseeker_form or recruiter_form

    if detail_form is None:
        messages.error(request, 'Invalid role for profile update.')
        return redirect('home')

    if request.method == 'POST' and user_form.is_valid() and detail_form.is_valid():
        user_form.save()
        detail_form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('home')

    return render(
        request,
        'update_profile.html',
        {
            'user_form': user_form,
            'jobseeker_form': jobseeker_form,
            'recruiter_form': recruiter_form,
        },
    )
