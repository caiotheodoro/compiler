import os
import sys
import pandas as pd
import numpy as np
from llvmlite import ir
from llvmlite import binding 
from sys import argv
from myerror import MyError
from tppsema import retorna_arvore_tabela
from utils import cria_modulo, func_inicializa

error_handler = MyError('SemaErrors')


global builder


config = { # Configurações iniciais de variáveis que serão utilizadas no código
    'escopo': '',
    'modulo': None,
    'tab_sym': None,
    'pilha_bloco_saida': [],
    'pilha_loop_validacao': [],
    'pilha_loop': [],
    'variaveis_declaradas': [],
    'nome_escopo_alocada': [],
    'lista_declaracao_funcao': [],
    'lista_escopo': [],
    'parametros_lista': [],
    'w_int': None,
    'w_float': None,
    'tem_se': False,
}


def ver_exp_par(parametro): 
    funcao_variaveis_parametro = [] 
    funcao_tabela_simbolos = config['tab_sym'][(config['tab_sym']['lex'] == config['escopo']) & (config['tab_sym']['funcao'] == '1')] # Procura na tabela de simbolos a função que está sendo chamada
    parametros_funcao_tabela_simbolos = funcao_tabela_simbolos['parametros'].values[0] # Pega os parametros da função

    for param_tabela_simbolos in parametros_funcao_tabela_simbolos: # Percorre os parametros da função
        funcao_variaveis_parametro.extend(param_tabela_simbolos.keys()) # Adiciona os parametros na lista de variaveis da função

    parametros_argumentos = config['parametros_lista'][-1] # Pega os parametros da função que está sendo chamada
    expressao_esquerda_temp = parametros_argumentos.args[funcao_variaveis_parametro.index(parametro)] if parametro in funcao_variaveis_parametro else acha_var_aux(parametro) # Verifica se o parametro está na lista de variaveis da função, se estiver pega o parametro, se não procura na tabela de simbolos
    return expressao_esquerda_temp # Retorna o parametro


def aux_chamado_func(no_chama_funcao): # Função que auxilia o chamado de funções
    def acha_chamada_funcao(label): # Função que acha o chamado de funções
        args = [] # Lista de argumentos
        for i in range(3, len(no_chama_funcao.children), 2): # Percorre os argumentos da função
            if i < len(no_chama_funcao.children) and no_chama_funcao.children[i].label: # Verifica se o argumento é válido
                func_achada = acha_var_aux(no_chama_funcao.children[i].label) # Procura o argumento na tabela de simbolos
                func_declarada = acha_func_decl_aux(label) # Procura a função na tabela de simbolos
                if func_achada and func_declarada: # Verifica se a função e o argumento foram encontrados
                    args.append(builder.load(func_achada)) # Adiciona o argumento na lista de argumentos
                else:
                    pass

        if func_declarada and args: # Verifica se a função e os argumentos foram encontrados
            return builder.call(func_declarada, args=args) # Retorna a função com os argumentos
        else:
            pass
    encontra_chamada_funcao_esquerda = acha_chamada_funcao(no_chama_funcao.children[3].label) # Procura o chamado de função na esquerda
    encontra_chamada_funcao_direita = acha_chamada_funcao(no_chama_funcao.children[6].label) # Procura o chamado de função na direita

    return encontra_chamada_funcao_esquerda, encontra_chamada_funcao_direita 


def operacoes_aux(expressao_esquerda_temp, expressao_direita_temp, operacao_sinal):
    operations = {
        '+': builder.add,
        '-': builder.sub,
        '*': builder.mul,
        '/': builder.sdiv,
    } # Dicionário de operações

    return operations[operacao_sinal](expressao_esquerda_temp, expressao_direita_temp, name=f'{operacao_sinal} result') # Retorna a operação


def acha_expressoes_aux(expressao):
    operacoes_lista = ['+', '-', '*', '/'] 
    operacao = any(child.label in operacoes_lista for child in expressao.children)  # Verifica se a expressão é uma operação

    if operacao: 
        child = expressao.children[1] if len(expressao.children) == 3 and len(expressao.children[1].children) == 0 else expressao.children[1].children[0] # Pega o filho da expressão
        return expressao.children[0].label, child.label, expressao.children[2].label # Retorna a expressão


def acha_comp_aux(no_ate):
    repita = no_ate.parent # Pega o pai do nó 
    posicao_ate = repita.children.index(no_ate) # Pega a posição do nó

    if len(repita.children) - posicao_ate == 4: # Verifica se o nó é uma comparação
        return repita.children[posicao_ate + 1].label, repita.children[posicao_ate + 2].label, repita.children[posicao_ate + 3].label # Retorna a comparação

def acha_func_decl_aux(nome_funcao): 
    if nome_funcao == 'principal': # Verifica se a função é a principal
        nome_funcao = 'main' # Muda o nome da função para main

    if nome_funcao in config['lista_escopo']: # Verifica se a função está na lista de escopos
        return config['lista_declaracao_funcao'][config['lista_escopo'].index(nome_funcao)] # Retorna a função
    return ''


def acha_var_aux(nome_variavel):
    for escopo_nome in [nome_variavel + config['escopo'], nome_variavel + 'global']: # Percorre os escopos
        if escopo_nome in config['nome_escopo_alocada']: # Verifica se o escopo está na lista de escopos
            return config['variaveis_declaradas'][config['nome_escopo_alocada'].index(escopo_nome)] # Retorna a variável

    return ''


def decl_variaveis_utils(linha,no):
    variavel = config['tab_sym'][config['tab_sym']['linha'] == linha] # Procura a variável na tabela de simbolos

    if 'global' == str(variavel['escopo'].values[0]): # Verifica se a variável é global
        if 'inteiro' == str(variavel['tipo'].values[0]): # Verifica se a variável é inteira
            if len(no.children) > 3: # Verifica se a variável é um array
                tamanho_primeira_dimensao = no.children[3].label # Pega o tamanho da primeira dimensão do array
                array_tipo = ir.ArrayType(ir.IntType(32), int(tamanho_primeira_dimensao)) # Cria o array
            else:
                array_tipo = ir.IntType(32) 

            array_global = ir.GlobalVariable(config['modulo'], array_tipo, variavel['lex'].values[0]) # Cria a variável global
            array_global.initializer = ir.Constant(array_tipo, None) # Inicializa a variável global
            array_global.linkage = "common" # Linka a variável global
            array_global.align = 4 # Alinha a variável global

            config['variaveis_declaradas'].append(array_global) # Adiciona a variável global na lista de variáveis declaradas
            config['nome_escopo_alocada'].append(variavel['lex'].values[0] + 'global') # Adiciona o nome da variável global na lista de escopos alocados
        else:
            if len(no.children) > 3: # Verifica se a variável é um array 
                tamanho_primeira_dimensao = no.children[3].label # Pega o tamanho da primeira dimensão do array
                array_tipo = ir.ArrayType(ir.FloatType(), int(tamanho_primeira_dimensao)) # Cria o array
            else:
                array_tipo = ir.FloatType()

            array_global = ir.GlobalVariable(config['modulo'], array_tipo, variavel['lex'].values[0]) # Cria a variável global
            array_global.initializer = ir.Constant(array_tipo, None) # Inicializa a variável global
            array_global.linkage = "common" # Linka a variável global
            array_global.align = 4 # Alinha a variável global

            config['variaveis_declaradas'].append(array_global) # Adiciona a variável global na lista de variáveis declaradas
            config['nome_escopo_alocada'].append(variavel['lex'].values[0] + 'global') # Adiciona o nome da variável global na lista de escopos alocados
        return None
    else:
       return variavel # Retorna a variável

def decl_funcao_utils(linha,no):
    global builder
    criacao_funcao = None 
    declaracao_funcao = None
    
    funcao_encontrada = config['tab_sym'][config['tab_sym']['linha'] == linha] # Procura a função na tabela de simbolos

    config['escopo'] = funcao_encontrada['lex'].values[0] # Muda o escopo para o escopo da função
  
    if 'inteiro' == no.children[0].label: # Verifica se a função é inteira
        if len(funcao_encontrada['parametros'].values[0]) == 0: # Verifica se a função não tem parâmetros
            criacao_funcao = ir.FunctionType(ir.IntType(32), ()) # Cria a função

        elif len(funcao_encontrada['parametros'].values[0]) == 1: # Verifica se a função tem um parâmetro
            criacao_funcao = ir.FunctionType(ir.IntType(32), [ir.IntType(32)]) # Cria a função

        else:
            param_types = [ir.IntType(32) for _ in range(len(funcao_encontrada['parametros'].values[0]))] # Cria os parâmetros da função
            criacao_funcao = ir.FunctionType(ir.IntType(32), param_types) # Cria a função

    if funcao_encontrada['lex'].values[0] == 'principal': # Verifica se a função é a principal
        declaracao_funcao = ir.Function(config['modulo'], criacao_funcao, name='main') # Cria a função
        config['lista_escopo'].append('main') # Adiciona o nome da função na lista de escopos
        config['lista_declaracao_funcao'].append(declaracao_funcao) # Adiciona a função na lista de funções

    elif criacao_funcao:
        declaracao_funcao = ir.Function(config['modulo'], criacao_funcao, name=funcao_encontrada['lex'].values[0]) # Cria a função
        config['lista_escopo'].append(funcao_encontrada['lex'].values[0]) # Adiciona o nome da função na lista de escopos
        config['lista_declaracao_funcao'].append(declaracao_funcao) # Adiciona a função na lista de funções

    parametros_funcao = funcao_encontrada['parametros'].values[0] # Pega os parâmetros da função

    quantidade_parametros = 0

    for parametros in parametros_funcao:
        for param_nome, _ in parametros.items():   # Percorre os parâmetros da função
            if declaracao_funcao:
                declaracao_funcao.args[quantidade_parametros].name = param_nome # Adiciona o nome do parâmetro na função
                quantidade_parametros += 1 # Incrementa a quantidade de parâmetros
 
    config['parametros_lista'].append(declaracao_funcao) # Adiciona a função na lista de parâmetros

    if declaracao_funcao:
        bloco_entrada = declaracao_funcao.append_basic_block('entry') # Cria o bloco de entrada da função
        bloco_saida = declaracao_funcao.append_basic_block('exit') # Cria o bloco de saída da função

        # Put exit blocks on a stack
        config['pilha_bloco_saida'].append(bloco_saida) # Adiciona o bloco de saída na pilha

        # Add the entry block 
        builder = ir.IRBuilder(bloco_entrada) # Cria o bloco de entrada

def decl_retorna_utils(linha,no):
    linha = no.label.split(':') # Pega a linha do nó
    linha = linha[1] 

    retorno_encontrado = config['tab_sym'][(config['tab_sym']['lex'] == 'retorna') & (config['tab_sym']['linha'] == linha)] # Procura o retorno na tabela de simbolos

    if not retorno_encontrado.empty: # Verifica se o retorno foi encontrado
        retorno_valor = retorno_encontrado['valor'].values[0] # Pega o valor do retorno 

    topo_bloco_saida = config['pilha_bloco_saida'].pop() # Pega o bloco de saída do topo da pilha

    if (not config['tem_se']): # Verifica se tem um 'se'
        builder.branch(topo_bloco_saida) # Cria o branch do bloco de saída

    builder.position_at_end(topo_bloco_saida) # Posiciona o bloco de saída no topo

    variavel_retornada_encontrada = '' 

    if len(no.children) ==1 : # Verifica se o nó tem filhos
        if len(retorno_encontrado['tipo'].values) > 0:
            if ('inteiro' == retorno_encontrado['tipo'].values[0]):
                for ret in retorno_valor: # Percorre o retorno
                    for variavel_retornada, tipo_retornado in ret.items(): # Percorre a variável retornada
                        variavel_retornada_encontrada = variavel_retornada # Pega a variável retornada

            elif ('float' == retorno_encontrado['tipo'].values[0]): # Verifica se o retorno é float
                pass

        if variavel_retornada_encontrada.isdigit(): # Verifica se a variável retornada é um dígito
            retorno_zero = ir.Constant(ir.IntType(32), variavel_retornada) # Cria o retorno
            builder.ret(retorno_zero)
        else:
            declaracao = acha_var_aux(variavel_retornada_encontrada) # Procura a variável retornada na tabela de simbolos
            if declaracao:
                builder.ret(builder.load(declaracao, "")) # Cria o retorno

    else:
        expressao_esquerda, operacao_sinal, expressao_direita = acha_expressoes_aux(no) # Pega as expressões
        
        if (expressao_esquerda.isdigit()):
            expressao_esquerda_temp = ir.Constant(ir.IntType(32), expressao_esquerda) # Cria a expressão esquerda
            expressao_direita_temp = ir.Constant(ir.IntType(32), expressao_direita)  # Cria a expressão direita

        else:
            funcao_variaveis_parametro = []
            funcao_tabela_simbolos = config['tab_sym'][(config['tab_sym']['lex'] == config['escopo']) & (config['tab_sym']['funcao'] == '1')] # Procura na tabela de simbolos a função que está sendo chamada
            parametros_funcao_tabela_simbolos = funcao_tabela_simbolos['parametros'].values[0] # Pega os parametros da função

            for param_tabela_simbolos in parametros_funcao_tabela_simbolos: # Percorre os parametros da função
                for retorno_nome_tabela_simbolos, _ in param_tabela_simbolos.items(): # Percorre o nome da variável retornada
                    funcao_variaveis_parametro.append(retorno_nome_tabela_simbolos) # Adiciona o nome da variável retornada na lista de variáveis da função
                 
            parametros_argumentos = config['parametros_lista'].pop() # Pega os parâmetros da função que está sendo chamada

            if expressao_esquerda in funcao_variaveis_parametro:
                posicao_variavel = funcao_variaveis_parametro.index(expressao_esquerda) # Pega a posição da variável
                expressao_esquerda_temp = parametros_argumentos.args[posicao_variavel] # Pega a expressão esquerda
            else:
                variavel_expressao_esquerda = acha_var_aux(expressao_esquerda)
                expressao_esquerda_temp = builder.load(variavel_expressao_esquerda, name=str(expressao_esquerda) + '_temp') # Pega a expressão esquerda

            if expressao_direita in funcao_variaveis_parametro: # Verifica se a expressão direita está na lista de variáveis da função
                posicao_variavel_direita = funcao_variaveis_parametro.index(expressao_direita) # Pega a posição da variável
                expressao_direita_temp = parametros_argumentos.args[posicao_variavel_direita] # Pega a expressão direita
            else:
                variavel_expressao_direita = acha_var_aux(expressao_direita)
                expressao_direita_temp = builder.load(variavel_expressao_direita, name=str(expressao_direita) + '_temp') # Pega a expressão direita

        resultado_op = operacoes_aux(expressao_esquerda_temp, expressao_direita_temp, operacao_sinal) # Pega o resultado da operação
        builder.ret(resultado_op)

def decl_acao_utils(linha,no):
    if (no.children[1].label == ':=' or no.children[1].label == '['): # Verifica se o nó é uma atribuição
        verifica_nome_funcao = no.children[2].label # Pega o nome da função

        pesquisa_nome_funcao = config['tab_sym'][(config['tab_sym']['lex'] == verifica_nome_funcao) & (config['tab_sym']['funcao'] == '1')] # Procura o nome da função na tabela de simbolos

        if len(pesquisa_nome_funcao) > 0: # Verifica se o nome da função foi encontrado
 
            recebe_chamada_funcao = acha_var_aux(no.children[0].label)  # Procura a variável que recebe o chamado da função

            if len(no.children) > 5:
                resultado_chamada_funcao_esquerda, resultado_chamada_funcao_direita = aux_chamado_func(no) # Pega o resultado da chamada da função

                esquerda_temp = builder.alloca(ir.IntType(32), name='chamada_temp_1') # Cria a variável temporária da esquerda
                builder.store(resultado_chamada_funcao_esquerda, esquerda_temp) # Armazena o resultado da chamada da função na variável temporária da esquerda

                direita_temp = builder.alloca(ir.IntType(32), name='chamada_temp_2') # Cria a variável temporária da direita
                builder.store(resultado_chamada_funcao_direita, direita_temp) # Armazena o resultado da chamada da função na variável temporária da direita

                encontra_chamada_funcao_inicial = acha_func_decl_aux(no.children[2].label) # Procura o chamado da função inicial

                chamada_funcao = builder.call(encontra_chamada_funcao_inicial, [builder.load(esquerda_temp), builder.load(direita_temp)]) # Chama a função inicial
                builder.store(chamada_funcao, recebe_chamada_funcao) # Armazena o resultado da chamada da função na variável que recebe o chamado da função
            else:
                acha_chamada_funcao = acha_func_decl_aux(no.children[2].label) # Procura o chamado da função
                operador_esquerdo_declaracao = acha_var_aux(no.children[3].label) # Procura o operador esquerdo da declaração
                operador_direito_declaracao = acha_var_aux(no.children[4].label) # Procura o operador direito da declaração

                chamada_funcao = builder.call(acha_chamada_funcao, [builder.load(operador_esquerdo_declaracao), builder.load(operador_direito_declaracao)]) # Chama a função
                builder.store(chamada_funcao, recebe_chamada_funcao) # Armazena o resultado da chamada da função na variável que recebe o chamado da função

        else:

            if len(no.children) == 3: # Verifica se o nó tem 3 filhos
                
                nome_variavel_recebendo = no.children[0].label # Pega o nome da variável que recebe a atribuição

                # representa o nome da variável y 
                nome_variavel_atribuida = no.children[2].label # Pega o nome da variável que recebe a atribuição
                
                # Procuro o tipo da variável atribuída
                tipo_variavel_atribuida = config['tab_sym'][config['tab_sym']['lex'] == nome_variavel_atribuida] # Procura o tipo da variável atribuída na tabela de simbolos
                
                if len(tipo_variavel_atribuida) > 0:
                    tipo_variavel_atribuida = tipo_variavel_atribuida['tipo'].values[0] # Pega o tipo da variável atribuída
                else:
                    # Verifico se é um valor 
                    if nome_variavel_atribuida.isdigit():
                        # Verifico se é inteiro ou flutuante 
                        tipo_variavel_atribuida = 'inteiro' # Atribuo o tipo da variável atribuída
                    
                    elif '.' in nome_variavel_atribuida:
                        # É flutuante
                        tipo_variavel_atribuida = 'flutuante' # Atribuo o tipo da variável atribuída


                variavel_declaracao_encontrada = '' # Variável que armazena a variável declarada
                # Primeiro procuro no escopo local e depois no global 
                if nome_variavel_recebendo+config['escopo'] in config['nome_escopo_alocada']: # Verifica se a variável está no escopo local
                    # Pegar a posição onde se encontra esse valor e acessar as variaveis declaradas
                    variavel_declaracao_encontrada  = config['variaveis_declaradas'][config['nome_escopo_alocada'].index(nome_variavel_recebendo+config['escopo'])] # Pega a variável declarada

                else:
                    if nome_variavel_recebendo+'global' in config['nome_escopo_alocada']: # Verifica se a variável está no escopo global
                        variavel_declaracao_encontrada  = config['variaveis_declaradas'][config['nome_escopo_alocada'].index(nome_variavel_recebendo+'global')] # Pega a variável declarada

                # Verifica se o valor que está sendo atribuído é uma variável
                valor_encontrado_atribuindo = acha_var_aux(nome_variavel_atribuida) # Procura o valor que está sendo atribuído na tabela de simbolos

                if valor_encontrado_atribuindo == '':
                    if tipo_variavel_atribuida == 'inteiro':
                        builder.store(ir.Constant(ir.IntType(32), nome_variavel_atribuida), variavel_declaracao_encontrada) # Armazena o valor na variável que recebe a atribuição
                    else:
                        builder.store(ir.Constant(ir.FloatType(), float(nome_variavel_atribuida)), variavel_declaracao_encontrada) # Armazena o valor na variável que recebe a atribuição
                else:
                    variavel_temporaria = builder.load(valor_encontrado_atribuindo, "") # Pega a variável temporária
                    builder.store(variavel_temporaria, variavel_declaracao_encontrada) # Armazena o valor na variável que recebe a atribuição
            else:
                if no.children[1].label == '[': # Verifica se o nó é um vetor
                    if len(no.children) == 6: 
                        nome_variavel_recebendo = acha_var_aux(no.children[0].label) # Procura a variável que recebe a atribuição

                        posicao_array = no.children[2].label # Pega a posição do array
                        posicao_array_variavel = acha_var_aux(posicao_array) # Procura a posição do array na tabela de simbolos

                        posicao_variavel_temporaria = builder.alloca(ir.IntType(32), name='pos_temp_1') # Cria a variável temporária da posição
                        builder.store(builder.load(posicao_array_variavel), posicao_variavel_temporaria) # Armazena a posição do array na variável temporária da posição

                        valor_recebendo = no.children[5].label # Pega o valor que está sendo atribuído
                        if valor_recebendo.isdigit(): # Verifica se o valor que está sendo atribuído é um dígito
                            tipo_inteiro = ir.IntType(32) # Cria o tipo inteiro
                            atribuicao_esquerda = builder.gep(nome_variavel_recebendo, [tipo_inteiro(0), tipo_inteiro(int(valor_recebendo))], name=str(no.children[0].label) + '_pos') # Cria a atribuição da esquerda

                            builder.store(atribuicao_esquerda, builder.load(valor_recebendo))  # Guarda o valor na variável que recebe a atribuição

                        else:
                            valor_recebendo_declaracao = acha_var_aux(valor_recebendo) # Procura o valor que está sendo atribuído na tabela de simbolos
                            tipo_inteiro = ir.IntType(32) # Cria o tipo inteiro
                            atribuicao_esquerda = builder.gep(nome_variavel_recebendo, [tipo_inteiro(0), builder.load(posicao_variavel_temporaria)], name=str(no.children[0].label) + '_pos')

                            builder.store(builder.load(valor_recebendo_declaracao), atribuicao_esquerda)    # Guarda o valor na variável que recebe a atribuição


                else:
                    nome_variavel_recebendo = acha_var_aux(no.children[0].label) # Procura a variável que recebe a atribuição

                    nome_variavel_atribuida_esquerda = no.children[2].label # Pega o nome da variável que recebe a atribuição
                    operacao_sinal = no.children[3].label # Pega o sinal da operação
                    nome_variavel_atribuida_direita = no.children[4].label # Pega o nome da variável que recebe a atribuição
                    
                    if (nome_variavel_atribuida_esquerda.isdigit()): 
                        nome_variavel_atribuida_esquerda_declarada = ir.Constant(ir.IntType(32), name=nome_variavel_atribuida_esquerda) # Cria a variável que recebe a atribuição

                    else:
                        nome_variavel_atribuida_esquerda_encontrada = acha_var_aux(nome_variavel_atribuida_esquerda) # Procura a variável que recebe a atribuição na tabela de simbolos
                        if nome_variavel_atribuida_esquerda_encontrada == '': # Verifica se a variável que recebe a atribuição foi encontrada
                            nome_variavel_atribuida_esquerda = ver_exp_par(nome_variavel_atribuida_esquerda) # Verifica a expressão da variável que recebe a atribuição

                            nome_variavel_atribuida_esquerda_encontrada = builder.alloca(ir.IntType(32), name='param') # Cria a variável que recebe a atribuição
                            builder.store(nome_variavel_atribuida_esquerda, nome_variavel_atribuida_esquerda_encontrada) # Armazena a variável que recebe a atribuição na variável que recebe a atribuição

                        nome_variavel_atribuida_esquerda_declarada = builder.load(nome_variavel_atribuida_esquerda_encontrada, name='_temp') # Pega a variável que recebe a atribuição
                    if (nome_variavel_atribuida_direita.isdigit()): # Verifica se a variável que recebe a atribuição é um dígito
                        nome_variavel_atribuida_direita_declarada = ir.Constant(ir.IntType(32), int(nome_variavel_atribuida_direita)) # Cria a variável que recebe a atribuição
                        

                    else:
                        nome_variavel_atribuida_direita_declarada_encontrada = acha_var_aux(nome_variavel_atribuida_direita) # Procura a variável que recebe a atribuição na tabela de simbolos
                        if nome_variavel_atribuida_direita_declarada_encontrada == '': # Verifica se a variável que recebe a atribuição foi encontrada
                            nome_variavel_atribuida_direita_declarada = ver_exp_par(nome_variavel_atribuida_direita) # Verifica a expressão da variável que recebe a atribuição
                            
                            nome_variavel_atribuida_direita_declarada_encontrada = builder.alloca(ir.IntType(32), name='param') # Cria a variável que recebe a atribuição
                            builder.store(nome_variavel_atribuida_direita_declarada_encontrada, nome_variavel_atribuida_direita_declarada_encontrada) # Armazena a variável que recebe a atribuição na variável que recebe a atribuição
                            nome_variavel_atribuida_direita_declarada_encontrada = builder.load(nome_variavel_atribuida_direita_declarada_encontrada) # Pega a variável que recebe a atribuição
                        
                        nome_variavel_atribuida_direita_declarada = builder.load(nome_variavel_atribuida_direita_declarada_encontrada, name='_temp') 
                        
                    # Chama função que vai declarar a operação
                    operacao_declarada = operacoes_aux(nome_variavel_atribuida_esquerda_declarada, nome_variavel_atribuida_direita_declarada, operacao_sinal) # Pega a operação declarada

                    builder.store(operacao_declarada, nome_variavel_recebendo) # Armazena a operação declarada na variável que recebe a atribuição


def decl_se_utils(linha,no):
    config['tem_se'] = True
    declaracao_funcao_encontrada = acha_func_decl_aux(config['escopo'])

    if_verdade_1 = declaracao_funcao_encontrada.append_basic_block('iftrue_1') # Cria o bloco de verdade
    if_falso_1 = declaracao_funcao_encontrada.append_basic_block('iffalse_1') # Cria o bloco de falsidade
    
    if_saida_1 = declaracao_funcao_encontrada.append_basic_block('ifend1') # Cria o bloco de saída
    config['pilha_bloco_saida'].append(if_saida_1)  # Adiciona o bloco de saída na pilha
    config['pilha_bloco_saida'].append(if_falso_1) # Adiciona o bloco de falsidade na pilha

    comparacao_variavel_esquerda = acha_var_aux(no.children[0].label) # Procura a variável da esquerda na tabela de simbolos
    comparacao_variavel_direita = ir.Constant(ir.IntType(32), int(no.children[2].label)) # Pega a variável da direita

    if len(no.children[1].children) > 0:
        comparacao_operacao = builder.icmp_signed(str(no.children[1].children[0].label), builder.load(comparacao_variavel_esquerda), comparacao_variavel_direita) # Pega a operação da comparação
    else:
        comparacao_operacao = builder.icmp_signed(str(no.children[1].label), builder.load(comparacao_variavel_esquerda), comparacao_variavel_direita) # Pega a operação da comparação
    
    builder.cbranch(comparacao_operacao, if_verdade_1, if_falso_1) # Cria o branch da comparação
 
    builder.position_at_end(if_verdade_1) # Posiciona o bloco de verdade no topo


def decl_senao_utils(linha,no):
    bloco_falsidade = config['pilha_bloco_saida'].pop() # Pega o bloco de falsidade do topo da pilha
    topo_bloco_saida = config['pilha_bloco_saida'].pop() # Pega o bloco de saída do topo da pilha

    builder.branch(topo_bloco_saida) # Cria o branch do bloco de saída

    builder.position_at_end(bloco_falsidade) # Posiciona o bloco de falsidade no topo

    config['pilha_bloco_saida'].append(topo_bloco_saida) # Adiciona o bloco de saída na pilha


def decl_fim_se_utils(linha,no):
    bloco_topo = []
    if config['pilha_bloco_saida']: # Verifica se a pilha de blocos de saída não está vazia
        bloco_topo = config['pilha_bloco_saida'].pop() # Pega o bloco do topo da pilha
        saida_bloco_principal = config['pilha_bloco_saida'].pop() # Pega o bloco de saída do topo da pilha

        builder.branch(bloco_topo) # Cria o branch do bloco do topo

        builder.position_at_end(bloco_topo) # Posiciona o bloco do topo no topo
        builder.branch(saida_bloco_principal) # Cria o branch do bloco de saída principal

        config['pilha_bloco_saida'].append(saida_bloco_principal) # Adiciona o bloco de saída principal na pilha


def decl_repita_utils(linha,no):
    loop = builder.append_basic_block('loop') # Cria o loop
    loop_validacao = builder.append_basic_block('loop_val') # Cria o loop de validação
    loop_end = builder.append_basic_block('loop_end') # Cria o loop de saída

    config['pilha_loop_validacao'].append(loop_validacao) # Adiciona o loop de validação na pilha
    config['pilha_loop'].append(loop) # Adiciona o loop na pilha
    config['pilha_bloco_saida'].append(loop_end) # Adiciona o loop de saída na pilha

    builder.branch(loop) # Cria o branch do loop

    builder.position_at_end(loop)        # Posiciona o loop no topo

def decl_ate_utils(linha,no):
    _ = config['pilha_loop_validacao'].pop()
    saida = config['pilha_bloco_saida'].pop()
    loop_inicial = config['pilha_loop'].pop()

    comparacao_esquerda, comparacao_sinal, comparacao_direita = acha_comp_aux(no) # Pega a comparação

    if comparacao_direita.isdigit():
        comparacao_valor = ir.Constant(ir.IntType(32), int(comparacao_direita)) # Cria a comparação
    comparacao_variavel = acha_var_aux(comparacao_esquerda) # Procura a variável da comparação na tabela de simbolos
    if '=' == comparacao_sinal:
        expressao = builder.icmp_signed('==', builder.load(comparacao_variavel), comparacao_valor, name='expressao_igualdade') # Pega a expressão da comparação
        builder.cbranch(expressao, loop_inicial, saida) # Cria o branch da comparação
 
    builder.position_at_end(saida) # Posiciona o bloco de saída no topo


def decl_escreva_utils(linha,no,w_int,w_float):
    valor_escrita = no.children[0].label # Pega o valor da escrita

    tipo_variavel_escrita = config['tab_sym'][config['tab_sym']['lex'] == str(valor_escrita)] # Procura o tipo da variável que está sendo escrita na tabela de simbolos
    tipo_variavel_escrita = tipo_variavel_escrita['tipo'].values[0] # Pega o tipo da variável que está sendo escrita

    if valor_escrita.isdigit():
        valor_escrita_constante = ir.Constant(ir.IntType(32), int(valor_escrita)) # Cria o valor da escrita
        builder.call(config['w_int'], args=[valor_escrita_constante]) # Chama a função de escrita
    else:
        variavel_escrever = acha_var_aux(valor_escrita)
        if tipo_variavel_escrita == 'inteiro':
            if w_int.function_type.return_type ==  ir.IntType(32):  # Verifica se o tipo da função de escrita é inteiro
                builder.call(w_int, args=[builder.load(variavel_escrever)]) # Chama a função de escrita
        else:
            builder.call(w_float, args=[builder.load(variavel_escrever)]) # Chama a função de escrita


def decl_leia_utils(linha,no):
    global r_int
    global r_float
    variavel_leia = no.children[0].label # Pega a variável que está sendo lida

    tipo_variavel_leitura = config['tab_sym'][config['tab_sym']['lex'] == variavel_leia] # Procura o tipo da variável que está sendo lida na tabela de simbolos
    tipo_variavel_leitura = tipo_variavel_leitura['tipo'].values[0] # Pega o tipo da variável que está sendo lida

    variavel_recebe_leitura = acha_var_aux(variavel_leia) # Procura a variável que recebe a leitura na tabela de simbolos

    if tipo_variavel_leitura == 'inteiro':
        leia_funcao_chamada = builder.call(r_int, args=[]) 
        builder.store(leia_funcao_chamada, variavel_recebe_leitura, align=4) # Armazena o valor lido na variável que recebe a leitura
    else:
        leia_funcao_chamada = builder.call(r_float, args=[])
        builder.store(leia_funcao_chamada, variavel_recebe_leitura, align=4) 

def main_ll_gerador(arvore):
    global builder

    linha = 0
    if arvore:
        for no in arvore.children:
            linha = no.label.split(':')
            if len(linha) > 1:
                linha = linha[1]
            if 'declaracao_variaveis' in no.label:
                variavel = decl_variaveis_utils(linha,no) 
                if variavel is not None:
                    if 'inteiro' == variavel['tipo'].values[0]:
                        variavel_declarada = builder.alloca(ir.IntType(32), name=variavel['lex'].values[0]) # Cria a variável declarada
                        variavel_declarada.initializer = ir.Constant(ir.IntType(32), 0) 
                    else:
                        variavel_declarada = builder.alloca(ir.FloatType(), name=str(variavel['lex'].values[0])) 
                        variavel_declarada_constante = ir.Constant(ir.FloatType(), 0.0) # Cria a variável declarada constante
                        builder.store(variavel_declarada_constante, variavel_declarada) 

                    variavel_declarada.linkage = "common"
                    variavel_declarada.align = 4

                    config['variaveis_declaradas'].append(variavel_declarada) # Adiciona a variável declarada na lista de variáveis declaradas
                    config['nome_escopo_alocada'].append(variavel['lex'].values[0] + config['escopo']) # Adiciona o nome da variável declarada na lista de nomes do escopo alocada
                    
            elif 'declaracao_funcao' in no.label:
                decl_funcao_utils(linha,no)
            elif ('retorna' in no.label):
                decl_retorna_utils(linha,no)
            elif ('acao' == no.label and len(no.children) > 1):
                decl_acao_utils(linha,no)
            elif (no.label == 'se'):
                decl_se_utils(linha,no)
            elif ('senão' == no.label):
                decl_senao_utils(linha,no)

            elif ('fim' == no.label and 'se' == no.parent.label):
                decl_fim_se_utils(linha,no)

            elif ('repita' == no.label):
                decl_repita_utils(linha,no)
            elif 'ATE' == no.label:
                decl_ate_utils(linha,no)
            elif 'escreva' == no.label:
                decl_escreva_utils(linha,no,config['w_int'],config['w_float'])
            elif 'leia' == no.label:
                decl_leia_utils(linha,no)
            main_ll_gerador(no)
    else:
        print(TypeError(error_handler.newError('ERR-INV-TREE')))


from anytree import RenderTree, AsciiStyle

def out_arq(modulo):
    with open('main.ll', "w") as arquivo:
        arquivo.write(str(modulo))

if __name__ == "__main__":
    if(len(sys.argv) < 2):
        raise TypeError(error_handler.newError('ERR-SEM-USE'))

    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
        raise IOError(error_handler.newError('ERR-SEM-NOT-TPP'))
    elif not os.path.exists(argv[1]):
        raise IOError(error_handler.newError('ERR-SEM-FILE-NOT-EXISTS'))
    else:
        data = open(argv[1])
        source_file = data.read()
        root, config['tab_sym'] = retorna_arvore_tabela(source_file)
        # print(RenderTree(root, style=AsciiStyle()).by_attr())
        
        binding.initialize()  # inicializa o binding do llvm
        binding.initialize_all_targets()  # inicializa os targets do llvm
        binding.initialize_native_target()  # inicializa o target nativo do llvm
        binding.initialize_native_asmprinter()  # inicializa o asmprinter do llvm

        config['modulo'] = cria_modulo()  # cria o config['modulo'] do llvm
        config['w_int'], config['w_float'], r_int, r_float = func_inicializa(
            config['modulo'])  # inicializa as funções de escrita e leitura (serão usadas para a escrita e leitura de variaveis)

    main_ll_gerador(root)
    out_arq(config['modulo'])