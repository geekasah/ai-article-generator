# Generated by Django 5.0.6 on 2024-05-29 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog_generator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='generated_content',
            field=models.TextField(default=''),
        ),
    ]
