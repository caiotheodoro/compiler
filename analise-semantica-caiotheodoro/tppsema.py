from myerror import MyError
from anytree.exporter import UniqueDotExporter
from tppparser import retorna_arvore
import sys
import os
from utils import conv_tipo, aux_simbolos_tabela, encontra_tipo_nome_parametro, processa_atr_exp, processa_idx_ret, nodes, poda_arvore, tokens, processa_id, processa_numero,  expressoes
from sys import argv

import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="sema.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()
avisos = []
aux_dict = {}
error_handler = MyError('SemaErrors')
escopo = 'global'
root = None
tipo = ''
func_name = ''
tipo_retorno = ''
parametros = []
retorno = []
tipos = []
valor_atribuido = {}
valss = []
tipo_valor = []
dimensoes = 0
dims = [0, 0]


def processa_val_ret(retorna, retorno):  # processa o valor de retorno

    for ret in retorna.children:
        if (ret.label in expressoes):  # se for uma expressão
            retorno = processa_exp_ret(ret, retorno)  # processa a expressão
            return retorno

        # se não for uma expressão, continua processando
        processa_val_ret(ret, retorno)

    return retorno


def processa_exp_ret(retorna, lista_retorno):  # processa a expressão de retorno
    aux = {}

    for ret in retorna.children:
        if ret.label == 'numero':

            # se for um número, processa o número
            return processa_id(ret, aux, lista_retorno)

        elif ret.label == 'ID':

            # se for um ID, processa o ID
            return processa_id(ret, aux, lista_retorno)

        lista_retorno = processa_exp_ret(ret, lista_retorno)

    return lista_retorno


def insere_tabela(tab_sym, args):
    tab_sym.loc[len(tab_sym)] = args  # insere na tabela de simbolos


def encontra_atribuicao_valor(expressao, valores):
    v = {}

    for filhos in expressao.children:  # percorre os filhos da expressão
        if filhos.label == 'numero':
            processa_numero(filhos, v, valores)

        elif filhos.label == 'ID':
            processa_id(filhos, v, valores)

        tipo_retorno, indice = processa_idx_ret(filhos)  # processa o indice

    return tipo_retorno, valores


def processa_dim(tree, dimensao, indice_1, indice_2):  # processa a dimensão

    for filho in tree.children:

        if (filho.label == 'indice'):
            if (filho.children[0].label == 'indice'):  # se o filho for um indice
                dimensao = 2
                _, indice_1 = processa_idx_ret(
                    filho.children[0].children[1])
                _, indice_2 = processa_idx_ret(
                    filho.children[2])  # processa o indice
                return dimensao, indice_1, indice_2  # retorna a dimensão e os indices

            else:
                dimensao = 1
                _, indice_1 = processa_idx_ret(filho.children[1])
                indice_2 = 0
                return dimensao, indice_1, indice_2  # retorna a dimensão e os indices

        dimensao, indice_1, indice_2 = processa_dim(
            filho, dimensao, indice_1, indice_2)
    return dimensao, indice_1, indice_2


# processa a declaração da função
def processa_data_func(declaracao_funcao, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno):

    global escopo

    for filho in declaracao_funcao.children:
        if (filho.label == 'tipo'):
            tipo = filho.children[0].children[0].label  # pega o tipo

        elif (filho.label == 'lista_parametros'):
            if (filho.children[0].label == 'vazio'):    # se não tiver parametros
                parametros = 'vazio'
            else:
                pass

        elif (filho.label == 'cabecalho'):
            # pega o nome da função
            nome_funcao = filho.children[0].children[0].label
            escopo = nome_funcao

        elif ('retorna' in filho.label):

            retorno_tipo_valor = processa_val_ret(
                filho, [])  # processa o valor de retorno
            linha_retorno = filho.label.split(':')
            linha_retorno = linha_retorno[1]

            tipo_retorno = 'vazio'

            return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno

        tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno = processa_data_func(
            filho, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno)  # continua processando

    return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno


# encontra os parametros da função
def encontra_parametro_funcao(no, parametros):

    parametro = {}

    for n in no.children:
        if (no.label == 'parametro'):  # se o nó for um parametro
            # encontra o tipo e o nome do parametro
            tipo, nome = encontra_tipo_nome_parametro(no, '', '')

            parametro[nome] = tipo

            parametros.append(parametro)

            return parametros
        encontra_parametro_funcao(n, parametros)

    return parametros


# processa a declaração da função
def processa_declaracao_funcao(filho, tab_sym):
    global parametros
    global linha_declaracao

    linha_declaracao = ''
    parametros = encontra_parametro_funcao(
        filho, parametros)  # retorna parametros
    if len(filho.label.split(':')) > 1:
        linha_declaracao = filho.label.split(':')[1]  # retorna linha

    tipo, func_name, _, retorno, tipo_retorno, linha_retorno = processa_data_func(
        filho, '', '', '', '', '', '')  # retorna tipo, idx, parametros, retorno, tipo_retorno, linha_retorno

    # se tipo for vazio, retorna vazio, senão retorna tipo
    tipo = tipo if tipo != '' else 'vazio'

    insere_tabela(tab_sym, ['ID', func_name, tipo, 0, 0,
                  0, escopo, '0', linha_declaracao, '1', parametros, []])  # insere na tabela de simbolos

    for p in parametros:
        for nome_param, tipo_param in p.items():  # para cada parametro, insere na tabela de simbolos
            insere_tabela(tab_sym, [
                          'ID', nome_param, tipo_param, 0, 0, 0, escopo, '1', linha_declaracao, '0', [], []])  # insere na tabela de simbolos

    if retorno and retorno != []:  # se houver retorno, insere na tabela de simbolos
        tipo_ret_dict = []  # lista de retorno
        for ret in retorno:  # para cada retorno, insere na tabela de simbolos
            for nome_retorno, tipo_retorno in ret.items():  # para cada retorno, insere na tabela de simbolos
                tipo_retorno = tab_sym.loc[tab_sym['lex']
                                           == nome_retorno]['tipo'].values  # encontra o tipo do retorno
                tipo_variaveis_retorno = tipo_retorno[0] if len(
                    tipo_retorno) > 0 else 'vazio'  # se não tiver tipo, retorna vazio

                # cria um dicionario com o idx e o tipo do retorno
                tipo_ret = {nome_retorno: tipo_variaveis_retorno}
                # adiciona na lista de retorno
                tipo_ret_dict.append(tipo_ret)

                # adiciona na lista de tipos
                tipos.append(tipo_variaveis_retorno)

        # se tiver flutuante, retorna flutuante, senão retorna inteiro
        tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        insere_tabela(tab_sym, ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                                '0', linha_retorno, '1', [], tipo_ret_dict])  # insere na tabela de simbolos


def encontra_parametros(no_parametro, parametros):  # encontra os parametros
    parametro = {}
    tipo = ''
    nome = ''

    for no in no_parametro.children:  # para cada nó filho
        if (no.label == 'expressao'):
            # processa o tipo e o nome do parametro
            tipo, nome = processa_idx_ret(no)
            parametro[nome] = tipo
            parametros.append(parametro)  # adiciona na lista de parametros

            return parametros

        encontra_parametros(no, parametros)
    return parametros


def processa_declaracao(filho, tab_sym):  # processa a declaração
    tipo = ''
    nome_funcao = ''
    tipo_retorno = ''
    parametros = []
    retorno = []
    tipos = []

    parametros = encontra_parametro_funcao(
        filho, parametros)  # encontra os parametros

    linha_declaracao = filho.label.split(':')
    linha_declaracao = linha_declaracao[1]

    tipo, nome_funcao, _, retorno, tipo_retorno, linha_retorno = processa_data_func(
        filho, '', '', '', '', '', '')  # processa o tipo, o nome, os parametros, o retorno, o tipo de retorno e a linha de retorno

    if tipo == '':
        tipo = 'vazio'

    insere_tabela(tab_sym, ['ID', nome_funcao, tipo, 0, 0, 0,
                            escopo, '0', linha_declaracao, '1', parametros, []])  # insere na tabela de simbolos

    for p in parametros:
        for nome_param, tipo_param in p.items():

            insere_tabela(tab_sym, ['ID', nome_param, tipo_param, 0,
                                    0, 0, escopo, '1', linha_declaracao, '0', [], []])  # insere na tabela de simbolos

    if (retorno != ''):  # se houver retorno
        pos = 0
        muda_tipo_retorno_lista = []
        for ret in retorno:
            for nome_retorno, tipo_retorno in ret.items():  # para cada retorno, insere na tabela de simbolos

                tipo_retorno = tab_sym.loc[tab_sym['lex']
                                           == nome_retorno]

                tipo_variaveis_retorno = tipo_retorno['tipo'].values
                if len(tipo_variaveis_retorno) > 0:
                    # se não tiver tipo, retorna vazio
                    tipo_variaveis_retorno = tipo_variaveis_retorno[0]
                else:
                    tipo_variaveis_retorno = 'vazio'

                muda_tipo_retorno = {}
                muda_tipo_retorno[nome_retorno] = tipo_variaveis_retorno
                muda_tipo_retorno_lista.append(muda_tipo_retorno)

                tipos.append(tipo_variaveis_retorno)
                pos += 1

        if len(tipos) > 0:
            if ('flutuante' in tipos):
                tipo = 'flutuante'
            else:
                tipo = 'inteiro'

        insere_tabela(tab_sym, ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                                '0', linha_retorno, '1', [], muda_tipo_retorno_lista])


def insert_entry(tab_sym, *entry):
    tab_sym.loc[len(tab_sym)] = entry


# processa a declaração de função
def process_function_declaration(tab_sym, filho, escopo):
    linha_declaracao = filho.label.split(':')[1]
    tipo, nome_funcao, _, retorno, tipo_retorno, linha_retorno = processa_data_func(
        filho, '', '', '', '', '', '')

    tipo = tipo if tipo else 'vazio'
    insert_entry(tab_sym, 'ID', nome_funcao, tipo, 0, 0, 0,
                 escopo, '0', linha_declaracao, '1', [], [])

    parametros = encontra_parametro_funcao(filho, [])
    for p in parametros:
        for nome_param, tipo_param in p.items():  # para cada parametro, insere na tabela de simbolos
            insert_entry(tab_sym, 'ID', nome_param, tipo_param, 0,
                         0, 0, escopo, '1', linha_declaracao, '0', [], [])  # insere na tabela de simbolos

    if retorno:
        muda_tipo_retorno_lista = []  # cria uma lista com os tipos de retorno
        for ret in retorno:
            for nome_retorno, _ in ret.items():
                tipo_retorno = tab_sym.loc[tab_sym['lex']
                                           == nome_retorno]['tipo'].values  # se não tiver tipo, retorna vazio
                tipo_variaveis_retorno = tipo_retorno[0] if len(
                    tipo_retorno) > 0 else 'vazio'
                muda_tipo_retorno = {
                    nome_retorno: tipo_variaveis_retorno}  # insere na lista
                muda_tipo_retorno_lista.append(muda_tipo_retorno)

        tipo = 'flutuante' if 'flutuante' in [
            x.values() for x in muda_tipo_retorno_lista] else 'inteiro'
        insert_entry(tab_sym, 'ID', 'retorna', tipo, 0, 0, 0, escopo,
                     '0', linha_retorno, '1', [], muda_tipo_retorno_lista)


def processa_decl_func(tab_sym, filho):
    tipo, nome_funcao, tipo_retorno, parametros, retorno, tipos = '', '', '', [], [], []

    parametros = encontra_parametro_funcao(filho, parametros)

    linha_declaracao = filho.label.split(':')[1]  # pega a linha da declaração

    tipo, nome_funcao, _, retorno, tipo_retorno, linha_retorno = processa_data_func(
        filho, '', '', '', '', '', '')

    if tipo == '':
        tipo = 'vazio'

    insere_tabela(tab_sym, ['ID', nome_funcao, tipo, 0, 0,
                  0, escopo, '0', linha_declaracao, '1', parametros, []])

    for p in parametros:
        for nome_param, tipo_param in p.items():
            insere_tabela(tab_sym, ['ID', nome_param, tipo_param,
                          0, 0, 0, escopo, '1', linha_declaracao, '0', [], []])

    if retorno:
        pos = 0
        muda_tipo_retorno_lista = []

        for ret in retorno:
            for nome_retorno, tipo_retorno in ret.items():
                tipo_retorno = tab_sym.loc[tab_sym['lex']  # se não tiver tipo, retorna vazio
                                           == nome_retorno]['tipo'].values

                tipo_variaveis_retorno = tipo_retorno[0] if len(
                    tipo_retorno) > 0 else 'vazio'

                muda_tipo_retorno = {
                    nome_retorno: tipo_variaveis_retorno}  # insere na lista
                muda_tipo_retorno_lista.append(
                    muda_tipo_retorno)  # insere na lista

                tipos.append(tipo_variaveis_retorno)
                pos += 1

        if tipos:
            tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        insere_tabela(tab_sym, ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                      '0', linha_retorno, '1', [], muda_tipo_retorno_lista])


def processa_ret(tab_sym):
    tipos = []
    linha_retorno = tab_sym.loc[(tab_sym['lex'] == 'retorna') & (
        tab_sym['escopo'] == escopo)]
    linha_retorno_index = linha_retorno.index[0]

    retorno_linha = linha_retorno['valor'].values.tolist()
    retorno = retorno_linha[0]

    if not linha_retorno.empty:
        muda_tipo_retorno_lista = []
        global variavel_nao_declarada

        for ret in retorno:
            for nome_retorno, tipo_retorno in ret.items():  # se não tiver tipo, retorna vazio
                tipo_retorno = tab_sym.loc[(tab_sym['lex'] == nome_retorno) & (
                    tab_sym['escopo'] == escopo)]['tipo'].values

                # se não tiver tipo, retorna vazio
                tipo_variaveis_retorno = tipo_retorno[0] if tipo_retorno else 'vazio'

                if not tipo_retorno and nome_retorno not in variavel_nao_declarada:  # se não tiver tipo, retorna vazio
                    print(error_handler.newError(
                        'WAR-SEM-VAR-DECL-NOT-USED', value=nome_retorno))
                    variavel_nao_declarada.append(nome_retorno)

                muda_tipo_retorno = {
                    nome_retorno: tipo_variaveis_retorno}  # insere na lista
                muda_tipo_retorno_lista.append(muda_tipo_retorno)

                tipos.append(tipo_variaveis_retorno)

        if tipos:
            tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        tab_sym.at[linha_retorno_index, 'valor'] = muda_tipo_retorno_lista
        tab_sym.at[linha_retorno_index, 'tipo'] = tipo


def processa_chamada_func(tab_sym, filho):
    nome_funcao = ''
    parametros = []

    nome_funcao = filho.children[0].children[0].label  # pega o nome da função
    parametros = encontra_parametros(filho, parametros)

    linha_declaracao = filho.label.split(':')[1]

    # se não tiver tipo, retorna vazio
    declaracao_funcao = tab_sym.loc[tab_sym['lex'] == nome_funcao]

    tipo_funcao = declaracao_funcao['tipo'].values[0] if len(
        declaracao_funcao) > 0 else 'vazio'

    parametro_list = []

    if len(parametros) >= 1:
        for param in parametros:
            for nome_param, tipo_param in param.items():
                parametro_dic = {}
                parametro_dic[nome_param] = tipo_param
                parametro_list.append(parametro_dic)

    insere_tabela(tab_sym, ['ID', filho.children[0].children[0].label, tipo_funcao,
                  0, 0, 0, escopo, '0', linha_declaracao, 'chamada_funcao', parametro_list, []])  # insere na tabela


def tab_sym_aux(tree, tab_sym):
    dims = [0, '', '']

    for filho in tree.children:
        if ('declaracao_variaveis' in filho.label):
            dims = processa_dim(
                filho, 0, 0, 0)

            linha_declaracao = filho.label.split(':')
            insere_tabela(tab_sym, ['ID', str(filho.children[2].children[0].children[0].children[0].label), str(
                filho.children[0].children[0].children[0].label), *dims, escopo, '0', linha_declaracao[1], '0', [], []])  # insere na tabela
            return tab_sym

        elif ('declaracao_funcao' in filho.label):
            processa_decl_func(tab_sym, filho)

        elif ('retorna' in filho.label):
            processa_ret(tab_sym)

        elif ('chamada_funcao' in filho.label):
            processa_chamada_func(tab_sym, filho)
        elif ('atribuicao' in filho.label):
            valor_atribuido = {}
            valores = []
            tipo_valor = []
            dimensoes = 0
            tam_dimensao_1 = 0
            tam_dimensao_2 = 0

            tipo_valor = processa_atr_exp(filho.children[2], [])

            # pega o nome da variável
            variavel_atribuicao_nome = filho.children[0].children[0].children[0].label

            linha_declaracao = filho.label.split(':')
            linha_declaracao = linha_declaracao[1]

            for i in tipo_valor:
                for valor, tipo in i.items():

                    if tipo == 'parametro':

                        variavel_declarada = tab_sym.loc[(
                            tab_sym['lex'] == valor) & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                        if len(variavel_declarada) > 0:
                            tipo = variavel_declarada['tipo'].values
                            tipo = tipo[0]
                        elif len(variavel_declarada) == 0:
                            print(error_handler.newError(
                                'ERR-VAR-NOT-DECL', value=valor))

                    tipo = conv_tipo.get(tipo)

                    valor_atribuido[valor] = tipo
                    valores.append(valor_atribuido)

                    tipo_variavel_recebendo = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                        tab_sym['iniciacao'] == '0') & (tab_sym['escopo'] == escopo)]  # se não tiver tipo, retorna vazio

                    if tipo == 'ID':
                        tipo_variavel_recebendo_global = tipo_variavel_recebendo

                        tipo_variavel_recebendo = tipo_variavel_recebendo['tipo'].values

                    if len(tipo_variavel_recebendo) > 0:
                        if len(tipo_variavel_recebendo) == 1:
                            tipo_variavel_recebendo = tipo_variavel_recebendo

                        else:
                            tipo_variavel_recebendo = tipo_variavel_recebendo[0]

                    if len(tipo_variavel_recebendo) == 0 and (tipo != 'inteiro' and tipo != 'flutuante'):
                        tipo_variavel_recebendo_global = tab_sym.loc[(
                            tab_sym['lex'] == variavel_atribuicao_nome) & (tab_sym['iniciacao'] == '0')]

                        if len(tipo_variavel_recebendo_global) > 0:
                            tipo_variavel_recebendo_global = tipo_variavel_recebendo_global[
                                'tipo'].values
                            tipo_variavel_recebendo_global = tipo_variavel_recebendo_global[0]

                            tipo_variavel_recebendo = tipo_variavel_recebendo_global

                    else:
                        tipo_variavel_valor = tipo
                        tipo_variavel_recebendo = tipo_variavel_valor

                    dimensoes = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                        tab_sym['iniciacao'] == '0')]
                    tam_dimensao_1 = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                        tab_sym['iniciacao'] == '0')]
                    tam_dimensao_2 = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                        tab_sym['iniciacao'] == '0')]

                    dimensoes = dimensoes['dimensao'].values

                    if len(dimensoes) > 0:
                        dimensoes = dimensoes[0]
                    else:
                        dimensoes = 0

                    tam_dimensao_1 = tam_dimensao_1['tamanho dimensional 1'].values

                    if len(tam_dimensao_1) > 0:
                        tam_dimensao_1 = tam_dimensao_1[0]

                    # pega o tamanho da dimensão 2
                    tam_dimensao_2 = tam_dimensao_2['tamanho dimensional 2'].values

                    if len(tam_dimensao_2) > 0:
                        tam_dimensao_2 = tam_dimensao_2[0]

                    if int(dimensoes) > 0:
                        dimensoes, tam_dimensao_1, tam_dimensao_2 = processa_dim(
                            filho, 0, 0, 0)

                    insere_tabela(tab_sym, ['ID', variavel_atribuicao_nome, tipo_variavel_recebendo, dimensoes,
                                            tam_dimensao_1, tam_dimensao_2, escopo, '1', linha_declaracao, '0', [], valores])

        tab_sym_aux(filho, tab_sym)

    return tab_sym


def processa_attr_tipo(variavel_atual, tipo_variavel, escopo_variavel, inicializacao_variaveis, variaveis, funcoes, tab_sym):
    status = True
    tipo_atribuicao = ''
    nome_inicializacao = ''
    tipo_variavel_inicializacao_retorno = ''
    tipo_variavel_novo = ''

    nome_variavel = variavel_atual['lex']

    for ini_variaveis in inicializacao_variaveis:  # pega o tipo da variável
        for ini_var in ini_variaveis:  # pega o tipo da variável
            for nome_variavel_inicializacao, tipo_variavel_inicializacao in ini_var.items():  # pega o nome da variável e o tipo
                status = True
                nome_inicializacao = nome_variavel_inicializacao

                declaracao_variavel = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                    tab_sym['escopo'] == escopo_variavel) & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                if len(declaracao_variavel) == 0:
                    declaracao_variavel_global = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                        tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                    if len(declaracao_variavel_global) > 0:
                        tipo_variavel_novo = declaracao_variavel_global['tipo'].values[0]
                else:
                    tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                if nome_variavel_inicializacao in funcoes:
                    tipo_atribuicao = tab_sym.loc[tab_sym['lex'] ==
                                                  nome_variavel_inicializacao]['tipo'].values
                    tipo_atribuicao = tipo_atribuicao[0] if len(
                        tipo_atribuicao) > 0 else ''

                    if tipo_variavel_novo == tipo_atribuicao:
                        status = True
                    else:
                        status = False

                    if status == False:
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=[
                              nome_variavel, tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao]))  # erro de atribuição de tipo incompatível

                    return status, tipo_variavel_inicializacao, tipo_variavel_novo, nome_inicializacao

                elif nome_variavel_inicializacao in variaveis['lex'].values:
                    tipo_atribuicao = tab_sym.loc[(tab_sym['lex'] == nome_variavel_inicializacao) & (
                        tab_sym['escopo'] == escopo_variavel) & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                    if len(tipo_atribuicao) == 0:
                        tipo_atribuicao = tab_sym.loc[(tab_sym['lex'] == nome_variavel_inicializacao) & (
                            tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                    tipo_atribuicao = tipo_atribuicao['tipo'].values[0] if len(
                        tipo_atribuicao) > 0 else ''

                    if tipo_variavel_novo and tipo_atribuicao:
                        if tipo_variavel_novo == tipo_atribuicao:
                            status = True
                        else:
                            status = False

                    if status == False:
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=[
                              nome_variavel, tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao]))  # erro de atribuição de tipo incompatível

                elif tipo_variavel_inicializacao == 'inteiro' or tipo_variavel_inicializacao == 'flutuante':
                    declaracao_variavel_valor = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                        tab_sym['escopo'] == escopo_variavel) & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                    if len(declaracao_variavel_valor) == 0:
                        declaracao_variavel_global_valor = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                            tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]  # se não tiver tipo, retorna vazio

                        if len(declaracao_variavel_global_valor) > 0:
                            tipo_variavel_novo = declaracao_variavel_global_valor['tipo'].values[0]
                    else:
                        tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                    if '.' in str(nome_variavel_inicializacao):
                        tipo_variavel = 'flutuante'

                    if tipo_variavel_inicializacao == 'flutuante':  # se for flutuante, o tipo da variável é flutuante
                        if tipo_variavel == 'flutuante':
                            status = True
                            tipo_variavel_novo = 'flutuante'
                        else:
                            status = False
                            tipo_variavel_novo = 'inteiro'
                    else:
                        if tipo_variavel_novo == 'inteiro':
                            status = True
                            tipo_variavel_novo = 'inteiro'
                        else:
                            status = False
                            tipo_variavel_novo = 'flutuante'

                    if status == False:
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=(nome_variavel,
                              tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao)))  # erro de atribuição de tipo incompatível

                tipo_variavel_inicializacao_retorno = tipo_variavel_inicializacao

    return status, tipo_variavel_inicializacao_retorno, tipo_variavel_novo, nome_inicializacao


def verifica_regras_semanticas(tab_sym):
    variaveis = tab_sym.loc[tab_sym['funcao'] == '0']

    funcoes = tab_sym.loc[tab_sym['funcao'] != '0']
    funcoes = funcoes['lex'].unique()

    i = 0

    variaveis_repetidas_valores_inicio = variaveis['lex'].unique()
    var_verificacao = variaveis
    for var in variaveis_repetidas_valores_inicio:

        linhas = tab_sym[tab_sym['lex'] ==
                         var].index.tolist()  # pega as linhas
        linha = tab_sym[tab_sym['lex'] == var]

        if len(linhas) > 1:
            linhas = linha[linha['iniciacao'] ==
                           '0'].index.tolist()  # pega as linhas
            if len(linhas) > 1:
                var_verificacao.drop(linhas[0])

    for _, row in variaveis.iterrows():
        lista_declaracao_variavel = tab_sym.loc[(tab_sym['lex'] == row['lex']) & (
            tab_sym['iniciacao'] == '0') & (tab_sym['escopo'] == row['escopo'])]

        if len(lista_declaracao_variavel) > 1:
            print(error_handler.newError(
                'WAR-ALR-DECL', value=row['lex']))

    escopo_variaveis_verificacao = var_verificacao['escopo'].unique()
    for e in escopo_variaveis_verificacao:
        for var in variaveis_repetidas_valores_inicio:
            mesmo_escopo = var_verificacao[(var_verificacao['escopo'] == e) & (
                var_verificacao['lex'] == var)]

            if len(mesmo_escopo) > 1:
                linha_mesmo_escopo = mesmo_escopo.index.tolist()  # pega as linhas
                var_verificacao.drop(linha_mesmo_escopo[0])

    for linha in var_verificacao.index:
        inicializacao_variaveis = tab_sym.loc[(tab_sym['lex'] == variaveis['lex'][linha]) & (
            tab_sym['escopo'] == variaveis['escopo'][linha]) & (tab_sym['iniciacao'] == '1')]  # pega as linhas
        inicializacao_variaveis = inicializacao_variaveis['valor'].values

        inicializacao_variaveis_valores = []
        if len(inicializacao_variaveis) > 0:
            inicializacao_variaveis_valores = inicializacao_variaveis

        if len(inicializacao_variaveis_valores) > 0:
            _, _, _, _ = processa_attr_tipo(
                variaveis.iloc[i], variaveis['tipo'][linha], variaveis['escopo'][linha], inicializacao_variaveis_valores, variaveis, funcoes, tab_sym)  # verifica se o tipo da variável é compatível com o tipo da inicialização

        i += 1

    variaveis_repetidas_valores = variaveis['lex'].unique()

    for var_rep in variaveis_repetidas_valores:
        variaveis_repetidas = variaveis.loc[variaveis['lex'] == var_rep]

        if len(variaveis_repetidas) > 1:
            variaveis_repetidas_linhas = variaveis_repetidas[variaveis_repetidas['iniciacao'] == '0']
            escopos_variaveis = variaveis_repetidas_linhas['escopo'].unique()

            for esc in escopos_variaveis:
                variaveis_repetidas_escopo_igual_index = variaveis_repetidas_linhas.loc[
                    variaveis_repetidas_linhas['escopo'] == esc].index
                # remove as variáveis repetidas
                variaveis.drop(variaveis_repetidas_escopo_igual_index[0])

        elif len(variaveis_repetidas) == 0:
            print(error_handler.newError('ERR-VAR-NOT-DECL', value=var_rep))

    repetidos_variaveis_atribuicao = variaveis['lex'].unique()
    for rep in repetidos_variaveis_atribuicao:
        _ = variaveis.loc[variaveis['lex'] == rep]
        tabela_variaveis_repetida_index = variaveis.loc[variaveis['lex'] == rep].index

        if len(tabela_variaveis_repetida_index) > 1:
            variaveis.drop(tabela_variaveis_repetida_index[0])

    if ('principal' not in funcoes):
        print(error_handler.newError('ERR-FUNC-NOT-DECL'))

    for _, row in variaveis.iterrows():
        dimensao_variavel = row['dimensao']

        if int(dimensao_variavel) > 0:
            # verifica se o tamanho da dimensão é inteiro
            if int(dimensao_variavel) == 1 and '.' in str(row['tamanho dimensional 1']):
                print(error_handler.newError(
                    'ERR-IND-ARRAY', value=row['lex']))
            # verifica se o tamanho da dimensão é inteiro
            elif int(dimensao_variavel) == 2 and '.' in str(row['tamanho dimensional 2']):
                print(error_handler.newError(
                    'ERR-IND-ARRAY', value=row['lex']))

        inicializada = False

        df = tab_sym.loc[tab_sym['lex'] == row['lex']]

        if (len(df) > 1):
            for lin in range(len(df)):
                if (df.iloc[lin]['iniciacao'] != '0'):
                    inicializada = True
        else:
            if (tab_sym.iloc[0]['iniciacao'] != '0'):
                inicializada = True

        retorna_parametros = tab_sym.loc[(tab_sym['lex'] == 'retorna') & (
            tab_sym['escopo'] == row['escopo'])]
        retorna_parametros = retorna_parametros['valor']
        retorna_parametros = retorna_parametros.values

        if len(retorna_parametros) > 0:
            for retornos_variaveis in retorna_parametros:
                for rt_vs in retornos_variaveis:
                    # verifica se a variável de retorno foi inicializada
                    for nome_variavel_retorno, tipo_variavel_retorno in rt_vs.items():

                        if (row['lex'] == nome_variavel_retorno):
                            inicializada = True

        if (inicializada == False):
            print(error_handler.newError(
                'WAR-SEM-VAR-DECL-NOT-USED', value=row['lex']))

    for func in funcoes:
        if func == 'principal':
            tabela_retorno = tab_sym.loc[tab_sym['lex'] == 'retorno']

            if (tabela_retorno.shape[0] == 0):
                print(error_handler.newError(
                    'ERR-RET-TIP-INCOMP', value=['inteiro']))

            chamada_funcao_principal = tab_sym.loc[(
                tab_sym['funcao'] == 'chamada_funcao') & (tab_sym['lex'] == 'principal')]

            if len(chamada_funcao_principal) > 0:
                verifica_escopo = chamada_funcao_principal['escopo'].values[0]

                if verifica_escopo == 'principal':
                    print(error_handler.newError(
                        'WAR-REC-PRIN'))
                else:
                    print(error_handler.newError(
                        'ERR-REC-PRIN'))
        else:
            chamada_funcao = tab_sym.loc[(tab_sym['lex'] == func) & (
                tab_sym['funcao'] == 'chamada_funcao')]
            declaracao_funcao = tab_sym.loc[(
                tab_sym['lex'] == func) & (tab_sym['funcao'] == '1')]

        if func == 'retorna':
            escopo_retorno = declaracao_funcao['escopo'].values[0]
            variavel_retornada = declaracao_funcao['valor'].values[0]

            for var in variavel_retornada:  # verifica se a variável de retorno foi declarada
                for n, t in var.items():
                    variavel_retornada = n

            tipo_retorno_funcao = declaracao_funcao['tipo'].values[0]

            # verifica se a variável de retorno foi declarada
            if variavel_retornada in tab_sym['lex'].unique():
                declaracao_variavel = tab_sym.loc[(tab_sym['lex'] == variavel_retornada) & (
                    tab_sym['escopo'] == escopo_retorno) & (tab_sym['iniciacao'] == '0')]

                if len(declaracao_variavel) == 0:
                    declaracao_variavel_global = tab_sym.loc[(tab_sym['lex'] == variavel_retornada) & (
                        tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]

                    if len(declaracao_variavel_global) == 0:
                        declaracao_variavel_global = tab_sym.loc[(tab_sym['lex'] == variavel_retornada) & (
                            tab_sym['escopo'] == escopo_retorno) & (tab_sym['iniciacao'] == '1')]

                    tipo_retorno_funcao = declaracao_variavel_global['tipo'].values[0]

            procura_funcao_escopo = tab_sym.loc[(tab_sym['funcao'] == '1') & (
                tab_sym['escopo'] == escopo_retorno) & (tab_sym['lex'] != 'retorna')]  # verifica se a função foi declarada

            nome_funcao = procura_funcao_escopo['lex'].values[0]
            tipo_funcao = procura_funcao_escopo['tipo'].values[0]

            if tipo_funcao != tipo_retorno_funcao:
                print(error_handler.newError('ERR-FUNC-TYPE-RETURN',
                      value=(nome_funcao, tipo_funcao, tipo_retorno_funcao)))  # verifica se o tipo de retorno da função é compatível com o tipo da variável de retorno

            if len(chamada_funcao) > 0:
                if len(declaracao_funcao) < 1:
                    print(error_handler.newError('ERR-CHAMA-FUNC', value=func))
                else:
                    quantidade_parametros_chamada = chamada_funcao['parametros'].values[0]
                    quantidade_parametros_declaracao_funcao = declaracao_funcao[
                        'parametros'].values[0]  # verifica se a quantidade de parâmetros da chamada da função é compatível com a quantidade de parâmetros da declaração da função

                    if len(quantidade_parametros_chamada) != len(quantidade_parametros_declaracao_funcao):
                        print(error_handler.newError('ERR-PARAM-FUNC-INCOMP-' + ('MENOS' if len(quantidade_parametros_chamada)
                              < len(quantidade_parametros_declaracao_funcao) else 'MAIS'), value=func))  # verifica se a quantidade de parâmetros da chamada da função é compatível com a quantidade de parâmetros da declaração da função
            else:
                if len(declaracao_funcao) > 0 and func != 'retorna':
                    print(error_handler.newError(
                        'WAR-NOT-USED-FUNC', value=func))


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
        root = retorna_arvore(source_file)  # retorna a arvore do parser

        if root:
            tab_sym = aux_simbolos_tabela()  # cria a tabela de simbolos
            tab_sym = tab_sym_aux(
                root, tab_sym)  # monta a tabela de simbolos

            # verifica as regras semanticas
            verifica_regras_semanticas(tab_sym)

            # salva a tabela de simbolos em um arquivo csv
            tab_sym.to_csv(f'{argv[1]}.csv', index=None, header=True)
            poda_arvore(root, tokens, nodes)  # poda a arvore
            UniqueDotExporter(root).to_picture(
                f'{sys.argv[1]}.podada.unique.ast.png')
