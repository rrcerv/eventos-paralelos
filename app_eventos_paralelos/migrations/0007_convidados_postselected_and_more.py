# Generated by Django 4.2.11 on 2024-03-13 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_eventos_paralelos', '0006_alter_convidadosextras_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='convidados',
            name='postSelected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='convidadosextras',
            name='postSelected',
            field=models.BooleanField(default=False),
        ),
    ]