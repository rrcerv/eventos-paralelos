from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.eventos_paralelos, name='index'),
    path('logistica/', views.logistica, name='logistica'),


    # PRÉ SELEÇÃO
    path('preselecao/<str:id>', views.pre_selecao, name='preselecao'), 
    path('api/api_post_evento/', views.api_post_evento, name='api_post_evento'),
    path('api/api_preselecao/', views.api_post_preselecao, name='api_post_preselecao'),
    path('api/populateTable/<str:id>', views.api_populateTable, name='api_populatetable'),
    path('api/post_convidado', views.api_post_convidado, name='post_convidado'),


    # SELEÇÃO PATROCINADOR
    path('selecao/<str:id>', views.selecao_patrocinador, name='selecao_patrocinador'), 
    path('api/populateTablePatrocinador/<str:id>', views.api_populateTablePatrocinador, name='api_populatetablepatrocinador'),
    path('api/postConvidadoPatrocinador', views.api_post_convidado_patrocinador, name='post_convidado_patrocinador'),
    path('api_post_selecaopatrocionador', views.api_post_selecaopatrocionador, name='api_post_selecaopatrocionador'),
    path('api/post_convidado_extra', views.api_post_convidadoextra, name='api_post_convidado_extra'),
    path('api/excluir_convidado_extra/<int:id>/<str:evento_id>', views.api_excluir_convidadoextra, name='api_excluir_convidadoextra'),


    #APROVAÇÃO DE LISTA
    path('aprovacao/<str:id>', views.aprovacao_lista, name='aprovacao_lista'),
    path('api/populateTableAprovacao/<str:id>', views.api_populateTableAprovacao, name='api_populatetableaprovacao'),
    path('api/postConvidadoAprovacao', views.api_post_convidado_aprovacao, name='post_convidado_aprovacao'),
    path('api/post_convidado_extra_aprovacao', views.api_post_convidadoextra_aprovacao, name='api_post_convidado_extra_aprovacao'),
    path('api/post_aprovacao/<str:id_evento>', views.api_post_aprovacao, name='api_post_aprovacao'),


    #AGENDA
    path('agenda/', views.agenda, name='agenda'),
    path('api/eventos', views.api_eventos, name='api_eventos')
]
