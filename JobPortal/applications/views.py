from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import JobSeekerProfile, RecruiterProfile
from jobs.models import Job

from .forms import ApplicationForm
from .models import Application


def _get_jobseeker_applications(profile):
    return Application.objects.select_related(
        'job',
        'recruiter__user_profile__user',
        'applicant__user',
    ).filter(
        Q(applicant=profile) |
        Q(applicant__isnull=True, email__iexact=profile.email)
    ).distinct()


def _get_recruiter_profile(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, 'Profile record does not exist for this account.')
        return None, redirect('home')

    if profile.role != 'recruiter':
        messages.error(request, 'Only recruiters can manage applications.')
        return None, redirect('home')

    recruiter_profile = get_object_or_404(RecruiterProfile, user_profile=profile)
    return recruiter_profile, None


@login_required(login_url='login')
def apply_job(request, job_id):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, 'Profile record does not exist for this account.')
        return redirect('home')

    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('home')

    job = get_object_or_404(Job.objects.select_related('recruiter'), pk=job_id)
    jobseeker_profile, _ = JobSeekerProfile.objects.get_or_create(user=profile)

    if _get_jobseeker_applications(profile).filter(job=job).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('my_applications')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            if not application.resume and jobseeker_profile.resume:
                application.resume = jobseeker_profile.resume
            if not application.resume:
                form.add_error('resume', 'Please upload a resume or add one to your profile first.')
            else:
                application.applicant = profile
                application.job = job
                application.recruiter = job.recruiter
                application.save()
                messages.success(request, 'Application submitted successfully.')
                return redirect('home')
    else:
        form = ApplicationForm(
            initial={
                'name': profile.get_full_name().strip() or request.user.username,
                'email': profile.email or request.user.email,
                'experience': jobseeker_profile.work_experience,
            }
        )

    return render(
        request,
        'application_form.html',
        {
            'form': form,
            'job': job,
            'page_title': f'Apply for {job.title}',
            'submit_label': 'Submit Application',
        },
    )


@login_required(login_url='login')
def my_applications(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, 'Profile record does not exist for this account.')
        return redirect('home')

    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can view their applications.')
        return redirect('home')

    applications = _get_jobseeker_applications(profile)
    return render(
        request,
        'my_applications.html',
        {
            'applications': applications,
            'application_count': applications.count(),
        },
    )


@login_required(login_url='login')
def edit_application(request, application_id):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, 'Profile record does not exist for this account.')
        return redirect('home')

    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can edit applications.')
        return redirect('home')

    application = get_object_or_404(_get_jobseeker_applications(profile), pk=application_id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application updated successfully.')
            return redirect('my_applications')
    else:
        form = ApplicationForm(instance=application)

    return render(
        request,
        'application_form.html',
        {
            'form': form,
            'job': application.job,
            'page_title': f'Edit Application for {application.job.title}',
            'submit_label': 'Save Changes',
            'application': application,
        },
    )


@login_required(login_url='login')
def delete_application(request, application_id):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, 'Profile record does not exist for this account.')
        return redirect('home')

    if profile.role != 'jobseeker':
        messages.error(request, 'Only job seekers can delete applications.')
        return redirect('home')

    application = get_object_or_404(_get_jobseeker_applications(profile), pk=application_id)

    if request.method == 'POST':
        job_title = application.job.title
        application.delete()
        messages.success(request, f'Application for "{job_title}" deleted successfully.')

    return redirect('my_applications')


@login_required(login_url='login')
def recruiter_applications(request):
    recruiter_profile, error_response = _get_recruiter_profile(request)
    if error_response:
        return error_response

    applications = Application.objects.select_related(
        'job',
        'applicant__user',
    ).filter(recruiter=recruiter_profile)

    return render(
        request,
        'recruiter_applications.html',
        {
            'applications': applications,
            'application_count': applications.count(),
        },
    )


@login_required(login_url='login')
def update_application_status(request, application_id, status):
    recruiter_profile, error_response = _get_recruiter_profile(request)
    if error_response:
        return error_response

    if request.method != 'POST':
        return redirect('recruiter_applications')

    if status not in {
        Application.STATUS_ACCEPTED,
        Application.STATUS_REJECTED,
    }:
        messages.error(request, 'Invalid application status.')
        return redirect('recruiter_applications')

    application = get_object_or_404(
        Application,
        pk=application_id,
        recruiter=recruiter_profile,
    )
    application.status = status
    application.save(update_fields=['status'])

    messages.success(
        request,
        f'Application for "{application.job.title}" marked as {application.get_status_display().lower()}.',
    )
    return redirect('recruiter_applications')

