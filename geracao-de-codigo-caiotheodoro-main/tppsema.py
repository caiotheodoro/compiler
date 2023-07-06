
from myerror import MyError
from anytree.exporter import UniqueDotExporter
from tppparser import retorna_arvore
import sys
import os
from utils import encontra_tipo_nome_parametro,  processa_retorno, processa_idx_ret, aux_tipo, aux_simbolos_tabela, nodes, poda_arvore, tokens, processa_numero, processa_id
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


def atribuicao_expressao(expressao, valss):
    valss = valss
    aux_dict = {}
    valss = []
    for filho in expressao.children:
        if filho.label == 'numero':
            # verifica se o no é um numero
            valss = processa_numero(filho, aux_dict, valss)
        elif filho.label == 'ID':
            # verifica se o no é um ID
            valss = processa_id(filho, aux_dict, valss)

        # processa a expressao recursivamente
        valss = atribuicao_expressao(filho, valss)

    return valss


def insere_tabela(tab_sym, args):
    tab_sym.loc[len(tab_sym)] = args  # insere na tabela de simbolos


# verifica se as dimensoes sao iguais
def verifica_dimensoes(tree, dimensao, indice_1, indice_2):
    for filho in tree.children:  # percorre os filhos
        if filho.label == 'indice':
            # se o filho for um indice (matriz)
            if filho.children[0].label == 'indice':
                dimensao = 2
                _, indice_1 = processa_idx_ret(filho.children[0].children[1])
                _, indice_2 = processa_idx_ret(filho.children[2])
            else:  # se o filho for um numero (vetor)
                dimensao = 1
                _, indice_1 = processa_idx_ret(filho.children[1])
                indice_2 = 0
        dimensao, indice_1, indice_2 = verifica_dimensoes(
            filho, dimensao, indice_1, indice_2)
    return dimensao, indice_1, indice_2


def processa_retorno(filho, resultado):
    if filho.label == 'inteiro' or filho.label == 'flutuante':  # se o filho for um numero
        resultado.append(filho.children[0].label)
    else:  # se o filho for um ID
        for child in filho.children:
            # processa o retorno recursivamente
            processa_retorno(child, resultado)
    return resultado


def encontra_dados_funcao(no, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno):

    global escopo

    for filho in no.children:  # percorre os filhos
        if filho.label == 'tipo':
            tipo = filho.children[0].children[0].label  # retorna o tipo

        elif filho.label == 'lista_parametros':  # se o filho for uma lista de parametros
            if filho.children[0].label == 'vazio':
                parametros = 'vazio'
            else:
                parametros = None

        elif filho.label == 'cabecalho':  # se o filho for um cabecalho
            # retorna o nome da funcao
            nome_funcao = filho.children[0].children[0].label
            escopo = nome_funcao  # escopo recebe o nome da funcao

        # se o filho for um retorno
        elif 'retorna' in filho.label and len(filho.label.split(':')) > 1:
            retorno_tipo_valor = processa_retorno(
                filho, [])  # retorna o tipo do retorno
            linha_retorno = filho.label.split(':')[1]
            tipo_retorno = 'vazio'

        encontra_dados_funcao(filho, tipo, nome_funcao, parametros,
                              retorno_tipo_valor, tipo_retorno, linha_retorno)  # processa recursivamente

    return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno


def encontra_parametro_funcao(no, parametros):

    params = {}

    for n in no.children:
        if (no.label == 'parametro'):
            tipo, nome = encontra_tipo_nome_parametro(
                no, '', '')  # retorna o tipo e o nome do parametro

            params[nome] = tipo  # insere na tabela de simbolos

            parametros.append(params)

            return parametros
        encontra_parametro_funcao(n, parametros)

    return parametros


def encontra_parametros(no_parametro, parametros):
    params = {}
    tipo = ''
    nome = ''

    for no in no_parametro.children:
        if (no.label == 'expressao'):  # se o no for uma expressao
            # retorna o tipo e o nome do parametro
            tipo, nome = processa_idx_ret(no)
            params[nome] = tipo
            parametros.append(params)

            return parametros

        encontra_parametros(no, parametros)
    return parametros


def processa_declaracao_funcao(filho, tab_sym):
    global parametros
    global linha_declaracao

    linha_declaracao = ''
    parametros = encontra_parametro_funcao(
        filho, parametros)  # retorna parametros
    if len(filho.label.split(':')) > 1:
        linha_declaracao = filho.label.split(':')[1]  # retorna linha

    tipo, func_name, _, retorno, tipo_retorno, linha_retorno = encontra_dados_funcao(
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


def retorna_funcao(tab_sym):
    tipos = []

    linha_retorno = tab_sym.loc[(tab_sym['lex'] == 'retorna') & (
        tab_sym['escopo'] == escopo)]  # se não tiver retorna, retorna vazio

    if not linha_retorno.empty:  # se tiver retorna
        ret_linha_i = linha_retorno.index[0]  # pega o index da linha
    # pega o valor da linha
    retorno_linha = linha_retorno['valor'].values.tolist()
    if retorno_linha:  # se tiver valor na linha
        retorno = retorno_linha[0]  # pega o valor da linha

    if len(linha_retorno) > 0:  # se tiver linha de retorno
        tipo_ret_dict = []
        global variavel_nao_declarada

        for ret in retorno:  # para cada retorno
            for nome_retorno, tipo_retorno in ret.items():  # para cada idx e tipo do retorno
                tipo_retorno = tab_sym.loc[(tab_sym['lex'] == nome_retorno) & (
                    tab_sym['escopo'] == escopo)]  # pega o tipo do retorno

                # pega o valor do tipo do retorno
                tipo_variaveis_retorno = tipo_retorno['tipo'].values

                if len(tipo_variaveis_retorno) > 0:  # se tiver valor no tipo do retorno
                    tipo_variaveis_retorno = tipo_variaveis_retorno[0]
                else:
                    if nome_retorno not in variavel_nao_declarada:  # se a variavel não tiver sido declarada
                        print(error_handler.newError(
                            'ERR-VAR-NOT-DECL', value=nome_retorno))  # printa o erro
                        variavel_nao_declarada.append(nome_retorno)
                    # se não tiver valor no tipo do retorno, retorna vazio
                    tipo_variaveis_retorno = 'vazio'

                # muda o tipo do retorno
                tipo_ret = {nome_retorno: tipo_variaveis_retorno}
                # adiciona na lista de retorno
                tipo_ret_dict.append(tipo_ret)

                # adiciona na lista de tipos
                tipos.append(tipo_variaveis_retorno)

        if len(tipos) > 0:
            # se tiver flutuante, retorna flutuante, se não, retorna inteiro
            tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        tab_sym.at[ret_linha_i,
                   'valor'] = tipo_ret_dict  # muda o valor do retorno
        tab_sym.at[ret_linha_i, 'tipo'] = tipo


def chamada_funcao_aux(tab_sym, filho):
    func_name = ''
    parametros = []
    iniciacao = ''
    linha_declaracao = ''
    # encontra o idx da funcao
    func_name = filho.children[0].children[0].label
    # encontra os parametros da chamada da funcao
    parametros = encontra_parametros(filho, parametros)

    if len(filho.label.split(':')) > 1:
        # encontra a linha da declaracao da funcao
        linha_declaracao = filho.label.split(':')[1]

    declaracao_funcao = tab_sym.loc[tab_sym['lex']
                                    == func_name]  # encontra a declaracao da funcao na tabela de simbolos
    tipo_funcao = declaracao_funcao['tipo'].values[0] if len(
        declaracao_funcao) > 0 else 'vazio'  # encontra o tipo da funcao

    parametro_list = []

    if len(parametros) >= 1:  # se a funcao tiver parametros
        for param in parametros:  # para cada parametro
            for nome_param, tipo_param in param.items():  # para cada idx e tipo do parametro
                parametro_dic = {}
                parametro_inicializado = tab_sym.loc[(
                    tab_sym['lex'] == nome_param) & (tab_sym['iniciacao'] == '1')]  # encontra o parametro na tabela de simbolos
                # cria um dicionario com o idx e tipo do parametro
                parametro_dic[nome_param] = tipo_param
                # adiciona o dicionario na lista de parametros
                parametro_list.append(parametro_dic)

                # se o parametro foi inicializado
                iniciacao = '1' if len(parametro_inicializado) > 0 else '0'

    insere_tabela(tab_sym, ['ID', filho.children[0].children[0].label, tipo_funcao, 0, 0, 0,
                            escopo, iniciacao, linha_declaracao, 'chamada_funcao', parametro_list, []])  # insere na tabela de simbolos


def atribuicao_funcao_aux(tab_sym, filho):
    tipo_valor = atribuicao_expressao(filho.children[2], [])  # expressao
    # ID
    variavel_atribuicao_nome = filho.children[0].children[0].children[0].label

    if len(filho.label.split(':')) > 1:  # se tiver linha de declaracao
        linha_declaracao = filho.label.split(':')[1]

    for i in tipo_valor:
        for valor, tipo in i.items():  # para cada valor e tipo da expressao
            if tipo == 'parametro':  # se for parametro
                variavel_declarada = tab_sym.loc[(
                    tab_sym['lex'] == valor) & (tab_sym['iniciacao'] == '0')]  # procura na tabela de simbolos

                if len(variavel_declarada) > 0:  # se tiver na tabela de simbolos
                    tipo = variavel_declarada['tipo'].values[0]  # pega o tipo
                elif len(variavel_declarada) == 0:  # se nao tiver na tabela de simbolos
                    print(error_handler.newError(
                        'ERR-VAR-NOT-DECL', value=valor))
            tipo = aux_tipo(tipo)  # auxiliar para pegar o tipo

            valor_atribuido[valor] = tipo  # atribui o valor e o tipo
            valss.append(valor_atribuido)  # adiciona na lista de valss

            var_tipo = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == '0') & (tab_sym['escopo'] == escopo)]  # procura na tabela de simbolos

            if tipo == 'ID':  # se for ID
                global_var = var_tipo
                var_tipo = var_tipo['tipo'].values  # pega o tipo

            if len(var_tipo) > 0:
                var_tipo = var_tipo[0]

            if len(var_tipo) == 0 and (tipo != 'inteiro' and tipo != 'flutuante'):
                global_var = tab_sym.loc[(
                    tab_sym['lex'] == variavel_atribuicao_nome) & (tab_sym['iniciacao'] == '0')]

                if len(global_var) > 0:
                    global_var = global_var['tipo'].values
                    global_var = global_var[0]  # pega o tipo
                    var_tipo = global_var  # atribui o tipo

            else:
                tipo_variavel_valor = tipo  # atribui o tipo
                var_tipo = tipo_variavel_valor  # atribui o tipo

            dimensoes = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == '0')]  # procura na tabela de simbolos
            dims[0] = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == '0')]  # procura na tabela de simbolos
            dims[1] = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == '0')]  # procura na tabela de simbolos

            dimensoes = dimensoes['dimensao'].values  # pega a dimensao

            if len(dimensoes) > 0:  # se tiver dimensao
                dimensoes = dimensoes[0]
            else:
                dimensoes = 0

            # pega o tamanho da dimensao 1
            dims[0] = dims[0]['tamanho dimensional 1'].values

            if len(dims[0]) > 0:  # se tiver tamanho da dimensao 1
                dims[0] = dims[0][0]  # pega o tamanho da dimensao 1

            if len(dims[1]) > 0:  # se tiver tamanho da dimensao 2
                dims[1] = dims[1][0]

            if int(dimensoes) > 0:  # se tiver dimensao
                dimensoes, dims[0], dims[1] = verifica_dimensoes(
                    filho, 0, 0, 0)  # verifica as dimensoes

            insere_tabela(tab_sym, ['ID', variavel_atribuicao_nome, var_tipo, dimensoes,
                                    dims[0], dims[1], escopo, '1', linha_declaracao, '0', [], valss])  # insere na tabela de simbolos


def tab_sym_aux(tree, tab_sym):
    dims = [0, '', '']

    for filho in tree.children:
        if ('declaracao_variaveis' in filho.label):

            dims[0], dims[1], dims[2] = verifica_dimensoes(
                filho, 0, 0, 0)

            linha_declaracao = filho.label.split(':')
            insere_tabela(tab_sym, ['ID', str(filho.children[2].children[0].children[0].children[0].label), str(
                filho.children[0].children[0].children[0].label), dims[0], dims[1], dims[2], escopo, '0', linha_declaracao[1], '0', [], []])
            return tab_sym

        elif ('declaracao_funcao' in filho.label):
            processa_declaracao_funcao(filho, tab_sym)

        elif ('retorna' in filho.label):
            retorna_funcao(tab_sym)

        elif ('chamada_funcao' in filho.label):
            chamada_funcao_aux(tab_sym, filho)
        elif ('atribuicao' in filho.label):
            atribuicao_funcao_aux(tab_sym, filho)

        tab_sym_aux(filho, tab_sym)

    return tab_sym


def verifica_tipo_atribuicao(variavel_atual, tipo_variavel, escopo_variavel, inicializacao_variaveis, variaveis, funcoes, tab_sym):
    status = True
    tipo_atribuicao = ''
    nome_inicializacao = ''
    tipo_variavel_inicializacao_retorno = ''
    tipo_variavel_novo = ''

    nome_variavel = variavel_atual['lex']
    for ini_variaveis in inicializacao_variaveis:
        for ini_var in ini_variaveis:
            for nome_variavel_inicializacao, tipo_variavel_inicializacao in ini_var.items():

                status = True
                nome_inicializacao = nome_variavel_inicializacao
                declaracao_variavel = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                    tab_sym['escopo'] == escopo_variavel) & (tab_sym['iniciacao'] == '0')]

                if len(declaracao_variavel) == 0:
                    declaracao_variavel_global = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                        tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]

                    if len(declaracao_variavel_global) > 0:
                        tipo_variavel_novo = declaracao_variavel_global['tipo'].values[0]
                else:
                    tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                if nome_variavel_inicializacao in funcoes:
                    tipo_atribuicao = tab_sym.loc[tab_sym['lex']
                                                  == nome_variavel_inicializacao]
                    tipo_atribuicao = tipo_atribuicao['tipo'].values
                    tipo_atribuicao = tipo_atribuicao[0]

                    if tipo_variavel_novo == tipo_atribuicao:
                        status = True
                    else:
                        status = False

                    if status == False:

                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=[nome_variavel,
                                                                                  tipo_variavel_novo, nome_variavel_inicializacao, tipo_atribuicao]))

                    return status, tipo_variavel_inicializacao, tipo_variavel_novo, nome_inicializacao

                elif nome_variavel_inicializacao in variaveis['lex'].values:
                    tipo_atribuicao = tab_sym.loc[(tab_sym['lex'] == nome_variavel_inicializacao) & (
                        tab_sym['escopo'] == escopo_variavel) & (tab_sym['iniciacao'] == '0')]

                    if len(tipo_atribuicao) == 0:
                        tipo_atribuicao = tab_sym.loc[(tab_sym['lex'] == nome_variavel_inicializacao) & (
                            tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]

                    tipo_atribuicao = tipo_atribuicao['tipo'].values
                    if len(tipo_atribuicao) > 0:
                        tipo_atribuicao = tipo_atribuicao[0]

                    if len(tipo_variavel_novo) > 0 and len(tipo_atribuicao) > 0:
                        if tipo_variavel_novo == tipo_atribuicao:
                            status = True
                        else:
                            status = False

                    if status == False:
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=[nome_variavel,
                                                                                  tipo_variavel_novo, nome_variavel_inicializacao, tipo_atribuicao]))

                elif tipo_variavel_inicializacao == 'inteiro' or tipo_variavel_inicializacao == 'flutuante':

                    declaracao_variavel_valor = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                        tab_sym['escopo'] == escopo_variavel) & (tab_sym['iniciacao'] == '0')]

                    if len(declaracao_variavel_valor) == 0:
                        declaracao_variavel_global_valor = tab_sym.loc[(tab_sym['lex'] == nome_variavel) & (
                            tab_sym['escopo'] == 'global') & (tab_sym['iniciacao'] == '0')]

                        if len(declaracao_variavel_global_valor) > 0:
                            tipo_variavel_novo = declaracao_variavel_global_valor['tipo'].values[0]
                    else:
                        tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                    if '.' in str(nome_variavel_inicializacao):
                        tipo_variavel = 'flutuante'

                    if tipo_variavel_inicializacao == 'flutuante':
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
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=[nome_variavel,
                                                                                  tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao]))
                tipo_variavel_inicializacao_retorno = tipo_variavel_inicializacao

    return status, tipo_variavel_inicializacao_retorno, tipo_variavel_novo, nome_inicializacao


def processa_semantica(tab_sym):
    variaveis = tab_sym.loc[tab_sym['funcao'] == '0']

    funcoes = tab_sym.loc[tab_sym['funcao']
                          != '0', 'lex'].unique()

    varss = variaveis
    i = 0
    for var in variaveis['lex'].unique():

        linhas = tab_sym[tab_sym['lex'] == var].index.tolist()
        linha = tab_sym[tab_sym['lex'] == var]

        if len(linhas) > 1:
            linhas = linha[linha['iniciacao'] == '0'].index.tolist()
            if len(linhas) > 1:
                varss.drop(linhas[0])

    for _, row in variaveis.iterrows():
        lista_declaracao_variavel = tab_sym.loc[(tab_sym['lex'] == row['lex']) & (
            tab_sym['iniciacao'] == '0') & (tab_sym['escopo'] == row['escopo'])]

        if len(lista_declaracao_variavel) > 1:
            print(error_handler.newError(
                'WAR-ALR-DECL', value=[row['lex']]))

    escopo_variaveis_verificacao = varss['escopo'].unique()
    for e in escopo_variaveis_verificacao:
        for var in variaveis['lex'].unique():
            mesmo_escopo = varss[(varss['escopo'] == e) & (
                varss['lex'] == var)]

            if len(mesmo_escopo) > 1:
                linha_mesmo_escopo = mesmo_escopo.index.tolist()
                varss.drop(linha_mesmo_escopo[0])

    for linha in varss.index:
        inicializacao_variaveis = tab_sym.loc[(tab_sym['lex'] == variaveis['lex'][linha]) & (
            tab_sym['escopo'] == variaveis['escopo'][linha]) & (tab_sym['iniciacao'] == '1')]
        inicializacao_variaveis = inicializacao_variaveis['valor'].values

        inicializacao_variaveis_valores = []
        if len(inicializacao_variaveis) > 0:
            inicializacao_variaveis_valores = inicializacao_variaveis

        if len(inicializacao_variaveis_valores) > 0:
            boolen_tipo_igual, tipo_variavel_atribuida, tipo_atribuicao, nome_variavel_inicializacao = verifica_tipo_atribuicao(
                variaveis.iloc[i], variaveis['tipo'][linha], variaveis['escopo'][linha], inicializacao_variaveis_valores, variaveis, funcoes, tab_sym)

        i += 1

    variaveis_repetidas_valores = variaveis['lex'].unique()

    for var_rep in variaveis_repetidas_valores:
        variaveis_repetidas = variaveis.loc[variaveis['lex'] == var_rep]

        if len(variaveis_repetidas) > 1:
            variaveis_repetidas_index = variaveis_repetidas[variaveis_repetidas['iniciacao'] == '0'].index
            variaveis_repetidas_linhas = variaveis_repetidas[variaveis_repetidas['iniciacao'] == '0']
            escopos_variaveis = variaveis_repetidas_linhas['escopo'].unique()

            for esc in escopos_variaveis:
                variaveis_repetidas_escopo_igual_index = variaveis_repetidas_linhas.loc[
                    variaveis_repetidas_linhas['escopo'] == esc].index
                variaveis.drop(variaveis_repetidas_escopo_igual_index[0])

        elif len(variaveis_repetidas) == 0:
            print(error_handler.newError('ERR-VAR-NOT-DECL', value=[var_rep]))

    repetidos_variaveis_atribuicao = variaveis['lex'].unique()
    for rep in repetidos_variaveis_atribuicao:
        tabela_variaveis_repetida = variaveis.loc[variaveis['lex'] == rep]
        tabela_variaveis_repetida_index = variaveis.loc[variaveis['lex'] == rep].index

        if len(tabela_variaveis_repetida_index) > 1:
            variaveis.drop(tabela_variaveis_repetida_index[0])

    if ('principal' not in funcoes):
        print(error_handler.newError('ERR-FUNC-NOT-DECL'))

    for index, row in variaveis.iterrows():
        dimensao_variavel = row['dimensao']

        if int(dimensao_variavel) > 0:
            if int(dimensao_variavel) == 1:
                if '.' in str(row['tamanho dimensional 1']):
                    print(error_handler.newError(
                        'ERR-IND-ARRAY', value=[row['lex']]))

            elif int(dimensao_variavel) == 2:
                if '.' in str(row['tamanho dimensional 2']):
                    print(error_handler.newError(
                        'ERR-IND-ARRAY', value=[row['lex']]))

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
                    for nome_variavel_retorno, tipo_variavel_retorno in rt_vs.items():

                        if (row['lex'] == nome_variavel_retorno):
                            inicializada = True

        if (inicializada == False):
            print(error_handler.newError(
                'WAR-SEM-VAR-DECL-NOT-USED', value=[row['lex']]))

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

            if (func == 'retorna'):
                escopo_retorno = declaracao_funcao['escopo'].values
                escopo_retorno = escopo_retorno[0]

                variavel_retornada = declaracao_funcao['valor'].values[0]
                for var in variavel_retornada:
                    for n, t in var.items():
                        variavel_retornada = n

                tipo_retorno_funcao = declaracao_funcao['tipo'].values
                tipo_retorno_funcao = tipo_retorno_funcao[0]

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
                    tab_sym['escopo'] == escopo_retorno) & (tab_sym['lex'] != 'retorna')]

                nome_funcao = procura_funcao_escopo['lex'].values
                nome_funcao = nome_funcao[0]

                tipo_funcao = procura_funcao_escopo['tipo'].values
                tipo_funcao = tipo_funcao[0]

                if (tipo_funcao != tipo_retorno_funcao):
                    print(error_handler.newError('ERR-FUNC-TYPE-RETURN', value=(nome_funcao, tipo_funcao, tipo_retorno_funcao)
                                                 ))

            if len(chamada_funcao) > 0:

                if len(declaracao_funcao) < 1:
                    print(error_handler.newError(
                        'ERR-CHAMA-FUNC', value=[func]))
                else:
                    quantidade_parametros_chamada = chamada_funcao['parametros']
                    quantidade_parametros_chamada = quantidade_parametros_chamada.values
                    quantidade_parametros_chamada = quantidade_parametros_chamada[0]

                    quantidade_parametros_declaracao_funcao = declaracao_funcao['parametros']
                    quantidade_parametros_declaracao_funcao = quantidade_parametros_declaracao_funcao.values
                    quantidade_parametros_declaracao_funcao = quantidade_parametros_declaracao_funcao[
                        0]

                    if len(quantidade_parametros_chamada) != len(quantidade_parametros_declaracao_funcao):
                        print(error_handler.newError(
                            'ERR-PARAM-FUNC-INCOMP-'+'MENOS' if len(quantidade_parametros_chamada) < len(
                                quantidade_parametros_declaracao_funcao) else 'MAIS', value=[func]))

            else:
                if len(declaracao_funcao) > 0:
                    if func != 'retorna':
                        print(error_handler.newError(
                            'WAR-NOT-USED-FUNC', value=[func]))


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
            processa_semantica(tab_sym)

            # salva a tabela de simbolos em um arquivo csv
            tab_sym.to_csv(f'{argv[1]}.csv', index=None, header=True)
            poda_arvore(root, tokens, nodes)  # poda a arvore
            UniqueDotExporter(root).to_picture(
                f'{sys.argv[1]}.podada.unique.ast.png')


def retorna_arvore_tabela(data):
    root = retorna_arvore(data)  # retorna a arvore do parser

    if root:
        tab_sym = aux_simbolos_tabela()  # cria a tabela de simbolos
        tab_sym = tab_sym_aux(
            root, tab_sym)

        processa_semantica(tab_sym)

        poda_arvore(root, tokens, nodes)  # poda a arvore

        return root, tab_sym
    else:
        return None, None
