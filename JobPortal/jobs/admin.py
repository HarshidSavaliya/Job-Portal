from django.contrib import admin

from .models import Job, JobCategory


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'job_category', 'recruiter', 'created_at')
    list_filter = ('job_type', 'job_category')
    search_fields = (
        'title',
        'company',
        'location',
        'recruiter__company_name',
        'recruiter__user_profile__user__username',
    )
    autocomplete_fields = ('recruiter',)
    list_select_related = ('job_category', 'recruiter')
    ordering = ('-created_at',)
