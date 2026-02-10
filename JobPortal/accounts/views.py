from django.shortcuts import  render, redirect
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import UserProfile , RecruiterProfile, JobSeekerProfile 
from .forms import RegistrationForm 
from django.contrib import messages

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

    jobs = Job.objects.none()
    jobseekers = UserProfile.objects.none()
    jobseeker_cards = []

    if is_jobseeker:
        jobs = Job.objects.select_related('recruiter__user_profile__user').order_by('-created_at')
    elif is_recruiter:
        jobseekers = UserProfile.objects.filter(role='jobseeker').select_related('user').order_by('-id')
        for seeker in jobseekers:
            try:
                seeker_profile = seeker.jobseeker_profile
            except JobSeekerProfile.DoesNotExist:
                seeker_profile = None
            jobseeker_cards.append(
                {
                    'profile': seeker,
                    'jobseeker_profile': seeker_profile,
                }
            )

    context = {
        'user_profile': user_profile,
        'is_jobseeker': is_jobseeker,
        'is_recruiter': is_recruiter,
        'jobs': jobs,
        'jobseekers': jobseekers,
        'jobseeker_cards': jobseeker_cards,
        }
    return render(request, 'home.html', context)

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

