from django.db import models


class Application(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    resume = models.FileField(upload_to='resumes/')
    experience = models.TextField(blank=True)
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='applications',
        null=True,
        blank=True,
    )

    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='applications'
    )

    recruiter = models.ForeignKey(
        'accounts.RecruiterProfile',
        on_delete=models.CASCADE,
        related_name='received_applications'
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.name} - {self.job}"
