from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from jobs.models import Job

from .forms import ApplicationForm


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

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.recruiter = job.recruiter
            application.save()
            messages.success(request, 'Application submitted successfully.')
            return redirect('home')
    else:
        form = ApplicationForm(
            initial={
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
        )

    return render(request, 'application_form.html', {'form': form, 'job': job})

