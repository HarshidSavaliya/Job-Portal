from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'applicant', 'job', 'recruiter', 'applied_at', 'has_resume')
    list_filter = ('status', 'applied_at', 'job__job_category')
    search_fields = (
        'name',
        'email',
        'applicant__user__username',
        'applicant__email',
        'job__title',
        'job__company',
        'recruiter__company_name',
        'recruiter__user_profile__user__username',
    )
    autocomplete_fields = ('applicant', 'job', 'recruiter')
    list_select_related = ('applicant__user', 'job', 'recruiter')
    ordering = ('-applied_at',)
    readonly_fields = ('applied_at',)

    @admin.display(boolean=True, description='Resume')
    def has_resume(self, obj):
        return bool(obj.resume)
