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


config = { ### Configurações iniciais de variáveis que serão utilizadas no código
    'escopo': '',
    'modulo': None,
    'tab_sym': None,
    'pilha_bloco_fim': [],
    'pilha_loop_validacao': [],
    'pilha_loop': [],
    'variaveis_declaradas': [],
    'nome_scope_alocada': [],
    'lista_declaracao_func': [],
    'lista_escopo': [],
    'parametros_lista': [],
    'w_int': None,
    'w_float': None,
    'tem_se': False,
}


def ver_exp_par(parametro): 
    var_func_params = [] 
    func_tab_sym = config['tab_sym'][(config['tab_sym']['lex'] == config['escopo']) & (config['tab_sym']['funcao'] == '1')] # Procura na tabela de simbolos a função que está sendo chamada
    param_func_tab_sym = func_tab_sym['parametros'].values[0] # Pega os parametros da função

    for param_tab_sym in param_func_tab_sym: # Percorre os parametros da função
        var_func_params.extend(param_tab_sym.keys()) # Adiciona os parametros na lista de variaveis da função

    param_args = config['parametros_lista'][-1] # Pega os parametros da função que está sendo chamada
    exp_esq_temp = param_args.args[var_func_params.index(parametro)] if parametro in var_func_params else acha_var_aux(parametro) # Verifica se o parametro está na lista de variaveis da função, se estiver pega o parametro, se não procura na tabela de simbolos
    return exp_esq_temp # Retorna o parametro


def aux_chamado_func(no_chama_func): # Função que auxilia o chamado de funções
    def acha_chamada_func(label): # Função que acha o chamado de funções
        args = [] # Lista de argumentos
        for i in range(3, len(no_chama_func.children), 2): # Percorre os argumentos da função
            if i < len(no_chama_func.children) and no_chama_func.children[i].label: # Verifica se o argumento é válido
                func_achada = acha_var_aux(no_chama_func.children[i].label) # Procura o argumento na tabela de simbolos
                func_declarada = acha_func_decl_aux(label) # Procura a função na tabela de simbolos
                if func_achada and func_declarada: # Verifica se a função e o argumento foram encontrados
                    args.append(builder.load(func_achada)) # Adiciona o argumento na lista de argumentos
                else:
                    pass

        if func_declarada and args: # Verifica se a função e os argumentos foram encontrados
            return builder.call(func_declarada, args=args) # Retorna a função com os argumentos
        else:
            pass
    esq_func = acha_chamada_func(no_chama_func.children[3].label) # Procura o chamado de função na esquerda
    dir_func = acha_chamada_func(no_chama_func.children[6].label) # Procura o chamado de função na direita

    return esq_func, dir_func 


def operacoes_aux(exp_esq_temp, exp_dir_temp, op_sinal):
    ops = {
        '+': builder.add,
        '-': builder.sub,
        '*': builder.mul,
        '/': builder.sdiv,
    } # Dicionário de operações

    return ops[op_sinal](exp_esq_temp, exp_dir_temp, name=f'{op_sinal} result') # Retorna a operação


def acha_expressoes_aux(expressao):
    ops_list = ['+', '-', '*', '/'] 
    op = any(child.label in ops_list for child in expressao.children)  # Verifica se a expressão é uma operação

    if op: 
        child = expressao.children[1] if len(expressao.children) == 3 and len(expressao.children[1].children) == 0 else expressao.children[1].children[0] # Pega o filho da expressão
        return expressao.children[0].label, child.label, expressao.children[2].label # Retorna a expressão


def acha_comp_aux(no_ate):
    repita = no_ate.parent # Pega o pai do nó 
    posicao_ate = repita.children.index(no_ate) # Pega a posição do nó

    if len(repita.children) - posicao_ate == 4: # Verifica se o nó é uma comparação
        return repita.children[posicao_ate + 1].label, repita.children[posicao_ate + 2].label, repita.children[posicao_ate + 3].label # Retorna a comparação

def acha_func_decl_aux(nome_func): 
    if nome_func == 'principal': # Verifica se a função é a principal
        nome_func = 'main' # Muda o nome da função para main

    if nome_func in config['lista_escopo']: # Verifica se a função está na lista de escopos
        return config['lista_declaracao_func'][config['lista_escopo'].index(nome_func)] # Retorna a função
    return ''


def acha_var_aux(nome_variavel):
    for scope_nome in [nome_variavel + config['escopo'], nome_variavel + 'global']: # Percorre os escopos
        if scope_nome in config['nome_scope_alocada']: # Verifica se o escopo está na lista de escopos
            return config['variaveis_declaradas'][config['nome_scope_alocada'].index(scope_nome)] # Retorna a variável

    return ''


def decl_variaveis_utils(linha,no):
    variavel = config['tab_sym'][config['tab_sym']['linha'] == linha] # Procura a variável na tabela de simbolos

    if 'global' == str(variavel['escopo'].values[0]): # Verifica se a variável é global
        if 'inteiro' == str(variavel['tipo'].values[0]): # Verifica se a variável é inteira
            if len(no.children) > 3: # Verifica se a variável é um array
                tamanho_primeira_dimensao = no.children[3].label # Pega o tamanho da primeira dimensão do array
                arr_tipo = ir.ArrayType(ir.IntType(32), int(tamanho_primeira_dimensao)) # Cria o array
            else:
                arr_tipo = ir.IntType(32) 

            arr_global = ir.GlobalVariable(config['modulo'], arr_tipo, variavel['lex'].values[0]) # Cria a variável global
            arr_global.initializer = ir.Constant(arr_tipo, None) # Inicializa a variável global
            arr_global.linkage = "common" # Linka a variável global
            arr_global.align = 4 # Alinha a variável global

            config['variaveis_declaradas'].append(arr_global) # Adiciona a variável global na lista de variáveis declaradas
            config['nome_scope_alocada'].append(variavel['lex'].values[0] + 'global') # Adiciona o nome da variável global na lista de escopos alocados
        else:
            if len(no.children) > 3: # Verifica se a variável é um array 
                tamanho_primeira_dimensao = no.children[3].label # Pega o tamanho da primeira dimensão do array
                arr_tipo = ir.ArrayType(ir.FloatType(), int(tamanho_primeira_dimensao)) # Cria o array
            else:
                arr_tipo = ir.FloatType()

            arr_global = ir.GlobalVariable(config['modulo'], arr_tipo, variavel['lex'].values[0]) # Cria a variável global
            arr_global.initializer = ir.Constant(arr_tipo, None) # Inicializa a variável global
            arr_global.linkage = "common" # Linka a variável global
            arr_global.align = 4 # Alinha a variável global

            config['variaveis_declaradas'].append(arr_global) # Adiciona a variável global na lista de variáveis declaradas
            config['nome_scope_alocada'].append(variavel['lex'].values[0] + 'global') # Adiciona o nome da variável global na lista de escopos alocados
        return None
    else:
       return variavel # Retorna a variável

def decl_func_utils(linha,no):
    global builder
    criacao_func = None 
    declaracao_func = None
    
    funcao_encontrada = config['tab_sym'][config['tab_sym']['linha'] == linha] # Procura a função na tabela de simbolos

    config['escopo'] = funcao_encontrada['lex'].values[0] # Muda o escopo para o escopo da função
  
    if 'inteiro' == no.children[0].label: # Verifica se a função é inteira
        if len(funcao_encontrada['parametros'].values[0]) == 0: # Verifica se a função não tem parâmetros
            criacao_func = ir.FunctionType(ir.IntType(32), ()) # Cria a função

        elif len(funcao_encontrada['parametros'].values[0]) == 1: # Verifica se a função tem um parâmetro
            criacao_func = ir.FunctionType(ir.IntType(32), [ir.IntType(32)]) # Cria a função

        else:
            param_types = [ir.IntType(32) for _ in range(len(funcao_encontrada['parametros'].values[0]))] # Cria os parâmetros da função
            criacao_func = ir.FunctionType(ir.IntType(32), param_types) # Cria a função

    if funcao_encontrada['lex'].values[0] == 'principal': # Verifica se a função é a principal
        declaracao_func = ir.Function(config['modulo'], criacao_func, name='main') # Cria a função
        config['lista_escopo'].append('main') # Adiciona o nome da função na lista de escopos
        config['lista_declaracao_func'].append(declaracao_func) # Adiciona a função na lista de funções

    elif criacao_func:
        declaracao_func = ir.Function(config['modulo'], criacao_func, name=funcao_encontrada['lex'].values[0]) # Cria a função
        config['lista_escopo'].append(funcao_encontrada['lex'].values[0]) # Adiciona o nome da função na lista de escopos
        config['lista_declaracao_func'].append(declaracao_func) # Adiciona a função na lista de funções

    parametros_func = funcao_encontrada['parametros'].values[0] # Pega os parâmetros da função

    quantidade_parametros = 0

    for parametros in parametros_func:
        for param_nome, _ in parametros.items():   # Percorre os parâmetros da função
            if declaracao_func:
                declaracao_func.args[quantidade_parametros].name = param_nome # Adiciona o nome do parâmetro na função
                quantidade_parametros += 1 # Incrementa a quantidade de parâmetros
 
    config['parametros_lista'].append(declaracao_func) # Adiciona a função na lista de parâmetros

    if declaracao_func:
        bloco_entrada = declaracao_func.append_basic_block('entry') # Cria o bloco de entrada da função
        bloco_fim = declaracao_func.append_basic_block(name='exit') # Cria o bloco de saída da função

        config['pilha_bloco_fim'].append(bloco_fim) # Adiciona o bloco de saída na pilha
        builder = ir.IRBuilder(bloco_entrada) # Cria o bloco de entrada
        print(builder ,"builder")

def decl_retorna_utils(linha,no):
    linha = no.label.split(':') # Pega a linha do nó
    linha = linha[1] 

    retorno_encontrado = config['tab_sym'][(config['tab_sym']['lex'] == 'retorna') & (config['tab_sym']['linha'] == linha)] # Procura o retorno na tabela de simbolos

    if not retorno_encontrado.empty: # Verifica se o retorno foi encontrado
        retorno_valor = retorno_encontrado['valor'].values[0] # Pega o valor do retorno 
    topo_bloco_fim = config['pilha_bloco_fim'].pop() # Pega o bloco de saída do topo da pilha
    if (not config['tem_se']): # Verifica se tem um 'se'
        print(type(topo_bloco_fim))
        print("oi3",topo_bloco_fim)
        builder.branch(topo_bloco_fim) # Cria o branch do bloco de saída

    builder.position_at_end(topo_bloco_fim) # Posiciona o bloco de saída no topo

    var_retornada_encontrada = '' 

    if len(no.children) ==1 : # Verifica se o nó tem filhos
        if len(retorno_encontrado['tipo'].values) > 0:
            if ('inteiro' == retorno_encontrado['tipo'].values[0]):
                for ret in retorno_valor: # Percorre o retorno
                    for var_retornada, tipo_retornado in ret.items(): # Percorre a variável retornada
                        var_retornada_encontrada = var_retornada # Pega a variável retornada

            elif ('float' == retorno_encontrado['tipo'].values[0]): # Verifica se o retorno é float
                pass

        if var_retornada_encontrada.isdigit(): # Verifica se a variável retornada é um dígito
            retorno_zero = ir.Constant(ir.IntType(32), var_retornada) # Cria o retorno
            builder.ret(retorno_zero)
        else:
            declaracao = acha_var_aux(var_retornada_encontrada) # Procura a variável retornada na tabela de simbolos
            if declaracao:
                builder.ret(builder.load(declaracao, "")) # Cria o retorno

    else:
        exp_esq, op_sinal, exp_dir = acha_expressoes_aux(no) # Pega as expressões
        
        if (exp_esq.isdigit()):
            exp_esq_temp = ir.Constant(ir.IntType(32), exp_esq) # Cria a expressão esquerda
            exp_dir_temp = ir.Constant(ir.IntType(32), exp_dir)  # Cria a expressão direita

        else:
            var_func_params = []
            func_tab_sym = config['tab_sym'][(config['tab_sym']['lex'] == config['escopo']) & (config['tab_sym']['funcao'] == '1')] # Procura na tabela de simbolos a função que está sendo chamada
            param_func_tab_sym = func_tab_sym['parametros'].values[0] # Pega os parametros da função

            for param_tab_sym in param_func_tab_sym: # Percorre os parametros da função
                for retorno_nome_tab_sym, _ in param_tab_sym.items(): # Percorre o nome da variável retornada
                    var_func_params.append(retorno_nome_tab_sym) # Adiciona o nome da variável retornada na lista de variáveis da função
                 
            param_args = config['parametros_lista'].pop() # Pega os parâmetros da função que está sendo chamada

            if exp_esq in var_func_params:
                posicao_variavel = var_func_params.index(exp_esq) # Pega a posição da variável
                exp_esq_temp = param_args.args[posicao_variavel] # Pega a expressão esquerda
            else:
                var_exp_esq = acha_var_aux(exp_esq)
                exp_esq_temp = builder.load(var_exp_esq, name=str(exp_esq) + '_temp') # Pega a expressão esquerda

            if exp_dir in var_func_params: # Verifica se a expressão direita está na lista de variáveis da função
                posicao_var_dir = var_func_params.index(exp_dir) # Pega a posição da variável
                exp_dir_temp = param_args.args[posicao_var_dir] # Pega a expressão direita
            else:
                var_exp_dir = acha_var_aux(exp_dir)
                exp_dir_temp = builder.load(var_exp_dir, name=str(exp_dir) + '_temp') # Pega a expressão direita

        resultado_op = operacoes_aux(exp_esq_temp, exp_dir_temp, op_sinal) # Pega o resultado da operação
        builder.ret(resultado_op)

def decl_acao_utils(linha,no):
    if (no.children[1].label == ':=' or no.children[1].label == '['): # Verifica se o nó é uma atribuição
        verifica_nome_func = no.children[2].label # Pega o nome da função

        pesquisa_nome_func = config['tab_sym'][(config['tab_sym']['lex'] == verifica_nome_func) & (config['tab_sym']['funcao'] == '1')] # Procura o nome da função na tabela de simbolos

        if len(pesquisa_nome_func) > 0: # Verifica se o nome da função foi encontrado
 
            recebe_chamada_func = acha_var_aux(no.children[0].label)  # Procura a variável que recebe o chamado da função

            if len(no.children) > 5:
                resultado_chamada_func_esq, resultado_chamada_func_dir = aux_chamado_func(no) # Pega o resultado da chamada da função

                esq_temp = builder.alloca(ir.IntType(32), name='chamada_temp_1') # Cria a variável temporária da esquerda
                builder.store(resultado_chamada_func_esq, esq_temp) # Armazena o resultado da chamada da função na variável temporária da esquerda

                dir_temp = builder.alloca(ir.IntType(32), name='chamada_temp_2') # Cria a variável temporária da direita
                builder.store(resultado_chamada_func_dir, dir_temp) # Armazena o resultado da chamada da função na variável temporária da direita

                encontra_chamada_func_inicial = acha_func_decl_aux(no.children[2].label) # Procura o chamado da função inicial

                chamada_func = builder.call(encontra_chamada_func_inicial, [builder.load(esq_temp), builder.load(dir_temp)]) # Chama a função inicial
                builder.store(chamada_func, recebe_chamada_func) # Armazena o resultado da chamada da função na variável que recebe o chamado da função
            else:
                acha_chamada_func = acha_func_decl_aux(no.children[2].label) # Procura o chamado da função
                operador_esq_declaracao = acha_var_aux(no.children[3].label) # Procura o operador esquerdo da declaração
                operador_dir_declaracao = acha_var_aux(no.children[4].label) # Procura o operador direito da declaração

                chamada_func = builder.call(acha_chamada_func, [builder.load(operador_esq_declaracao), builder.load(operador_dir_declaracao)]) # Chama a função
                builder.store(chamada_func, recebe_chamada_func) # Armazena o resultado da chamada da função na variável que recebe o chamado da função

        else:

            if len(no.children) == 3: # Verifica se o nó tem 3 filhos
                
                nome_var_recebendo = no.children[0].label # Pega o nome da variável que recebe a atribuição

                # representa o nome da variável y 
                nome_var_atribuida = no.children[2].label # Pega o nome da variável que recebe a atribuição
                
                # Procuro o tipo da variável atribuída
                tipo_var_atribuida = config['tab_sym'][config['tab_sym']['lex'] == nome_var_atribuida] # Procura o tipo da variável atribuída na tabela de simbolos
                
                if len(tipo_var_atribuida) > 0:
                    tipo_var_atribuida = tipo_var_atribuida['tipo'].values[0] # Pega o tipo da variável atribuída
                else:
                    # Verifico se é um valor 
                    if nome_var_atribuida.isdigit():
                        # Verifico se é inteiro ou flutuante 
                        tipo_var_atribuida = 'inteiro' # Atribuo o tipo da variável atribuída
                    
                    elif '.' in nome_var_atribuida:
                        # É flutuante
                        tipo_var_atribuida = 'flutuante' # Atribuo o tipo da variável atribuída


                var_declaracao_encontrada = '' # Variável que armazena a variável declarada
                # Primeiro procuro no escopo local e depois no global 
                if nome_var_recebendo+config['escopo'] in config['nome_scope_alocada']: # Verifica se a variável está no escopo local
                    # Pegar a posição onde se encontra esse valor e acessar as variaveis declaradas
                    var_declaracao_encontrada  = config['variaveis_declaradas'][config['nome_scope_alocada'].index(nome_var_recebendo+config['escopo'])] # Pega a variável declarada

                else:
                    if nome_var_recebendo+'global' in config['nome_scope_alocada']: # Verifica se a variável está no escopo global
                        var_declaracao_encontrada  = config['variaveis_declaradas'][config['nome_scope_alocada'].index(nome_var_recebendo+'global')] # Pega a variável declarada

                # Verifica se o valor que está sendo atribuído é uma variável
                valor_encontrado_atribuindo = acha_var_aux(nome_var_atribuida) # Procura o valor que está sendo atribuído na tabela de simbolos

                if valor_encontrado_atribuindo == '':
                    if tipo_var_atribuida == 'inteiro':
                        builder.store(ir.Constant(ir.IntType(32), nome_var_atribuida), var_declaracao_encontrada) # Armazena o valor na variável que recebe a atribuição
                    else:
                        builder.store(ir.Constant(ir.FloatType(), float(nome_var_atribuida)), var_declaracao_encontrada) # Armazena o valor na variável que recebe a atribuição
                else:
                    var_temporaria = builder.load(valor_encontrado_atribuindo, "") # Pega a variável temporária
                    builder.store(var_temporaria, var_declaracao_encontrada) # Armazena o valor na variável que recebe a atribuição
            else:
                if no.children[1].label == '[': # Verifica se o nó é um vetor
                    if len(no.children) == 6: 
                        nome_var_recebendo = acha_var_aux(no.children[0].label) # Procura a variável que recebe a atribuição

                        posicao_array = no.children[2].label # Pega a posição do array
                        posicao_arr_variavel = acha_var_aux(posicao_array) # Procura a posição do array na tabela de simbolos

                        posicao_var_temporaria = builder.alloca(ir.IntType(32), name='pos_temp_1') # Cria a variável temporária da posição
                        builder.store(builder.load(posicao_arr_variavel), posicao_var_temporaria) # Armazena a posição do array na variável temporária da posição

                        valor_recebendo = no.children[5].label # Pega o valor que está sendo atribuído
                        if valor_recebendo.isdigit(): # Verifica se o valor que está sendo atribuído é um dígito
                            tipo_inteiro = ir.IntType(32) # Cria o tipo inteiro
                            atribuicao_esq = builder.gep(nome_var_recebendo, [tipo_inteiro(0), tipo_inteiro(int(valor_recebendo))], name=str(no.children[0].label) + '_pos') # Cria a atribuição da esquerda

                            builder.store(atribuicao_esq, builder.load(valor_recebendo))  # Guarda o valor na variável que recebe a atribuição

                        else:
                            valor_recebendo_declaracao = acha_var_aux(valor_recebendo) # Procura o valor que está sendo atribuído na tabela de simbolos
                            tipo_inteiro = ir.IntType(32) # Cria o tipo inteiro
                            atribuicao_esq = builder.gep(nome_var_recebendo, [tipo_inteiro(0), builder.load(posicao_var_temporaria)], name=str(no.children[0].label) + '_pos')

                            builder.store(builder.load(valor_recebendo_declaracao), atribuicao_esq)    # Guarda o valor na variável que recebe a atribuição


                else:
                    nome_var_recebendo = acha_var_aux(no.children[0].label) # Procura a variável que recebe a atribuição

                    nome_var_atribuida_esq = no.children[2].label # Pega o nome da variável que recebe a atribuição
                    op_sinal = no.children[3].label # Pega o sinal da operação
                    nome_var_atribuida_dir = no.children[4].label # Pega o nome da variável que recebe a atribuição
                    
                    if (nome_var_atribuida_esq.isdigit()): 
                        nome_var_atribuida_esq_declarada = ir.Constant(ir.IntType(32), name=nome_var_atribuida_esq) # Cria a variável que recebe a atribuição

                    else:
                        nome_var_atribuida_esq_encontrada = acha_var_aux(nome_var_atribuida_esq) # Procura a variável que recebe a atribuição na tabela de simbolos
                        if nome_var_atribuida_esq_encontrada == '': # Verifica se a variável que recebe a atribuição foi encontrada
                            nome_var_atribuida_esq = ver_exp_par(nome_var_atribuida_esq) # Verifica a expressão da variável que recebe a atribuição

                            nome_var_atribuida_esq_encontrada = builder.alloca(ir.IntType(32), name='param') # Cria a variável que recebe a atribuição
                            builder.store(nome_var_atribuida_esq, nome_var_atribuida_esq_encontrada) # Armazena a variável que recebe a atribuição na variável que recebe a atribuição

                        nome_var_atribuida_esq_declarada = builder.load(nome_var_atribuida_esq_encontrada, name='_temp') # Pega a variável que recebe a atribuição
                    if (nome_var_atribuida_dir.isdigit()): # Verifica se a variável que recebe a atribuição é um dígito
                        nome_var_atribuida_dir_declarada = ir.Constant(ir.IntType(32), int(nome_var_atribuida_dir)) # Cria a variável que recebe a atribuição
                        

                    else:
                        nome_var_atribuida_dir_declarada_encontrada = acha_var_aux(nome_var_atribuida_dir) # Procura a variável que recebe a atribuição na tabela de simbolos
                        if nome_var_atribuida_dir_declarada_encontrada == '': # Verifica se a variável que recebe a atribuição foi encontrada
                            nome_var_atribuida_dir_declarada = ver_exp_par(nome_var_atribuida_dir) # Verifica a expressão da variável que recebe a atribuição
                            
                            nome_var_atribuida_dir_declarada_encontrada = builder.alloca(ir.IntType(32), name='param') # Cria a variável que recebe a atribuição
                            builder.store(nome_var_atribuida_dir_declarada_encontrada, nome_var_atribuida_dir_declarada_encontrada) # Armazena a variável que recebe a atribuição na variável que recebe a atribuição
                            nome_var_atribuida_dir_declarada_encontrada = builder.load(nome_var_atribuida_dir_declarada_encontrada) # Pega a variável que recebe a atribuição
                        
                        nome_var_atribuida_dir_declarada = builder.load(nome_var_atribuida_dir_declarada_encontrada, name='_temp') 
                        
                    # Chama função que vai declarar a operação
                    op_declarada = operacoes_aux(nome_var_atribuida_esq_declarada, nome_var_atribuida_dir_declarada, op_sinal) # Pega a operação declarada

                    builder.store(op_declarada, nome_var_recebendo) # Armazena a operação declarada na variável que recebe a atribuição


def decl_se_utils(linha,no):
    config['tem_se'] = True
    declaracao_func_encontrada = acha_func_decl_aux(config['escopo'])

    if_verdade_1 = declaracao_func_encontrada.append_basic_block('iftrue_1') # Cria o bloco de verdade
    if_falso_1 = declaracao_func_encontrada.append_basic_block('iffalse_1') # Cria o bloco de falsidade
    
    if_fim_1 = declaracao_func_encontrada.append_basic_block('ifend1') # Cria o bloco de saída
    config['pilha_bloco_fim'].append(if_fim_1)  # Adiciona o bloco de saída na pilha
    config['pilha_bloco_fim'].append(if_falso_1) # Adiciona o bloco de falsidade na pilha

    comp_var_esq = acha_var_aux(no.children[0].label) # Procura a variável da esquerda na tabela de simbolos
    comp_var_dir = ir.Constant(ir.IntType(32), int(no.children[2].label)) # Pega a variável da direita

    if len(no.children[1].children) > 0:
        print("test1")
        comp_operacao = builder.icmp_signed(str(no.children[1].children[0].label), builder.load(comp_var_esq), comp_var_dir) # Pega a operação da comparação
    else:
        print("test2")
        comp_operacao = builder.icmp_signed(str(no.children[1].label), builder.load(comp_var_esq), comp_var_dir) # Pega a operação da comparação
    builder.cbranch(comp_operacao, if_verdade_1, if_falso_1) # Cria o branch da comparação

    # builder.position_at_end(if_verdade_1) # Posiciona o bloco de verdade no topo


def decl_senao_utils(linha,no):
    bloco_falsidade = config['pilha_bloco_fim'].pop() # Pega o bloco de falsidade do topo da pilha
    topo_bloco_fim = config['pilha_bloco_fim'].pop() # Pega o bloco de saída do topo da pilha

    builder.branch(topo_bloco_fim) # Cria o branch do bloco de saída

    builder.position_at_end(bloco_falsidade) # Posiciona o bloco de falsidade no topo

    config['pilha_bloco_fim'].append(topo_bloco_fim) # Adiciona o bloco de saída na pilha


def decl_fim_se_utils(linha,no):
    bloco_topo = []
    if config['pilha_bloco_fim']: # Verifica se a pilha de blocos de saída não está vazia
        bloco_topo = config['pilha_bloco_fim'].pop() # Pega o bloco do topo da pilha
        saida_bloco_principal = config['pilha_bloco_fim'].pop() # Pega o bloco de saída do topo da pilha

        builder.branch(bloco_topo) # Cria o branch do bloco do topo
        print("bloco_topo",bloco_topo)
        builder.position_at_end(bloco_topo) # Posiciona o bloco do topo no topo
        builder.branch(saida_bloco_principal) # Cria o branch do bloco de saída principal

        config['pilha_bloco_fim'].append(saida_bloco_principal) # Adiciona o bloco de saída principal na pilha


def decl_repita_utils(linha,no):
    loop = builder.append_basic_block('loop') # Cria o loop
    loop_validacao = builder.append_basic_block('loop_val') # Cria o loop de validação
    loop_end = builder.append_basic_block('loop_end') # Cria o loop de saída

    config['pilha_loop_validacao'].append(loop_validacao) # Adiciona o loop de validação na pilha
    config['pilha_loop'].append(loop) # Adiciona o loop na pilha
    config['pilha_bloco_fim'].append(loop_end) # Adiciona o loop de saída na pilha
    print("loop",loop)
    builder.branch(loop) # Cria o branch do loop

    builder.position_at_end(loop)        # Posiciona o loop no topo

def decl_ate_utils(linha,no):
    _ = config['pilha_loop_validacao'].pop()
    saida = config['pilha_bloco_fim'].pop()
    loop_inicial = config['pilha_loop'].pop()

    comp_esq, comp_sinal, comp_dir = acha_comp_aux(no) # Pega a comparação

    if comp_dir.isdigit():
        comp_valor = ir.Constant(ir.IntType(32), int(comp_dir)) # Cria a comparação
    comp_variavel = acha_var_aux(comp_esq) # Procura a variável da comparação na tabela de simbolos
    if '=' == comp_sinal:
        expressao = builder.icmp_signed('==', builder.load(comp_variavel), comp_valor, name='exp_igualdade') # Pega a expressão da comparação
        print("expressao, loop_inicial, saida",expressao, loop_inicial, saida)
        builder.cbranch(expressao, loop_inicial, saida) # Cria o branch da comparação
 
    builder.position_at_end(saida) # Posiciona o bloco de saída no topo


def decl_escreva_utils(linha,no,w_int,w_float):
    valor_escrita = no.children[0].label # Pega o valor da escrita

    tipo_var_escrita = config['tab_sym'][config['tab_sym']['lex'] == str(valor_escrita)] # Procura o tipo da variável que está sendo escrita na tabela de simbolos
    tipo_var_escrita = tipo_var_escrita['tipo'].values[0] # Pega o tipo da variável que está sendo escrita

    if valor_escrita.isdigit():
        valor_escrita_constante = ir.Constant(ir.IntType(32), int(valor_escrita)) # Cria o valor da escrita
        builder.call(config['w_int'], args=[valor_escrita_constante]) # Chama a função de escrita
    else:
        var_escrever = acha_var_aux(valor_escrita)
        if tipo_var_escrita == 'inteiro':
            if w_int.function_type.return_type ==  ir.IntType(32):  # Verifica se o tipo da função de escrita é inteiro
                builder.call(w_int, args=[builder.load(var_escrever)]) # Chama a função de escrita
        else:
            builder.call(w_float, args=[builder.load(var_escrever)]) # Chama a função de escrita


def decl_leia_utils(linha,no):
    global r_int
    global r_float
    var_leia = no.children[0].label # Pega a variável que está sendo lida

    var_read = config['tab_sym'][config['tab_sym']['lex'] == var_leia] # Procura o tipo da variável que está sendo lida na tabela de simbolos
    var_read = var_read['tipo'].values[0] # Pega o tipo da variável que está sendo lida

    var_read_receive = acha_var_aux(var_leia) # Procura a variável que recebe a leitura na tabela de simbolos

    if var_read == 'inteiro':
        var_read_func = builder.call(r_int, args=[]) 
        builder.store(var_read_func, var_read_receive, align=4) # Armazena o valor lido na variável que recebe a leitura
    else:
        var_read_func = builder.call(r_float, args=[])
        builder.store(var_read_func, var_read_receive, align=4) 

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
                        var_declarada = builder.alloca(ir.IntType(32), name=variavel['lex'].values[0]) # Cria a variável declarada
                        var_declarada.initializer = ir.Constant(ir.IntType(32), 0) 
                    else:
                        var_declarada = builder.alloca(ir.FloatType(), name=str(variavel['lex'].values[0])) 
                        var_declarada_constante = ir.Constant(ir.FloatType(), 0.0) # Cria a variável declarada constante
                        builder.store(var_declarada_constante, var_declarada) 

                    var_declarada.linkage = "common"
                    var_declarada.align = 4

                    config['variaveis_declaradas'].append(var_declarada) # Adiciona a variável declarada na lista de variáveis declaradas
                    config['nome_scope_alocada'].append(variavel['lex'].values[0] + config['escopo']) # Adiciona o nome da variável declarada na lista de nomes do escopo alocada
                    
            elif 'declaracao_func' in no.label:
                decl_func_utils(linha,no)
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
    # config['modulo'] = modify_ir_code(str(config['modulo']))
    # print(config['modulo'])
    # config['modulo'] = binding.parse_assembly(config['modulo'])
    out_arq(config['modulo'])
    # main_process()