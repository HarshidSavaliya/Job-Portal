from django.db import models


class JobCategory(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Job Category'
        verbose_name_plural = 'Job Categories'

    def __str__(self):
        return self.name


class Job(models.Model):

    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]

    recruiter = models.ForeignKey(
        'accounts.RecruiterProfile',
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)

    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPES
    )

    job_category = models.ForeignKey(
        JobCategory,
        on_delete=models.PROTECT,
        related_name='jobs'
    )

    job_description = models.TextField()

    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    salary = models.DecimalField(max_digits=10, decimal_places=2)

    education_requirements = models.TextField()
    experience_requirements = models.TextField()
    skills_required = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.company}"
