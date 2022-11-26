#!/usr/bin/env python3
import asyncio
from tcp import Servidor
import re
Nicks = {}



def validar_nome(nome):
    return re.match(br'^[a-zA-Z][a-zA-Z0-9_-]*$', nome) is not None


def sair(conexao):
    print(conexao, 'conexão fechada')
    conexao.fechar()


def dados_recebidos(conexao, dados):
	if dados == b'':
		return sair(conexao)
	#chamada do tratamento do caso 2
	dados = data_treatment(conexao, dados)
	# recebe todos os elementos de dados menos o ultimo (vazio)
	dados = dados[:-1]
	for dado in dados:
		comando = dado.split(b' ', 1)[0] # recebe a primeira palavra da conexao

		if comando == b'PING':
			itsPing(conexao, dado)
		elif comando == b'NICK':
			itsNick(conexao, dado)
		elif comando == b'PRIVMSG':
			dest_msg = dado.split(b' :', 1)
			#print("destinatario e mensagem: ", dest_msg)
			privatemsg(conexao, dest_msg[0], dest_msg[1])

	print(conexao, dados)

# TRATAMENTO DO CASO 1
def itsPing (conexao, dados):
    
    resposta= b':server PONG server :'
    resposta+= dados.split(b' ', 1)[1] # resposta recebe resposta padrão + payload
    conexao.enviar(resposta)

def conexao_aceita(conexao):
    print(conexao, 'nova conexão')
    conexao.registrar_recebedor(dados_recebidos)
    conexao.dados_residuais = b''


# TRATAMENTO DO CASO 2
def data_treatment(conexao, dados):
	"""
	Funcao para o tratamento de entradas, podendo receber entradas como:
	* 'lin', depois 'h' e depois 'a\r\n'
	e as transforma em 'linha\r\n'
	
	normalmente, para a finalização dos dados, entende-se de que o ultimo elemento da lista 
	dados seja o b'' para sair dessa funçao
	
	retorna uma lista
	"""
	
	if conexao.dados_residuais != b'':
		dados = conexao.dados_residuais + dados
		conexao.dados_residuais = b''
	
	if b'\n' in dados:
		dados = dados.split(b'\n')
		for i in range(len(dados) - 1):
				dados[i] = dados[i] + b'\n'
		if dados[-1] != b'\n':
			conexao.dados_residuais = dados[-1]
			dados[-1] = b''
	else:
		conexao.dados_residuais = conexao.dados_residuais + dados
		dados = []
	return dados
		
# FIM DO CASO 2	
# TRATAMENTO CASO 3 E 4


# ENCONTRA USUARIO
def encontra_usuario(conexao):
	# confirmar se existe uma conexao ja estabelecida
		for chave, valor in Nicks.items():
				if conexao == valor:
					return chave
					
		return b'*'
					
                 
def itsNick (conexao, dados):


	apelido = dados.split(b' ', 1)[1] # extraindo o apelido após o comando
	apelido = apelido.split(b'\r\n')[0] # removendo os caracteres de quebra de linha
	apelido_antigo = encontra_usuario(conexao)	


	# validando apelido 
	if validar_nome(apelido):
		# se o apelido ja tiver nos nicks e nao tem o mesmo valor de conexao
		if apelido.lower() in Nicks:
			conexao.enviar (b':server 433 ' + apelido_antigo + b' ' + apelido + b' :Nickname is already in use\r\n')
			return 
			
		Nicks[apelido.lower()] = conexao
		
		# troca de apelido
		if apelido_antigo != b'*':
			del Nicks[apelido_antigo]
			print("else")
			print(b':' , apelido_antigo , b' NICK ' , apelido , b'\r\n')
			conexao.enviar(b':' + apelido_antigo + b' NICK ' + apelido + b'\r\n')
		
		
		# primeiro apelido
		else:
			conexao.enviar(b':server 001 ' + apelido + b' :Welcome\r\n')
			conexao.enviar(b':server 422 ' + apelido + b' :MOTD File is missing\r\n')
		return	

	  
	# apelido invalido          
	else: 
		conexao.enviar(b':server 432 ' + apelido_antigo + b' '+ apelido + b' :Erroneous nickname\r\n')

# INICIO DO 5
def privatemsg(remetente, destinatario, mensagem):
	#retirando o comando
	remetente = encontra_usuario(remetente)
	destinatario = destinatario.split(b' ', 1)[1]
	#print("destinatario = ", destinatario.lower(), "MENSAGEM = ", mensagem)
	
	# primeira etapa
	if Nicks[destinatario.lower()] and remetente != b'*':
		print("mandou\n\n")
		Nicks[destinatario.lower()].enviar(b':' + remetente + b' PRIVMSG ' + destinatario + b' :' + mensagem + b'\r\n')
		
		
# FIM CASO 5
		
servidor = Servidor(6667)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()