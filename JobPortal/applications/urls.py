from django.urls import path

from . import views


urlpatterns = [
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('my/', views.my_applications, name='my_applications'),
    path('edit/<int:application_id>/', views.edit_application, name='edit_application'),
    path('delete/<int:application_id>/', views.delete_application, name='delete_application'),
    path('received/', views.recruiter_applications, name='recruiter_applications'),
    path(
        'status/<int:application_id>/<str:status>/',
        views.update_application_status,
        name='update_application_status',
    ),
]
