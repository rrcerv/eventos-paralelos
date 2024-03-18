# Generated by Django 4.2.11 on 2024-03-05 23:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_eventos_paralelos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventos',
            name='status',
            field=models.CharField(choices=[('lista pendente de seleção', 'Lista Pendente de Seleção'), ('lista com patrocinador', 'Lista com Patrocinador'), ('lista pendente de aprovação', 'Lista Pendente de Aprovação')], default='lista pendente de seleção', max_length=30),
        ),
        migrations.AlterField(
            model_name='eventos',
            name='update_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
