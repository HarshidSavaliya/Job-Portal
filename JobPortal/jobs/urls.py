from django.urls import path
from . import views 

urlpatterns = [
    path('create_job_post/', views.create_post_job, name='create_job_post'),
    path('edit_job_post/<int:job_id>/', views.edit_job_post, name='edit_job_post'),
]
