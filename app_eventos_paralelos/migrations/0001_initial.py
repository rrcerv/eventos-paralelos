# Generated by Django 4.2.11 on 2024-03-05 20:48

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LogisticaParticipantes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=255)),
                ('arrivalDate', models.DateField()),
                ('departureDate', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Eventos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
                ('local', models.CharField(max_length=200)),
                ('data', models.DateField()),
                ('horario', models.TimeField()),
                ('capacidade', models.IntegerField(validators=[django.core.validators.MaxValueValidator(2000), django.core.validators.MinValueValidator(1)])),
                ('empresa_responsavel', models.CharField(max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('update_at', models.DateTimeField()),
                ('CreateUserId', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eventos', to=settings.AUTH_USER_MODEL)),
                ('Responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eventosResponsavel', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ConvidadosExtras',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('empresa', models.CharField(max_length=255)),
                ('cargo', models.CharField(blank=True, max_length=255, null=True)),
                ('vip', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='convidadosextras', to='app_eventos_paralelos.eventos')),
            ],
        ),
        migrations.CreateModel(
            name='Convidados',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=37)),
                ('local', models.BooleanField()),
                ('vip', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='convidados', to='app_eventos_paralelos.eventos')),
            ],
        ),
    ]
