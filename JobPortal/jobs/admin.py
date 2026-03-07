from django.contrib import admin

from .models import Job, JobCategory


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'job_category', 'created_at')
    list_filter = ('job_type', 'job_category')
    search_fields = ('title', 'company', 'location')
