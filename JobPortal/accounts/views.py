from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import UserProfile , RecruiterProfile, JobSeekerProfile 
from .forms import RegistrationForm , UpdateUserProfileForm , UpdateJobSeekerProfileForm , UpdateRecruiterProfileForm
from django.contrib import messages
from jobs.models import Job
from applications.models import Application


def _display_name(user_profile):
    full_name = user_profile.get_full_name().strip()
    return full_name or user_profile.user.username


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


def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'index.html')

@login_required(login_url='login')
def home(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile record does not exist for this account.')
        auth_logout(request)
        return redirect('login')

    is_jobseeker = user_profile.role == 'jobseeker'
    is_recruiter = user_profile.role == 'recruiter'
    search_query = request.GET.get('q', '').strip()

    context = {
        'user_profile': user_profile,
        'is_jobseeker': is_jobseeker,
        'is_recruiter': is_recruiter,
        'jobs': Job.objects.none(),
        'jobseekers': UserProfile.objects.none(),
        'jobseeker_cards': [],
        'applied_job_ids': [],
        'search_query': search_query,
        'search_result_count': 0,
        'has_active_filters': bool(search_query),
    }

    if is_jobseeker:
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
        applied_job_ids = list(
            Application.objects.filter(
                Q(applicant=user_profile) |
                Q(applicant__isnull=True, email__iexact=user_profile.email)
            ).values_list('job_id', flat=True)
        )
        context.update(
            {
                'jobs': jobs,
                'applied_job_ids': applied_job_ids,
                'search_result_count': jobs.count(),
            }
        )
    elif is_recruiter:
        jobseekers = (
            UserProfile.objects.filter(role='jobseeker')
            .select_related('user')
            .order_by('-id')
        )
        jobseeker_cards = []
        if search_query:
            jobseekers = jobseekers.filter(
                Q(user__username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        for seeker in jobseekers:
            try:
                seeker_profile = seeker.jobseeker_profile
            except JobSeekerProfile.DoesNotExist:
                seeker_profile = None
            jobseeker_cards.append(
                {
                    'profile': seeker,
                    'jobseeker_profile': seeker_profile,
                    'display_name': _display_name(seeker),
                }
            )
        context.update(
            {
                'jobseekers': jobseekers,
                'jobseeker_cards': jobseeker_cards,
                'search_result_count': len(jobseeker_cards),
            }
        )

    return render(request, 'home.html', context)


@login_required(login_url='login')
def view_jobseeker_profile(request, profile_id):
    try:
        viewer_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile record does not exist for this account.')
        auth_logout(request)
        return redirect('login')

    if viewer_profile.role != 'recruiter':
        messages.error(request, 'Only recruiters can view jobseeker profiles.')
        return redirect('home')

    jobseeker_user_profile = get_object_or_404(
        UserProfile.objects.select_related('user').filter(role='jobseeker'),
        pk=profile_id,
    )
    jobseeker_profile, _ = JobSeekerProfile.objects.get_or_create(user=jobseeker_user_profile)

    full_name = " ".join(
        value for value in [
            jobseeker_user_profile.first_name,
            jobseeker_user_profile.middle_name,
            jobseeker_user_profile.last_name,
        ]
        if value
    ).strip()
    if not full_name:
        full_name = jobseeker_user_profile.user.username

    location_parts = [
        jobseeker_user_profile.city,
        jobseeker_user_profile.state,
        jobseeker_user_profile.country,
    ]
    location = ", ".join(part for part in location_parts if part) or "Not provided"

    context = {
        'jobseeker_user_profile': jobseeker_user_profile,
        'jobseeker_profile': jobseeker_profile,
        'full_name': full_name,
        'location': location,
    }
    return render(request, 'jobseeker_profile_detail.html', context)

@login_required(login_url='login')
def dashboard(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "Profile record does not exist for this account.")
        return redirect('home')
    if user_profile.role == 'recruiter':

        recruiter_profile, _ = RecruiterProfile.objects.get_or_create(
            user_profile=user_profile
        )

        my_jobs = Job.objects.filter(
            recruiter=recruiter_profile
        ).order_by('-created_at')

        job_post_count = my_jobs.count()
        application_count = Application.objects.filter(recruiter=recruiter_profile).count()
        profile_completion = _calculate_profile_completion(user_profile, recruiter_profile)

        context = {
            'user_profile': user_profile,
            'display_name': _display_name(user_profile),
            'recruiter_profile': recruiter_profile,
            'my_jobs': my_jobs,
            'job_post_count': job_post_count,
            'application_count': application_count,
            'profile_completion': profile_completion,
            'profile_view_count': 0,
            'message_count': 0,
        }

        return render(request, 'dashboard_Recruiter.html', context)

    elif user_profile.role == 'jobseeker':

        jobseeker_profile, _ = JobSeekerProfile.objects.get_or_create(
            user=user_profile
        )
        applications = Application.objects.select_related(
            'job',
            'recruiter__user_profile__user',
        ).filter(
            Q(applicant=user_profile) |
            Q(applicant__isnull=True, email__iexact=user_profile.email)
        ).distinct()
        profile_completion = _calculate_profile_completion(user_profile, jobseeker_profile)

        context = {
            'user_profile': user_profile,
            'display_name': _display_name(user_profile),
            'jobseeker_profile': jobseeker_profile,
            'application_count': applications.count(),
            'recent_applications': applications[:5],
            'profile_completion': profile_completion,
        }

        return render(request, 'dashboard_JobSeeker.html', context)
    messages.error(request, "Invalid role for dashboard.")
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            gender = form.cleaned_data['gender']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            # Check if passwords match
            if password != confirm_password:
                return render(request, 'register.html', {
                    'form': form,
                    'error': 'Passwords do not match'
                })

            # Check if username already exists
            if AuthUser.objects.filter(username=username).exists():
                return render(request, 'register.html', {
                    'form': form,
                    'error': 'Username already exists'
                })

            # Check if email already exists
            if AuthUser.objects.filter(email=email).exists():
                return render(request, 'register.html', {
                    'form': form,
                    'error': 'Email already exists'
                })

            # Create the user
            auth_user = AuthUser.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create the user profile
            profile = UserProfile.objects.create(
                user=auth_user,
                role=role,
                email=email,
                phone_number=phone_number,
                gender=gender
            )

            if role == 'recruiter':
                RecruiterProfile.objects.create(
                    user_profile=profile
                )
            else:
                JobSeekerProfile.objects.create(
                    user=profile
                )

            request.session['role'] = role

            # Log the user in
            auth_login(request, auth_user)
            return redirect('home')
        else:
            # Form is invalid
            return render(request, 'register.html', {
                'form': form,
                'error': 'Please correct the errors below'
            })

    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not all([username, password]):
            return render(request, 'login.html', {'error': 'All fields are required'})

        # Authenticate the user
        auth_user = authenticate(request, username=username, password=password)

        if auth_user is None:
            return render(request, 'login.html', {'error': 'Invalid username or password'})

        # Log the user in
        auth_login(request, auth_user)
        if hasattr(auth_user, 'profile'):
            request.session['role'] = auth_user.profile.role
        return redirect('home')
    
    return render(request, 'login.html')

def logout(request):
    auth_logout(request)
    return redirect('index')

@login_required(login_url='login')
def update_profile(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile record does not exist for this account.')
        return redirect('home')
    jobseeker_form = None
    recruiter_form = None

    if request.method == 'POST':
        user_form = UpdateUserProfileForm(request.POST, instance=user_profile)

        if user_profile.role == 'jobseeker':
            jobseeker_profile, _ = JobSeekerProfile.objects.get_or_create(user=user_profile)
            jobseeker_form = UpdateJobSeekerProfileForm(
                request.POST,
                request.FILES,
                instance=jobseeker_profile,
            )
            if user_form.is_valid() and jobseeker_form.is_valid():
                user_form.save()
                jobseeker_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('home')
        elif user_profile.role == 'recruiter':
            recruiter_profile, _ = RecruiterProfile.objects.get_or_create(user_profile=user_profile)
            recruiter_form = UpdateRecruiterProfileForm(
                request.POST,
                request.FILES,
                instance=recruiter_profile,
            )
            if user_form.is_valid() and recruiter_form.is_valid():
                user_form.save()
                recruiter_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('home')
        else:
            messages.error(request, 'Invalid role for profile update.')
            return redirect('home')
    else:
        user_form = UpdateUserProfileForm(instance=user_profile)

        if user_profile.role == 'jobseeker':
            jobseeker_profile, _ = JobSeekerProfile.objects.get_or_create(user=user_profile)
            jobseeker_form = UpdateJobSeekerProfileForm(instance=jobseeker_profile)
        elif user_profile.role == 'recruiter':
            recruiter_profile, _ = RecruiterProfile.objects.get_or_create(user_profile=user_profile)
            recruiter_form = UpdateRecruiterProfileForm(instance=recruiter_profile)
        else:
            messages.error(request, 'Invalid role for profile update.')
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
