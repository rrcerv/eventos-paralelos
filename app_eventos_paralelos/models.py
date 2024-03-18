from django.db import models
from usuarios.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class Eventos(models.Model):
    nome = models.CharField(max_length = 200, null = False)
    local = models.CharField(max_length = 200)
    data = models.DateField()
    horario = models.TimeField()
    capacidade = models.IntegerField(validators=[MaxValueValidator(2000), MinValueValidator(1)])
    Responsavel = models.ForeignKey(User, blank= True, null= True, related_name='eventosResponsavel', on_delete=models.SET_NULL) 
    empresa_responsavel = models.CharField(max_length = 255, null= True)

    LISTA_PENDENTE_DE_SELECAO = 'Pré-Selecione a Lista'
    LISTA_COM_PATROCINADOR = 'Com Patrocinador'
    LISTA_PENDENTE_DE_APROVACAO = 'Aprove a Lista'
    CONCLUIDO = 'Lista concluida'
    
    # Lista enviada, re-envio

    STATUS_CHOICES = (
        (LISTA_PENDENTE_DE_SELECAO, 'Lista Pendente de Seleção'),
        (LISTA_COM_PATROCINADOR, 'Lista com Patrocinador'),
        (LISTA_PENDENTE_DE_APROVACAO, 'Lista Pendente de Aprovação'),
        (CONCLUIDO, 'Lista concluida')
    )

    status = models.CharField(choices=STATUS_CHOICES, default=LISTA_PENDENTE_DE_SELECAO, max_length=30)
    
    CreateUserId = models.ForeignKey(User, related_name='eventos', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_deleted = models.BooleanField(default=False)
    update_at = models.DateTimeField(auto_now_add=True)


class Convidados(models.Model):
    uuid = models.CharField(max_length=37)
    local = models.BooleanField()
    vip = models.BooleanField()
    sponsorSelected= models.BooleanField(default=False)
    postSelected = models.BooleanField(default=False) # Parâmetro caso o comercial tenha selecionado um participante que não havia sido selecionado pelo patrocinador
    evento = models.ForeignKey(Eventos, related_name='convidados', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add = True)
    is_deleted = models.BooleanField(default=False)
    createUserId = models.ForeignKey(User, null=True, related_name='convidado', on_delete=models.SET_NULL)

 
class ConvidadosExtras(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField()
    empresa = models.CharField(max_length=255, blank=True, null=True)
    cargo = models.CharField(max_length=255, blank = True, null = True)
    vip = models.BooleanField(default=False)
    postSelected = models.BooleanField(default=False) # Parâmetro caso o comercial tenha adicionado o convidado extra
    evento = models.ForeignKey(Eventos, related_name='convidadosextras', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add = True)
    is_deleted = models.BooleanField(default=False)


class LogisticaParticipantes(models.Model):
    uuid = models.CharField(max_length = 255)
    arrivalDate = models.DateField()
    departureDate = models.DateField() 

    created_at = models.DateTimeField(auto_now_add = True)
    is_deleted = models.BooleanField(default=False)
     

  