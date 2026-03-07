from django.contrib import admin

from .models import JobSeekerProfile, RecruiterProfile, User


@admin.register(User)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'email',
        'phone_number',
        'gender',
        'city',
        'country',
    )
    list_filter = ('role', 'gender', 'country', 'state')
    search_fields = (
        'user__username',
        'user__email',
        'email',
        'first_name',
        'middle_name',
        'last_name',
        'phone_number',
        'city',
        'state',
        'country',
    )
    list_select_related = ('user',)
    ordering = ('user__username',)


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_email', 'has_resume', 'linkedin', 'github')
    search_fields = (
        'user__user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'linkedin',
        'github',
    )
    list_select_related = ('user',)
    raw_id_fields = ('user',)

    @admin.display(description='Email')
    def profile_email(self, obj):
        return obj.user.email

    @admin.display(boolean=True, description='Resume')
    def has_resume(self, obj):
        return bool(obj.resume)


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_profile',
        'company_name',
        'company_position',
        'company_email',
        'company_phone',
    )
    search_fields = (
        'user_profile__user__username',
        'user_profile__email',
        'company_name',
        'company_position',
        'company_email',
        'company_phone',
    )
    list_select_related = ('user_profile',)
    raw_id_fields = ('user_profile',)
