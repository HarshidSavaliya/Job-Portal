from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import JobForm
from .models import Job
from accounts.models import RecruiterProfile


JOB_FORM_FIELDS = (
    'title',
    'job_type',
    'job_category',
    'job_description',
    'company',
    'location',
    'salary',
    'education_requirements',
    'experience_requirements',
    'skills_required',
)


def _get_recruiter_profile_or_none(user):
    try:
        return RecruiterProfile.objects.get(user_profile__user=user)
    except RecruiterProfile.DoesNotExist:
        return None


@login_required(login_url='login')
def create_post_job(request):
    recruiter_profile = _get_recruiter_profile_or_none(request.user)
    if recruiter_profile is None:
        messages.error(request, 'You need to be a recruiter to post a job.')
        return redirect('home')

    if request.method == 'POST':
        form = JobForm(request.POST)

        if form.is_valid():
            Job.objects.create(recruiter=recruiter_profile, **form.cleaned_data)
            messages.success(request, 'Job posted successfully.')
            return redirect('home')
    else:
        form = JobForm()

    return render(
        request,
        'post_job.html',
        {
            'form': form,
            'form_title': 'Post a Job',
            'submit_label': 'Post Job',
        },
    )


@login_required(login_url='login')
def edit_job_post(request, job_id):
    recruiter_profile = _get_recruiter_profile_or_none(request.user)
    if recruiter_profile is None:
        messages.error(request, 'You need to be a recruiter to edit a job post.')
        return redirect('home')

    job = get_object_or_404(Job, pk=job_id, recruiter=recruiter_profile)

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            for field_name in JOB_FORM_FIELDS:
                setattr(job, field_name, form.cleaned_data[field_name])
            job.save(update_fields=list(JOB_FORM_FIELDS) + ['updated_at'])
            messages.success(request, 'Job post updated successfully.')
            return redirect('dashboard')
    else:
        form = JobForm(
            initial={field_name: getattr(job, field_name) for field_name in JOB_FORM_FIELDS}
        )

    return render(
        request,
        'post_job.html',
        {
            'form': form,
            'form_title': 'Edit Job Post',
            'submit_label': 'Save Changes',
        },
    )


