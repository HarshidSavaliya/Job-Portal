import django.db.models.deletion
from django.db import migrations, models


DEFAULT_CATEGORIES = [
    ('it', 'IT / Software'),
    ('marketing', 'Marketing'),
    ('finance', 'Finance'),
    ('hr', 'Human Resources'),
    ('other', 'Other'),
]


def seed_categories_and_backfill_jobs(apps, schema_editor):
    Job = apps.get_model('jobs', 'Job')
    JobCategory = apps.get_model('jobs', 'JobCategory')

    code_to_id = {}
    for code, name in DEFAULT_CATEGORIES:
        category, _ = JobCategory.objects.get_or_create(
            code=code,
            defaults={'name': name},
        )
        code_to_id[code] = category.id

    other_id = code_to_id['other']
    for job in Job.objects.all().iterator():
        job.job_category_fk_id = code_to_id.get(job.job_category, other_id)
        job.save(update_fields=['job_category_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_remove_job_languages_required'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Job Category',
                'verbose_name_plural': 'Job Categories',
            },
        ),
        migrations.AddField(
            model_name='job',
            name='job_category_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='jobs',
                to='jobs.jobcategory',
            ),
        ),
        migrations.RunPython(seed_categories_and_backfill_jobs, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='job',
            name='job_category',
        ),
        migrations.RenameField(
            model_name='job',
            old_name='job_category_fk',
            new_name='job_category',
        ),
        migrations.AlterField(
            model_name='job',
            name='job_category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='jobs',
                to='jobs.jobcategory',
            ),
        ),
    ]
