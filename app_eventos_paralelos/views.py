from django.shortcuts import render, redirect
from django.urls import reverse
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Group
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import json
import pyodbc

# CRIPTOGRAFIA
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import environ

from .models import Eventos, Convidados, ConvidadosExtras
from usuarios.models import User


erro_permissao = JsonResponse({'response': 'Seu perfil nao tem permissoes suficientes.'})

env = environ.Env()
environ.Env.read_env()

def encrypt(message):

    chave_separadora = env('cripto_chave_separadora')
    salt = env('cripto_salt')
    password = env('cripto_password')
    key = PBKDF2(password, salt, dkLen=32)

    cipher = AES.new(key, AES.MODE_CBC)

    cipher_data = cipher.encrypt(pad(message.encode(), AES.block_size))

    encriptado = (cipher_data)

    iv = cipher.iv

    encriptado = base64.urlsafe_b64encode(encriptado).decode('utf-8')
    
    iv = base64.urlsafe_b64encode(iv).decode('utf-8')

    return encriptado + chave_separadora + iv


def decrypt(encriptado):

    chave_separadora = env('cripto_chave_separadora')
    salt = env('cripto_salt')
    password = env('cripto_password')

    encriptado = encriptado.split(chave_separadora)
    
    
    iv = encriptado[1]
    encriptado = encriptado[0]

    encriptado = base64.urlsafe_b64decode(encriptado.encode('utf-8'))
    iv = base64.urlsafe_b64decode(iv.encode('utf-8'))
    key = PBKDF2(password, salt, dkLen=32)
    cipher = AES.new(key, AES.MODE_CBC, iv = iv)

    decrypted_text = unpad(cipher.decrypt(encriptado), AES.block_size).decode()

    return (decrypted_text)


@login_required
def eventos_paralelos(request):
    usuario = request.user

    # HOME COMERCIAL
    if usuario.role == 'comercial':

        try:
            todos_os_eventos = Eventos.objects.filter(CreateUserId = usuario.id)

            todos_os_eventos_teste = []

            for evento in todos_os_eventos:
                json = {}
                evento_fields = evento._meta.fields # TRANSFORMA O OBJETO PARA ITERAR SOBRE SUAS COLUNAS
                for field in evento_fields:
                    if field.name == 'id':
                        id_encriptado = encrypt(str(getattr(evento, 'id')))
                        json['id'] = id_encriptado
                        
                    else:
                        json[f'{field.name}'] = getattr(evento, field.name)

                todos_os_eventos_teste.append(json)


            numero_de_eventos = todos_os_eventos.count()
        except:
            #todos_os_eventos = Eventos.objects.filter(CreateUserId = usuario.id)
            numero_de_eventos = 0
    
        try:
            eventos_pendentes_aprovacao = todos_os_eventos.filter(status='Aprove a Lista')
            numero_eventos_pendentes = eventos_pendentes_aprovacao.count()
        except:
            numero_eventos_pendentes = 0 
    
        return render(request, 'EventosParalelos.html', {
            'eventos': todos_os_eventos_teste,
            'numero_de_eventos': numero_de_eventos,
            'nr_eventos_pendentes': numero_eventos_pendentes
        })
    
    # HOME PATROCINADOR
    elif(usuario.role == 'patrocinador'):
        usuario = request.user
        
        try:
            eventos_patrocinador = Eventos.objects.filter(Responsavel = usuario)
            numero_de_eventos = eventos_patrocinador.count()

            eventos_patrocinador_teste = []

            for evento in eventos_patrocinador:
                json = {}
                evento_fields = evento._meta.fields # TRANSFORMA O OBJETO PARA ITERAR SOBRE SUAS COLUNAS
                for field in evento_fields:
                    if field.name == 'id':
                        #print(evento.id)
                        id_encriptado = encrypt(str(getattr(evento, 'id')))
                        #id_encriptado = id_encriptado[0] + '-' + id_encriptado[1]
                        #print(id_encriptado)
                        json['id'] = id_encriptado
                        
                    else:
                        json[f'{field.name}'] = getattr(evento, field.name)

                eventos_patrocinador_teste.append(json)

        except:
            eventos_patrocinador = Eventos.objects.filter(Responsavel = usuario)
            numero_de_eventos = 0

        try:
            eventos_pendentes_selecao = eventos_patrocinador.filter(status='Com Patrocinador')
            numero_eventos_pendentes = eventos_pendentes_selecao.count()

        except:
            numero_eventos_pendentes = 0

        return render(request, 'EventoPatrocinador.html', {
            'eventos': eventos_patrocinador_teste,
            'numero_de_eventos': numero_de_eventos,
            'nr_eventos_pendentes': numero_eventos_pendentes
        })
    
    else:
        return HttpResponse("<h1>Ops! Seu perfil não pode acessar esta página.</h1>")

@login_required
def logistica(request):

    # CONECTANDO COM O BANCO DE DADOS
    cnxn = pyodbc.connect("DRIVER={SQL Server};"
                        "SERVER=rio2c-sqlserver.cb5mokkxuw8r.us-east-1.rds.amazonaws.com;"
                        "DATABASE=MyRio2C_Prod;"
                        "UID=user-readonly;PWD=v8Gosb8W3w-p*FHn")
    
    cursor = cnxn.cursor()

    query_teste='''SELECT CONCAT(C.FirstName, ' ', C.LastNames) AS 'Nome',
       ACTV.Email,
       LOWER(CONCAT('https://assets.my.rio2c.com/img/users/', C.Uid,'_thumbnail.png')) AS 'Foto (500 x 500)',
       CJT.Value AS 'Cargo',
       --O.CompanyName,
       STUFF((
       SELECT NCHAR(13) + '\r\n' + '• ' + O.CompanyName
       FROM dbo.Organizations AS O
       JOIN dbo.AttendeeOrganizationCollaborators AS AOC ON AOC.AttendeeCollaboratorId = AC.Id
       JOIN dbo.AttendeeOrganizations AS AO ON AO.Id = AOC.AttendeeOrganizationId
       WHERE O.Id = AO.OrganizationId
       FOR XML PATH(''), TYPE
       ).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 'Interesses',
       --O.TradeName,
       --CJT.LanguageId as 'Cargo - LanguageId',
       C.ImageUploadDate,
       C.Uid
       --CJT.Value  as 'Cargo - Value'

FROM dbo.AttendeeCollaborators AS AC
LEFT JOIN dbo.AttendeeCollaboratorTypes AS ACT ON ACT.AttendeeCollaboratorId = AC.Id
LEFT JOIN dbo.Users AS ACTV ON ACTV.Id = AC.CollaboratorId
LEFT JOIN dbo.Collaborators AS C ON C.Id = AC.CollaboratorId
--LEFT JOIN dbo.CollaboratorJobTitles AS CJT ON CJT.CollaboratorId = C.Id
--LEFT JOIN dbo.AttendeeOrganizationCollaborators AOC ON AOC.AttendeeCollaboratorId = AC.Id    -- Associação entre Empresas/Edição & Colaborador/Edição
--LEFT JOIN dbo.AttendeeOrganizations AO on AO.Id = AOC.AttendeeOrganizationId                -- Empresas/Edição
--LEFT JOIN dbo.Organizations O on O.Id = AO.OrganizationId                                    -- Empresas
LEFT JOIN dbo.CollaboratorJobTitles CJT on CJT.CollaboratorId = C.Id                        -- Cargos

WHERE AC.EditionId = 6
AND (ACT.CollaboratorTypeId = 200 OR ACT.CollaboratorTypeId = 201 OR ACT.CollaboratorTypeId = 202) -- 300 -> Audiovisual / 301 -> Música / 302 -> Startup
AND (CJT.LanguageId = 2 OR CJT.LanguageId IS NULL)
AND AC.isDeleted = 0
--AND AOC.IsDeleted = 0
--AND AO.IsDeleted = 0
--AND O.IsDeleted = 0
AND ACT.IsDeleted = 0
AND ACTV.IsDeleted = 0
AND C.IsDeleted = 0'''

    cursor.execute(query_teste)

    participantes = cursor.fetchall()

    return render(request, 'logistica.html', {
        'participantes': participantes
    })




# ----- CRIAR EVENTO -----

@login_required
def api_post_evento(request):
    usuario_atual = request.user

    if usuario_atual.role == 'comercial':
        if request.method == 'POST':

            usuario = request.user

            eventoData = (request.body.decode('utf-8'))
            eventoData = json.loads(eventoData)

            evento_nome = (eventoData['name'])
            evento_local = (eventoData['location'])
            evento_data = (eventoData['date'])
            evento_horario =  (eventoData['time'])
            evento_capacidade = (eventoData['capacity'])
            evento_responsavel = (eventoData['manager'])
            evento_empresa_responsavel = (eventoData['responsible_company'])

            try:
                usuario_patrocinador = User.objects.get(email = evento_responsavel)

            except:
                usuario_patrocinador = User.objects.create(role='patrocinador', email=evento_responsavel)


                usuario_patrocinador.set_password('12345')
                usuario_patrocinador.save()

            Eventos.objects.create(nome=evento_nome, local=evento_local, data=evento_data, horario=evento_horario, capacidade=evento_capacidade, Responsavel=usuario_patrocinador, empresa_responsavel= evento_empresa_responsavel, CreateUserId = usuario )

            return JsonResponse({"response": "Request OK"}, safe=False)
        else:
            return JsonResponse({"response": "Erro."})
    else:
        return JsonResponse({'response':'Seu perfil não tem autorização para utilizar esta API.'})

# FIM CRIAR EVENTO 



#  ----- PRÉ SELEÇÃO -----
@login_required
def pre_selecao(request, id):
    usuario = request.user
    url_home = reverse(eventos_paralelos)
    if (usuario.role == 'comercial'):
        try:
            id = decrypt(id)
            evento = Eventos.objects.get(id=id)
            
            if(evento.status == "Pré-Selecione a Lista"):

                if evento.CreateUserId == usuario:
                    cnxn = pyodbc.connect("DRIVER={SQL Server};"
                            "SERVER=rio2c-sqlserver.cb5mokkxuw8r.us-east-1.rds.amazonaws.com;"
                            "DATABASE=MyRio2C_Prod;"
                            "UID=user-readonly;PWD=v8Gosb8W3w-p*FHn")
        
                    cursor = cnxn.cursor()

                    query_teste='''SELECT CONCAT(C.FirstName, ' ', C.LastNames) AS 'Nome',
        ACTV.Email,
        LOWER(CONCAT('https://assets.my.rio2c.com/img/users/', C.Uid,'_thumbnail.png')) AS 'Foto (500 x 500)',
        CJT.Value AS 'Cargo',
        --O.CompanyName,
        STUFF((
        SELECT NCHAR(13) + '\r\n' + '• ' + O.CompanyName
        FROM dbo.Organizations AS O
        JOIN dbo.AttendeeOrganizationCollaborators AS AOC ON AOC.AttendeeCollaboratorId = AC.Id
        JOIN dbo.AttendeeOrganizations AS AO ON AO.Id = AOC.AttendeeOrganizationId
        WHERE O.Id = AO.OrganizationId
        FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 'Interesses',
        --O.TradeName,
        --CJT.LanguageId as 'Cargo - LanguageId',
        C.ImageUploadDate,
        C.Uid,
            CASE
            WHEN ACT.CollaboratorTypeId = 200 THEN 'Audiovisual'
                ELSE
                    CASE
                        WHEN ACT.CollaboratorTypeId = 201 THEN 'Música'
                    ELSE 'Startup'
                    END
                END AS 'CollaboratorType'
        --CJT.Value  as 'Cargo - Value'

    FROM dbo.AttendeeCollaborators AS AC
    LEFT JOIN dbo.AttendeeCollaboratorTypes AS ACT ON ACT.AttendeeCollaboratorId = AC.Id
    LEFT JOIN dbo.Users AS ACTV ON ACTV.Id = AC.CollaboratorId
    LEFT JOIN dbo.Collaborators AS C ON C.Id = AC.CollaboratorId
    --LEFT JOIN dbo.CollaboratorJobTitles AS CJT ON CJT.CollaboratorId = C.Id
    --LEFT JOIN dbo.AttendeeOrganizationCollaborators AOC ON AOC.AttendeeCollaboratorId = AC.Id    -- Associação entre Empresas/Edição & Colaborador/Edição
    --LEFT JOIN dbo.AttendeeOrganizations AO on AO.Id = AOC.AttendeeOrganizationId                -- Empresas/Edição
    --LEFT JOIN dbo.Organizations O on O.Id = AO.OrganizationId                                    -- Empresas
    LEFT JOIN dbo.CollaboratorJobTitles CJT on CJT.CollaboratorId = C.Id                        -- Cargos

    WHERE AC.EditionId = 6
    AND (ACT.CollaboratorTypeId = 200 OR ACT.CollaboratorTypeId = 201 OR ACT.CollaboratorTypeId = 202) -- 300 -> Audiovisual / 301 -> Música / 302 -> Startup
    AND (CJT.LanguageId = 2 OR CJT.LanguageId IS NULL)
    AND AC.isDeleted = 0
    --AND AOC.IsDeleted = 0
    --AND AO.IsDeleted = 0
    --AND O.IsDeleted = 0
    AND ACT.IsDeleted = 0
    AND ACTV.IsDeleted = 0
    AND C.IsDeleted = 0'''
                    
                    cursor.execute(query_teste)

                    participantes = cursor.fetchall()
                    
                    return render(request, 'PreSelecao.html',{
                        'evento': evento,
                        'participantes': participantes,
                        'url_home': url_home
                    })
                else:
                    return HttpResponse('<h1>Ops. Somente o criador do evento pode acessar a pré-seleção.</h1>')
            else:
                return HttpResponse("<h1>O evento desejado não está na fase de pré-seleção.</h1>")

        except:
            return HttpResponse('<h1>Ops. O evento que você está tentando acessar não existe.</h1>')
    else:
        return HttpResponse('<h1> Você precisa ser do comercial para acessar esta página. </h1>')

@login_required
def api_post_preselecao(request):
    usuario = request.user
    if usuario.role == 'comercial':
        if request.method == 'POST':
            convidadosData = request.body.decode('utf-8')
            convidadosData = json.loads(convidadosData)

            id_evento = (convidadosData['idEvento'])
            id_evento = decrypt(id_evento)
            evento = Eventos.objects.get(id = id_evento)

            evento.status = 'Com Patrocinador' # Pré-Selecione a Lista, Com Patrocinador, Aprove a Lista
            evento.save()

            return JsonResponse({"response": "success"})
        else:
            return JsonResponse({'response':'Erro.'})
    
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a acessar esta API.'})

@login_required
def api_post_convidado(request):
    usuario = request.user
    if usuario.role == 'comercial':
        if request.method == 'POST':

            convidado_data = request.body.decode('utf-8')
            convidado_data = json.loads(convidado_data)

            funcao = convidado_data['funcao']

            if(funcao == 'add'):
                print('add')
                id_evento = convidado_data['idEvento']
                id_evento = decrypt(id_evento)
                evento = Eventos.objects.get(id=id_evento)

                uuid_convidado = convidado_data['Uuid']

                Convidados.objects.create( uuid = uuid_convidado, local=1, vip=0, evento=evento, createUserId = usuario)

                return JsonResponse({'Reponse': 'Ok'})
            
            if (funcao == 'rem'):
                print('rem')
                uuid_convidado = convidado_data['Uuid']

                id_evento = convidado_data['idEvento']
                id_evento = decrypt(id_evento)
                evento = Eventos.objects.get(id=id_evento)
                
                #convidado = Convidados.objects.get(uuid = uuid_convidado, evento = evento)
                convidado = Convidados.objects.get(uuid=uuid_convidado, evento=evento)
                convidado.delete()

                return JsonResponse({'Reponse': 'Ok'})
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a utilizar essa API.'})

@login_required
def api_populateTable(request, id):
    usuario = request.user
    if usuario.role == 'comercial':
        id = decrypt(id)
        evento = Eventos.objects.get(id=id)
        convidados = evento.convidados.all()
        lista_uuid = [convidado.uuid for convidado in convidados]
        #Convidados.objects.create( uuid = uuid_convidado, local=1, vip=0, evento=evento, createUserId= usuario )
        return JsonResponse({"response": lista_uuid})
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a utilizar esta API.'})

# FIM PRÉ SELEÇÃO




# ----- PÁGINA PATROCINADOR -----

@login_required
def selecao_patrocinador(request, id):
    usuario = request.user
    url_home = reverse(eventos_paralelos)
    if (usuario.role == 'patrocinador'):
        try:
            id = decrypt(id)
            evento = Eventos.objects.get(id=id)

            if (evento.status == 'Com Patrocinador'):

                if evento.Responsavel == usuario:

                    convidados = evento.convidados.all()
                    uuid_convidados = [convidado.uuid for convidado in convidados]

                    cnxn = pyodbc.connect("DRIVER={SQL Server};"
                            "SERVER=rio2c-sqlserver.cb5mokkxuw8r.us-east-1.rds.amazonaws.com;"
                            "DATABASE=MyRio2C_Prod;"
                            "UID=user-readonly;PWD=v8Gosb8W3w-p*FHn")
                    cursor = cnxn.cursor()
                    query_teste='''SELECT CONCAT(C.FirstName, ' ', C.LastNames) AS 'Nome',
        ACTV.Email,
        LOWER(CONCAT('https://assets.my.rio2c.com/img/users/', C.Uid,'_thumbnail.png')) AS 'Foto (500 x 500)',
        CJT.Value AS 'Cargo',
        --O.CompanyName,
        STUFF((
        SELECT NCHAR(13) + '\r\n' + '• ' + O.CompanyName
        FROM dbo.Organizations AS O
        JOIN dbo.AttendeeOrganizationCollaborators AS AOC ON AOC.AttendeeCollaboratorId = AC.Id
        JOIN dbo.AttendeeOrganizations AS AO ON AO.Id = AOC.AttendeeOrganizationId
        WHERE O.Id = AO.OrganizationId
        FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 'Interesses',
        --O.TradeName,
        --CJT.LanguageId as 'Cargo - LanguageId',
        C.ImageUploadDate,
        C.Uid,
            CASE
            WHEN ACT.CollaboratorTypeId = 200 THEN 'Audiovisual'
                ELSE
                    CASE
                        WHEN ACT.CollaboratorTypeId = 201 THEN 'Música'
                    ELSE 'Startup'
                    END
                END AS 'CollaboratorType'
        --CJT.Value  as 'Cargo - Value'

    FROM dbo.AttendeeCollaborators AS AC
    LEFT JOIN dbo.AttendeeCollaboratorTypes AS ACT ON ACT.AttendeeCollaboratorId = AC.Id
    LEFT JOIN dbo.Users AS ACTV ON ACTV.Id = AC.CollaboratorId
    LEFT JOIN dbo.Collaborators AS C ON C.Id = AC.CollaboratorId
    --LEFT JOIN dbo.CollaboratorJobTitles AS CJT ON CJT.CollaboratorId = C.Id
    --LEFT JOIN dbo.AttendeeOrganizationCollaborators AOC ON AOC.AttendeeCollaboratorId = AC.Id    -- Associação entre Empresas/Edição & Colaborador/Edição
    --LEFT JOIN dbo.AttendeeOrganizations AO on AO.Id = AOC.AttendeeOrganizationId                -- Empresas/Edição
    --LEFT JOIN dbo.Organizations O on O.Id = AO.OrganizationId                                    -- Empresas
    LEFT JOIN dbo.CollaboratorJobTitles CJT on CJT.CollaboratorId = C.Id                        -- Cargos

    WHERE AC.EditionId = 6
    AND (ACT.CollaboratorTypeId = 200 OR ACT.CollaboratorTypeId = 201 OR ACT.CollaboratorTypeId = 202) -- 300 -> Audiovisual / 301 -> Música / 302 -> Startup
    AND (CJT.LanguageId = 2 OR CJT.LanguageId IS NULL)
    AND AC.isDeleted = 0
    --AND AOC.IsDeleted = 0
    --AND AO.IsDeleted = 0
    --AND O.IsDeleted = 0
    AND ACT.IsDeleted = 0
    AND ACTV.IsDeleted = 0
    AND C.IsDeleted = 0'''  
                    cursor.execute(query_teste)
                    todos_participantes = cursor.fetchall()

                    #participantes = [item for item in todos_participantes if item[6] in uuid_convidados]
                    
                    json_participantes = []

                    for participante in todos_participantes:
                        if participante[6] in uuid_convidados:
                            convidado = convidados.get(uuid=participante[6])
                            json_participante = {}
                            for index, item in enumerate(participante):
                                if index == len(participante)-1:
                                    json_participante[index] = item
                                    json_participante[len(participante)] = convidado.id
                                else:
                                    json_participante[index] = item                      
                            json_participantes.append(json_participante)

                    participantes = json_participantes

                    participantes_extras = ConvidadosExtras.objects.filter(evento=evento)

                    nr_participantes_extras = (participantes_extras.count())

                    
                    return render(request, 'SelecaoPatrocinador.html',{
                        'evento': evento,
                        'participantes': participantes,
                        'url_home': url_home,
                        'participantes_extras': participantes_extras,
                        'nr_participantes_extras': nr_participantes_extras
                    })
                else:
                    return HttpResponse('<h1>Ops. Somente o responsável do evento pode acessar a lista.</h1>')
            else:
                if evento.status == "Pré-Selecione a Lista":
                    return HttpResponse(f'<h1>A lista do evento {evento.nome} ainda não pode ser selecionada.</h1>')
                else:
                    return HttpResponse(f'<h1>A lista do evento {evento.nome} já foi enviada para o comercial</h1>')

        except Exception as E:
            print(E)
            return HttpResponse('<h1>Ops. O evento que você está tentando acessar não existe.</h1>')
    else:
        return HttpResponse('<h1> Você precisa ser do comercial para acessar esta página. </h1>')

@login_required
def api_populateTablePatrocinador(request, id):
    usuario = request.user
    if usuario.role == 'patrocinador':
        id = decrypt(id)
        evento = Eventos.objects.get(id=id)
        convidados = evento.convidados.all()
        lista_uuid = [convidado.id for convidado in convidados if convidado.sponsorSelected == 1]
        #Convidados.objects.create( uuid = uuid_convidado, local=1, vip=0, evento=evento, createUserId= usuario )
        return JsonResponse({"response": lista_uuid})
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a utilizar esta API.'})

@login_required
def api_post_convidado_patrocinador(request):
    usuario = request.user
    if usuario.role == 'patrocinador':
        if request.method == 'POST':

            convidado_data = request.body.decode('utf-8')
            convidado_data = json.loads(convidado_data)

            funcao = convidado_data['funcao']

            if(funcao == 'add'):
                print('add')
                id_evento = convidado_data['idEvento']
                id_evento = decrypt(id_evento)
                evento = Eventos.objects.get(id=id_evento)

                id_convidado = convidado_data['Uuid']


                convidado = Convidados.objects.get(id = id_convidado)

                convidado.sponsorSelected = True
                
                convidado.save()

                return JsonResponse({'Reponse': 'Ok'})
            
            if (funcao == 'rem'):
                print('rem')
                id_convidado = convidado_data['Uuid']

                id_evento = convidado_data['idEvento']
                id_evento = decrypt(id_evento)
                evento = Eventos.objects.get(id=id_evento)

                convidado = Convidados.objects.get(id = id_convidado)

                convidado.sponsorSelected = False

                convidado.save()

                return JsonResponse({'Reponse': 'Ok'})
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a utilizar essa API.'})

@login_required
def api_post_selecaopatrocionador(request):
    usuario = request.user
    if usuario.role == 'patrocinador':
        if request.method == 'POST':
            convidadosData = request.body.decode('utf-8')
            convidadosData = json.loads(convidadosData)

            id_evento = (convidadosData['idEvento'])
            id_evento = decrypt(id_evento)
            evento = Eventos.objects.get(id = id_evento)

            evento.status = 'Aprove a Lista' # Pré-Selecione a Lista, Com Patrocinador, Aprove a Lista
            evento.save()

            return JsonResponse({"response": "success"})
        else:
            return JsonResponse({'response':'Erro.'})
    
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a acessar esta API.'})

@login_required
def api_post_convidadoextra(request):
    usuario = request.user
    if usuario.role == 'patrocinador':
        if request.method == 'POST':
            data = request.body.decode('utf-8')
            data = json.loads(data)

            nome = (data['guestName'])
            email = (data['guestEmail'])
            empresa = (data['guestCompany'])
            cargo = (data['guestJobTitle'])
            
            evento_id = data['eventoId']
            evento_id = decrypt(evento_id)
            evento = Eventos.objects.get(id= evento_id)
            
            ConvidadosExtras.objects.create(nome= nome, email = email, empresa = empresa, cargo= cargo, evento= evento)

            return JsonResponse({'response': 'Ok'})


        else:
            return JsonResponse({'response': 'Erro.'})

    else:
        return JsonResponse({'response': 'Seu perfil não está autorizado a acessar essa API'})

@login_required
def api_excluir_convidadoextra(request, id, evento_id):
    usuario = request.user
    if usuario.role == 'patrocinador':
        evento_id = decrypt(evento_id)
        evento = Eventos.objects.get(id=evento_id)
        if (usuario == evento.Responsavel):
            convidado_extra = ConvidadosExtras.objects.get(id=id)
            convidado_extra.delete()
            return redirect(selecao_patrocinador, id=evento_id)
        else:
            return erro_permissao
    else:
        return erro_permissao


# FIM PÁGINA PATROCINADOR
    

# ----- PÁGINA APROVAÇÃO -----

@login_required
def aprovacao_lista(request, id):
    usuario = request.user
    if usuario.role == 'comercial':

        id = decrypt(id)
 
        evento = Eventos.objects.get(id = id)

        url_home = reverse(eventos_paralelos)
    
        convidados = evento.convidados.filter(sponsorSelected=True)
        uuid_convidados = [convidado.uuid for convidado in convidados]

        not_selected = evento.convidados.filter(sponsorSelected=False)
        not_selected_uuid = [not_.uuid for not_ in not_selected]

        cnxn = pyodbc.connect("DRIVER={SQL Server};"
                        "SERVER=rio2c-sqlserver.cb5mokkxuw8r.us-east-1.rds.amazonaws.com;"
                        "DATABASE=MyRio2C_Prod;"
                        "UID=user-readonly;PWD=v8Gosb8W3w-p*FHn")
        cursor = cnxn.cursor()
        query_teste='''SELECT CONCAT(C.FirstName, ' ', C.LastNames) AS 'Nome',
       ACTV.Email,
       LOWER(CONCAT('https://assets.my.rio2c.com/img/users/', C.Uid,'_thumbnail.png')) AS 'Foto (500 x 500)',
       CJT.Value AS 'Cargo',
       --O.CompanyName,
       STUFF((
       SELECT NCHAR(13) + '\r\n' + '• ' + O.CompanyName
       FROM dbo.Organizations AS O
       JOIN dbo.AttendeeOrganizationCollaborators AS AOC ON AOC.AttendeeCollaboratorId = AC.Id
       JOIN dbo.AttendeeOrganizations AS AO ON AO.Id = AOC.AttendeeOrganizationId
       WHERE O.Id = AO.OrganizationId
       FOR XML PATH(''), TYPE
       ).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 'Interesses',
       --O.TradeName,
       --CJT.LanguageId as 'Cargo - LanguageId',
       C.ImageUploadDate,
       C.Uid,
        CASE
           WHEN ACT.CollaboratorTypeId = 200 THEN 'Audiovisual'
            ELSE
                CASE
                    WHEN ACT.CollaboratorTypeId = 201 THEN 'Música'
                ELSE 'Startup'
                END
            END AS 'CollaboratorType'
       --CJT.Value  as 'Cargo - Value'

FROM dbo.AttendeeCollaborators AS AC
LEFT JOIN dbo.AttendeeCollaboratorTypes AS ACT ON ACT.AttendeeCollaboratorId = AC.Id
LEFT JOIN dbo.Users AS ACTV ON ACTV.Id = AC.CollaboratorId
LEFT JOIN dbo.Collaborators AS C ON C.Id = AC.CollaboratorId
--LEFT JOIN dbo.CollaboratorJobTitles AS CJT ON CJT.CollaboratorId = C.Id
--LEFT JOIN dbo.AttendeeOrganizationCollaborators AOC ON AOC.AttendeeCollaboratorId = AC.Id    -- Associação entre Empresas/Edição & Colaborador/Edição
--LEFT JOIN dbo.AttendeeOrganizations AO on AO.Id = AOC.AttendeeOrganizationId                -- Empresas/Edição
--LEFT JOIN dbo.Organizations O on O.Id = AO.OrganizationId                                    -- Empresas
LEFT JOIN dbo.CollaboratorJobTitles CJT on CJT.CollaboratorId = C.Id                        -- Cargos

WHERE AC.EditionId = 6
AND (ACT.CollaboratorTypeId = 200 OR ACT.CollaboratorTypeId = 201 OR ACT.CollaboratorTypeId = 202) -- 300 -> Audiovisual / 301 -> Música / 302 -> Startup
AND (CJT.LanguageId = 2 OR CJT.LanguageId IS NULL)
AND AC.isDeleted = 0
--AND AOC.IsDeleted = 0
--AND AO.IsDeleted = 0
--AND O.IsDeleted = 0
AND ACT.IsDeleted = 0
AND ACTV.IsDeleted = 0
AND C.IsDeleted = 0'''  
        cursor.execute(query_teste)
        todos_participantes = cursor.fetchall()

        # MONTANDO LISTA DE JSON DOS PARTICIPANTES E NÃO SELECIONADOS           
        json_participantes = []
        json_not_selected = []

        for participante in todos_participantes:
            # CONVIDADOS
            if participante[6] in uuid_convidados:
                convidado = convidados.get(uuid=participante[6])
                json_participante = {}
                for index, item in enumerate(participante):
                    if index == len(participante)-1:
                        json_participante[index] = item
                        json_participante[len(participante)] = convidado.id
                    else:
                        json_participante[index] = item                      
                json_participantes.append(json_participante)

            # NÃO SELECIONADOS
            elif participante[6] in not_selected_uuid:
                convidado = not_selected.get(uuid=participante[6])
                json_participante = {}
                for index, item in enumerate(participante):
                    if index == len(participante)-1:
                        json_participante[index] = item
                        json_participante[len(participante)] = convidado.id
                    else:
                        json_participante[index] = item
                json_not_selected.append(json_participante)
                

                    

        participantes = json_participantes

        nao_selecionados = json_not_selected

        # MONTANDO LISTA DE JSON NÃO SELECIONADOS PELO PATROCINADOR



        participantes_extras = ConvidadosExtras.objects.filter(evento=evento)

        nr_participantes_extras = (participantes_extras.count())
        nr_convidados = convidados.count()

        nr_participantes = nr_participantes_extras + nr_convidados

        return render(request, 'Aprovacao.html', {
            'evento': evento,
            'participantes': participantes,
            'nao_selecionados': nao_selecionados,
            'url_home': url_home,
            'participantes_extras':participantes_extras,
            'nr_participantes': nr_participantes

        })

    else:
        return erro_permissao

@login_required
def api_populateTableAprovacao(request, id):
    usuario = request.user
    if usuario.role == 'comercial':
        id = decrypt(id)
        evento = Eventos.objects.get(id=id)
        convidados = evento.convidados.filter(postSelected=True)
        lista_uuid = [convidado.id for convidado in convidados]
        #Convidados.objects.create( uuid = uuid_convidado, local=1, vip=0, evento=evento, createUserId= usuario )
        return JsonResponse({"response": lista_uuid})
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a utilizar esta API.'})

@login_required
def api_post_convidado_aprovacao(request):
    usuario = request.user
    if usuario.role == 'comercial':
        if request.method == 'POST':

            convidado_data = request.body.decode('utf-8')
            convidado_data = json.loads(convidado_data)

            funcao = convidado_data['funcao']

            if(funcao == 'add'):
                print('add aprovacao')
                id_evento = convidado_data['idEvento']
                id_evento = decrypt(id_evento)
                evento = Eventos.objects.get(id=id_evento)

                id_convidado = convidado_data['Uuid']

                convidado = Convidados.objects.get(id = id_convidado)

                convidado.postSelected = True
                
                convidado.save()

                return JsonResponse({'Reponse': 'Ok'})
            
            if (funcao == 'rem'):
                print('rem aprovacao')
                id_convidado = convidado_data['Uuid']

                id_evento = convidado_data['idEvento']
                id_evento = decrypt(id_evento)
                evento = Eventos.objects.get(id=id_evento)

                convidado = Convidados.objects.get(id = id_convidado)

                convidado.postSelected = False

                convidado.save()

                return JsonResponse({'Reponse': 'Ok'})
    else:
        return JsonResponse({'response':'Seu perfil não está autorizado a utilizar essa API.'})

@login_required
def api_post_convidadoextra_aprovacao(request):
    usuario = request.user
    if usuario.role == 'comercial':
        if request.method == 'POST':
            data = request.body.decode('utf-8')
            data = json.loads(data)

            nome = (data['guestName'])
            email = (data['guestEmail'])
            empresa = (data['guestCompany'])
            cargo = (data['guestJobTitle'])
            
            evento_id = data['eventoId']
            evento_id = decrypt(evento_id)
            evento = Eventos.objects.get(id= evento_id)
            
            ConvidadosExtras.objects.create(nome= nome, email = email, empresa = empresa, cargo= cargo, evento= evento, postSelected=True)

            return JsonResponse({'response': 'Ok'})


        else:
            return JsonResponse({'response': 'Erro.'})

    else:
        return JsonResponse({'response': 'Seu perfil não está autorizado a acessar essa API'})

@login_required
def api_post_aprovacao(request, id_evento):
    usuario = request.user
    if usuario.role == 'comercial':
        if request.method == 'POST':
            id_evento = decrypt(id_evento)
            evento = Eventos.objects.get(id=id_evento)

            # JSON FORMATO

            evento_json = {
            "nome":"",
            "local":"",
            "data":"",
            "convidados":"",
            "convidadosExtras":""
            }
            
            # EVENTO
            evento_json["nome"] = (evento.nome)
            evento_json["local"] = (evento.local)
            evento_json["data"] = (evento.data.strftime('%d-%m-%Y'))

            # CONVIDADOS
            condition1 = Q(sponsorSelected=True)
            condition2 = Q(postSelected=True)
            convidados = evento.convidados.filter(condition1 | condition2)

            uuid_convidados = [convidado.uuid for convidado in convidados]

            cnxn = pyodbc.connect("DRIVER={SQL Server};"
                            "SERVER=rio2c-sqlserver.cb5mokkxuw8r.us-east-1.rds.amazonaws.com;"
                            "DATABASE=MyRio2C_Prod;"
                            "UID=user-readonly;PWD=v8Gosb8W3w-p*FHn")
            cursor = cnxn.cursor()
            query_teste='''SELECT CONCAT(C.FirstName, ' ', C.LastNames) AS 'Nome',
        ACTV.Email,
        LOWER(CONCAT('https://assets.my.rio2c.com/img/users/', C.Uid,'_thumbnail.png')) AS 'Foto (500 x 500)',
        CJT.Value AS 'Cargo',
        --O.CompanyName,
        STUFF((
        SELECT NCHAR(13) + '\r\n' + '• ' + O.CompanyName
        FROM dbo.Organizations AS O
        JOIN dbo.AttendeeOrganizationCollaborators AS AOC ON AOC.AttendeeCollaboratorId = AC.Id
        JOIN dbo.AttendeeOrganizations AS AO ON AO.Id = AOC.AttendeeOrganizationId
        WHERE O.Id = AO.OrganizationId
        FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 'Interesses',
        --O.TradeName,
        --CJT.LanguageId as 'Cargo - LanguageId',
        C.ImageUploadDate,
        C.Uid,
            CASE
            WHEN ACT.CollaboratorTypeId = 200 THEN 'Audiovisual'
                ELSE
                    CASE
                        WHEN ACT.CollaboratorTypeId = 201 THEN 'Música'
                    ELSE 'Startup'
                    END
                END AS 'CollaboratorType'
        --CJT.Value  as 'Cargo - Value'

    FROM dbo.AttendeeCollaborators AS AC
    LEFT JOIN dbo.AttendeeCollaboratorTypes AS ACT ON ACT.AttendeeCollaboratorId = AC.Id
    LEFT JOIN dbo.Users AS ACTV ON ACTV.Id = AC.CollaboratorId
    LEFT JOIN dbo.Collaborators AS C ON C.Id = AC.CollaboratorId
    --LEFT JOIN dbo.CollaboratorJobTitles AS CJT ON CJT.CollaboratorId = C.Id
    --LEFT JOIN dbo.AttendeeOrganizationCollaborators AOC ON AOC.AttendeeCollaboratorId = AC.Id    -- Associação entre Empresas/Edição & Colaborador/Edição
    --LEFT JOIN dbo.AttendeeOrganizations AO on AO.Id = AOC.AttendeeOrganizationId                -- Empresas/Edição
    --LEFT JOIN dbo.Organizations O on O.Id = AO.OrganizationId                                    -- Empresas
    LEFT JOIN dbo.CollaboratorJobTitles CJT on CJT.CollaboratorId = C.Id                        -- Cargos

    WHERE AC.EditionId = 6
    AND (ACT.CollaboratorTypeId = 200 OR ACT.CollaboratorTypeId = 201 OR ACT.CollaboratorTypeId = 202) -- 300 -> Audiovisual / 301 -> Música / 302 -> Startup
    AND (CJT.LanguageId = 2 OR CJT.LanguageId IS NULL)
    AND AC.isDeleted = 0
    --AND AOC.IsDeleted = 0
    --AND AO.IsDeleted = 0
    --AND O.IsDeleted = 0
    AND ACT.IsDeleted = 0
    AND ACTV.IsDeleted = 0
    AND C.IsDeleted = 0'''  
            cursor.execute(query_teste)
            todos_participantes = cursor.fetchall()

            json_convidados = {}

            for participante in todos_participantes:
                if participante[6] in uuid_convidados:
                    convidado = convidados.get(uuid=participante[6])
                    json_participante = {}

                    json_participante['id'] = convidado.id
                    json_participante['nome'] = participante[0]
                    json_participante['email'] = participante[1]
                    json_participante['foto'] = participante[2]
                    json_participante['uuid_myrio'] = participante[6]

                    json_convidados[convidado.id] = json_participante

            evento_json["convidados"] = json_convidados


            # CONVIDADOS EXTRAS
                
            convidados_extras = evento.convidadosextras.all()

            convidados_extras_json = {}

            for convidado_extra in convidados_extras:
                convidado_extra_json = {}
                convidado_extra_json["id"] = (convidado_extra.id)
                convidado_extra_json["nome"] = (convidado_extra.nome)
                convidado_extra_json["email"] = (convidado_extra.email)

                convidados_extras_json[convidado_extra.id] = convidado_extra_json
            
            evento_json["convidadosExtras"] = convidados_extras_json

            evento_json = str(evento_json)
            evento_json = evento_json.replace("'", '"')

            print(evento_json)
            #evento.status = 'Lista concluida'
            #evento.save()

            return JsonResponse({'response':'ok'})
        else:
            return JsonResponse({'response':'Method not allowed'})
    else:
        return erro_permissao


def api_rsvp(request):
    estrutura_json= {
        'nome':'',
        'local':'',
        'data':'',
        'convidados':'',
        'convidadosExtras':''
    }
# FIM PÁGINA APROVAÇÃO


# ----- AGENDA -----
@login_required
def agenda(request):
    usuario = request.user
    if usuario.role == 'comercial':
        
        myEvents = serializers.serialize('json', Eventos.objects.all())
        
        
        return render(request, 'Agenda.html', {
            'eventos': myEvents
        })
    else:
        return erro_permissao

@login_required
def api_eventos(request):
    usuario = request.user

    if usuario.role=='comercial':
        if request.method == 'GET':
            eventos = Eventos.objects.all()
            json_evento = serializers.serialize('json', eventos)

            return JsonResponse({'response':json_evento})

        else:
            return JsonResponse({'response':'Error'})

    else:
        return erro_permissao

# FIM AGENDA


    # -- - -- - -- - -- - MELHORIAS PENDENTES -- - -- - -- - -- - -- -
    
        # CRUDE para edição convidados extras na página do patrocinador
        # Limiter na capacidade do evento a seleção do lado do patrocinador

    # -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - 