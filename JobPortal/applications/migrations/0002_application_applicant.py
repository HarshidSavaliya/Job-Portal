from django.db import migrations, models
import django.db.models.deletion


def backfill_application_applicant(apps, schema_editor):
    Application = apps.get_model('applications', 'Application')
    User = apps.get_model('accounts', 'User')

    for application in Application.objects.filter(applicant__isnull=True):
        matches = list(
            User.objects.filter(role='jobseeker', email__iexact=application.email)[:2]
        )
        if len(matches) == 1:
            application.applicant_id = matches[0].id
            application.save(update_fields=['applicant'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_remove_jobseekerprofile_certifications_and_more'),
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='applicant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='applications',
                to='accounts.user',
            ),
        ),
        migrations.RunPython(
            backfill_application_applicant,
            migrations.RunPython.noop,
        ),
    ]
