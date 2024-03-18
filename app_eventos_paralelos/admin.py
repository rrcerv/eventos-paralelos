from django.contrib import admin
from .models import Eventos, Convidados, ConvidadosExtras, LogisticaParticipantes

admin.site.register(Eventos)
admin.site.register(ConvidadosExtras)
admin.site.register(Convidados)
admin.site.register(LogisticaParticipantes)