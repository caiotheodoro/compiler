from myerror import MyError
from anytree.exporter import UniqueDotExporter
from tppparser import retorna_arvore
import sys
import os
from utils import conv_tipo, checa_chamada_funcao, checa_retorno_funcao, checa_inicializacao_variavel, checa_declaracao_variavel, aux_tipo, aux_simbolos_tabela, nodes, poda_arvore, processa_cabecalho, processa_lista_parametros, processa_tipo, tokens, processa_numero, processa_id, processa_parametro
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


def encontra_expressao_retorno(retorna, lista_retorno):
    lista_retorno = lista_retorno
    retorno_dict = {}
    tipo_retorno = ''
    indice = ''

    for ret in retorna.children:
        if ret.label == 'numero':
            indice = ret.children[0].children[0].label
            tipo_retorno = ret.children[0].label

            if (tipo_retorno == 'NUM_INTEIRO'):
                tipo_retorno = 'inteiro'

            elif (tipo_retorno == 'NUM_FLUTUANTE'):
                tipo_retorno = 'flutuante'

            retorno_dict[indice] = tipo_retorno
            lista_retorno.append(retorno_dict)

            return lista_retorno

        elif ret.label == 'ID':
            indice = ret.children[0].label
            tipo_retorno = 'parametro'

            retorno_dict[indice] = tipo_retorno
            lista_retorno.append(retorno_dict)

            return lista_retorno

        lista_retorno = encontra_expressao_retorno(ret, lista_retorno)

    return lista_retorno


def encontra_valores_retorno(retorna, retorno):
    retorno = retorno

    for ret in retorna.children:
        expressoes = ['expressao_aditiva', 'expressao_multiplicativa', ]
        if (ret.label in expressoes):
            retorno = encontra_expressao_retorno(ret, retorno)
            return retorno

        encontra_valores_retorno(ret, retorno)

    return retorno


def encontra_tipo_nome_parametro(parametro, tipo, nome):
    tipo = tipo
    nome = nome

    for param in parametro.children:

        if param.label == 'INTEIRO':
            tipo = param.children[0].label
            return tipo, nome

        elif param.label == 'FLUTUANTE':
            tipo = param.children[0].label
            return tipo, nome

        if param.label == 'id':
            nome = param.children[0].label
            return tipo, nome

        tipo, nome = encontra_tipo_nome_parametro(param, tipo, nome)
    return tipo, nome


def atribuicao_expressao(expressao, valores):
    indice = ''
    tipo_retorno = ''
    valores = valores
    valor_dic = {}

    for filhos in expressao.children:
        if filhos.label == 'numero':
            indice = filhos.children[0].children[0].label
            tipo_retorno = filhos.children[0].label

            if (tipo_retorno == 'NUM_INTEIRO'):
                tipo_retorno = 'inteiro'

            elif (tipo_retorno == 'NUM_PONTO_FLUTUANTE'):
                tipo_retorno = 'flutuante'

            valor_dic[indice] = tipo_retorno
            valores.append(valor_dic)

        elif filhos.label == 'ID':
            indice = filhos.children[0].label
            tipo_retorno = 'parametro'

            valor_dic[indice] = tipo_retorno
            valores.append(valor_dic)

        valores = atribuicao_expressao(filhos, valores)

    return valores


def encontra_indice_retorno(expressao):
    indice = ''
    tipo_retorno = ''

    for filhos in expressao.children:
        if filhos.label == 'numero':
            indice = filhos.children[0].children[0].label
            tipo_retorno = filhos.children[0].label

            if (tipo_retorno == 'NUM_INTEIRO'):
                tipo_retorno = 'inteiro'

            elif (tipo_retorno == 'NUM_PONTO_FLUTUANTE'):
                tipo_retorno = 'flutuante'

            return tipo_retorno, indice

        elif filhos.label == 'ID':
            indice = filhos.children[0].label
            tipo_retorno = 'parametro'

            return tipo_retorno, indice

        tipo_retorno, indice = encontra_indice_retorno(filhos)

    return tipo_retorno, indice


def encontra_atribuicao_valor(expressao, valores):
    indice = ''
    tipo_retorno = ''
    valores = valores
    v = {}

    for filhos in expressao.children:
        if filhos.label == 'numero':
            indice = filhos.children[0].children[0].label
            tipo_retorno = filhos.children[0].label

            if (tipo_retorno == 'NUM_INTEIRO'):
                tipo_retorno = 'inteiro'

            elif (tipo_retorno == 'NUM_PONTO_FLUTUANTE'):
                tipo_retorno = 'flutuante'

            v[indice] = tipo_retorno
            valores.append(v)

        elif filhos.label == 'ID':
            indice = filhos.children[0].label
            tipo_retorno = 'parametro'

            v[indice] = tipo_retorno
            valores.append(v)

        tipo_retorno, indice = encontra_indice_retorno(filhos)

    return tipo_retorno, valores


def verifica_dimensoes(tree, dimensao, indice_1, indice_2):
    indice_1 = indice_1
    indice_2 = indice_2
    dimensao = dimensao

    for filho in tree.children:

        if (filho.label == 'indice'):
            if (filho.children[0].label == 'indice'):
                dimensao = 2
                _, indice_1 = encontra_indice_retorno(
                    filho.children[0].children[1])
                _, indice_2 = encontra_indice_retorno(filho.children[2])
                return dimensao, indice_1, indice_2

            else:
                dimensao = 1
                _, indice_1 = encontra_indice_retorno(filho.children[1])
                indice_2 = 0
                return dimensao, indice_1, indice_2

        dimensao, indice_1, indice_2 = verifica_dimensoes(
            filho, dimensao, indice_1, indice_2)
    return dimensao, indice_1, indice_2


def encontra_dados_funcao(declaracao_funcao, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno):
    tipo = tipo
    nome_funcao = nome_funcao
    parametros = parametros
    tipo_retorno = tipo_retorno
    linha_retorno = linha_retorno
    retorno_tipo_valor = retorno_tipo_valor

    global escopo

    for filho in declaracao_funcao.children:
        if (filho.label == 'tipo'):
            tipo = filho.children[0].children[0].label

        elif (filho.label == 'lista_parametros'):
            if (filho.children[0].label == 'vazio'):
                parametros = 'vazio'
            else:
                pass

        elif (filho.label == 'cabecalho'):
            nome_funcao = filho.children[0].children[0].label
            escopo = nome_funcao

        elif ('retorna' in filho.label):

            retorno_tipo_valor = encontra_valores_retorno(filho, [])
            linha_retorno = filho.label.split(':')
            linha_retorno = linha_retorno[1]
            token = filho.children[0].label
            retorno = ''

            tipo_retorno = 'vazio'

            return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno

        tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno = encontra_dados_funcao(
            filho, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno)

    return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno


def encontra_parametro_funcao(no, parametros):

    parametros = parametros
    parametro = {}

    for n in no.children:
        if (no.label == 'parametro'):
            tipo, nome = encontra_tipo_nome_parametro(no, '', '')

            parametro[nome] = tipo

            parametros.append(parametro)

            return parametros
        encontra_parametro_funcao(n, parametros)

    return parametros


def encontra_parametros(no_parametro, parametros):
    no_parametro = no_parametro
    parametros = parametros
    parametro = {}
    tipo = ''
    nome = ''

    for no in no_parametro.children:
        if (no.label == 'expressao'):
            tipo, nome = encontra_indice_retorno(no)
            parametro[nome] = tipo
            parametros.append(parametro)

            return parametros

        encontra_parametros(no, parametros)
    return parametros


def monta_tabela_simbolos(tree, tabela_simbolos):
    dimensao_1 = ''
    dimensao_2 = ''
    dimensao = 0

    for filho in tree.children:
        if ('declaracao_variaveis' in filho.label):
            dimensao, dimensao_1, dimensao_2 = verifica_dimensoes(
                filho, 0, 0, 0)

            if (int(dimensao) > 1):
                linha_declaracao = filho.label.split(':')
                linha_dataframe = ['ID', str(filho.children[2].children[0].children[0].children[0].label), str(
                    filho.children[0].children[0].children[0].label), dimensao, dimensao_1, dimensao_2, escopo, '0', linha_declaracao[1], '0', [], []]
                tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe
                return tabela_simbolos
            else:
                linha_declaracao = filho.label.split(':')
                linha_dataframe = ['ID', str(filho.children[2].children[0].children[0].children[0].label), str(
                    filho.children[0].children[0].children[0].label), dimensao, dimensao_1, dimensao_2, escopo, '0', linha_declaracao[1], '0', [], []]
                tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe
                return tabela_simbolos

        elif ('declaracao_funcao' in filho.label):
            tipo = ''
            nome_funcao = ''
            tipo_retorno = ''
            parametros = []
            retorno = []
            tipos = []

            parametros = encontra_parametro_funcao(filho, parametros)

            linha_declaracao = filho.label.split(':')
            linha_declaracao = linha_declaracao[1]

            tipo, nome_funcao, _, retorno, tipo_retorno, linha_retorno = encontra_dados_funcao(
                filho, '', '', '', '', '', '')

            if tipo == '':
                tipo = 'vazio'

            linha_dataframe = ['ID', nome_funcao, tipo, 0, 0, 0,
                               escopo, '0', linha_declaracao, 'S', parametros, []]
            tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe

            for p in parametros:
                for nome_param, tipo_param in p.items():

                    linha_dataframe = ['ID', nome_param, tipo_param, 0,
                                       0, 0, escopo, 'S', linha_declaracao, '0', [], []]
                    tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe

            if (retorno != ''):
                pos = 0
                muda_tipo_retorno_lista = []
                for ret in retorno:
                    for nome_retorno, tipo_retorno in ret.items():

                        tipo_retorno = tabela_simbolos.loc[tabela_simbolos['lex']
                                                           == nome_retorno]

                        tipo_variaveis_retorno = tipo_retorno['tipo'].values
                        if len(tipo_variaveis_retorno) > 0:
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

                linha_dataframe = ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                                   '0', linha_retorno, 'S', [], muda_tipo_retorno_lista]
                tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe

        elif ('retorna' in filho.label):
            tipos = []

            linha_retorno = tabela_simbolos.loc[(tabela_simbolos['lex'] == 'retorna') & (
                tabela_simbolos['escopo'] == escopo)]

            linha_retorno_index = tabela_simbolos.index[(tabela_simbolos['lex'] == 'retorna') & (
                tabela_simbolos['escopo'] == escopo)].tolist()
            linha_retorno_index = linha_retorno_index[0]

            retorno_linha = linha_retorno['valor'].values.tolist()
            retorno = retorno_linha[0]

            if len(linha_retorno) > 0:
                pos = 0
                muda_tipo_retorno_lista = []
                global variavel_nao_declarada

                for ret in retorno:
                    for nome_retorno, tipo_retorno in ret.items():
                        tipo_retorno = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_retorno) & (
                            tabela_simbolos['escopo'] == escopo)]

                        tipo_variaveis_retorno = tipo_retorno['tipo'].values

                        if len(tipo_variaveis_retorno) > 0:
                            tipo_variaveis_retorno = tipo_variaveis_retorno[0]
                        else:
                            if nome_retorno not in variavel_nao_declarada:
                                print(error_handler.newError(
                                    'WAR-SEM-VAR-DECL-NOT-USED', value=nome_retorno))
                                variavel_nao_declarada.append(nome_retorno)
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

                tabela_simbolos.at[linha_retorno_index,
                                   'valor'] = muda_tipo_retorno_lista
                tabela_simbolos.at[linha_retorno_index, 'tipo'] = tipo

        elif ('chamada_funcao' in filho.label):
            nome_funcao = ''
            parametros = []
            token = ''
            iniciacao = ''

            nome_funcao = filho.children[0].children[0].label
            parametros = encontra_parametros(filho, parametros)

            linha_declaracao = filho.label.split(':')
            linha_declaracao = linha_declaracao[1]

            declaracao_funcao = tabela_simbolos.loc[tabela_simbolos['lex']
                                                    == nome_funcao]

            if len(declaracao_funcao) > 0:
                tipo_funcao = declaracao_funcao['tipo'].values
                tipo_funcao = tipo_funcao[0]
            else:
                tipo_funcao = 'vazio'

            parametro_list = []

            if len(parametros) >= 1:
                for param in parametros:
                    for nome_param, tipo_param in param.items():
                        parametro_dic = {}

                        parametro_inicializado = tabela_simbolos.loc[(
                            tabela_simbolos['lex'] == nome_param) & (tabela_simbolos['iniciacao'] == 'S')]
                        parametro_declarado = tabela_simbolos.loc[(
                            tabela_simbolos['lex'] == nome_param)]

                        parametro_dic[nome_param] = tipo_param
                        parametro_list.append(parametro_dic)

                        if len(parametro_inicializado) > 0:
                            iniciacao = 'S'
                        else:
                            iniciacao = '0'

            linha_dataframe = ['ID', filho.children[0].children[0].label, tipo_funcao, 0,
                               0, 0, escopo, '0', linha_declaracao, 'chamada_funcao', parametro_list, []]
            tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe

        elif ('atribuicao' in filho.label):
            valor_atribuido = {}
            valores = []
            tipo_valor = []
            dimensoes = 0
            tam_dimensao_1 = 0
            tam_dimensao_2 = 0

            tipo_valor = atribuicao_expressao(filho.children[2], [])

            variavel_atribuicao_nome = filho.children[0].children[0].children[0].label

            linha_declaracao = filho.label.split(':')
            linha_declaracao = linha_declaracao[1]

            for i in tipo_valor:
                for valor, tipo in i.items():

                    if tipo == 'parametro':

                        variavel_declarada = tabela_simbolos.loc[(
                            tabela_simbolos['lex'] == valor) & (tabela_simbolos['iniciacao'] == '0')]

                        if len(variavel_declarada) > 0:
                            tipo = variavel_declarada['tipo'].values
                            tipo = tipo[0]
                        elif len(variavel_declarada) == 0:
                            print(error_handler.newError(
                                'ERR-VAR-NOT-DECL', value=valor))

                    if tipo == 'NUM_INTEIRO':
                        tipo = 'inteiro'

                    elif tipo == 'NUM_PONTO_FLUTUANTE':
                        tipo = 'flutuante'

                    valor_atribuido[valor] = tipo
                    valores.append(valor_atribuido)

                    tipo_variavel_recebendo = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                        tabela_simbolos['iniciacao'] == '0') & (tabela_simbolos['escopo'] == escopo)]

                    if tipo == 'ID':
                        tipo_variavel_recebendo_global = tipo_variavel_recebendo

                        tipo_variavel_recebendo = tipo_variavel_recebendo['tipo'].values

                    if len(tipo_variavel_recebendo) > 0:
                        if len(tipo_variavel_recebendo) == 1:
                            tipo_variavel_recebendo = tipo_variavel_recebendo

                        else:
                            tipo_variavel_recebendo = tipo_variavel_recebendo[0]

                    if len(tipo_variavel_recebendo) == 0 and (tipo != 'inteiro' and tipo != 'flutuante'):
                        tipo_variavel_recebendo_global = tabela_simbolos.loc[(
                            tabela_simbolos['lex'] == variavel_atribuicao_nome) & (tabela_simbolos['iniciacao'] == '0')]

                        if len(tipo_variavel_recebendo_global) > 0:
                            tipo_variavel_recebendo_global = tipo_variavel_recebendo_global[
                                'tipo'].values
                            tipo_variavel_recebendo_global = tipo_variavel_recebendo_global[0]

                            tipo_variavel_recebendo = tipo_variavel_recebendo_global

                    else:
                        tipo_variavel_valor = tipo
                        tipo_variavel_recebendo = tipo_variavel_valor

                    dimensoes = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                        tabela_simbolos['iniciacao'] == '0')]
                    tam_dimensao_1 = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                        tabela_simbolos['iniciacao'] == '0')]
                    tam_dimensao_2 = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                        tabela_simbolos['iniciacao'] == '0')]

                    dimensoes = dimensoes['dimensao'].values

                    if len(dimensoes) > 0:
                        dimensoes = dimensoes[0]
                    else:
                        dimensoes = 0

                    tam_dimensao_1 = tam_dimensao_1['tamanho dimensional 1'].values

                    if len(tam_dimensao_1) > 0:
                        tam_dimensao_1 = tam_dimensao_1[0]

                    tam_dimensao_2 = tam_dimensao_2['tamanho dimensional 2'].values

                    if len(tam_dimensao_2) > 0:
                        tam_dimensao_2 = tam_dimensao_2[0]

                    if int(dimensoes) > 0:
                        dimensoes, tam_dimensao_1, tam_dimensao_2 = verifica_dimensoes(
                            filho, 0, 0, 0)

                    linha_dataframe = ['ID', variavel_atribuicao_nome, tipo_variavel_recebendo, dimensoes,
                                       tam_dimensao_1, tam_dimensao_2, escopo, 'S', linha_declaracao, '0', [], valores]
                    tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe

        monta_tabela_simbolos(filho, tabela_simbolos)

    return tabela_simbolos


def verifica_tipo_atribuicao(variavel_atual, tipo_variavel, escopo_variavel, inicializacao_variaveis, variaveis, funcoes, tabela_simbolos):
    status = True
    tipo_atribuicao = ''
    nome_inicializacao = ''
    tipo_variavel_inicializacao_retorno = ''
    tipo_variavel_novo = ''
    tipos_distintos = []

    nome_variavel = variavel_atual['lex']
    for ini_variaveis in inicializacao_variaveis:
        for ini_var in ini_variaveis:
            for nome_variavel_inicializacao, tipo_variavel_inicializacao in ini_var.items():

                status = True
                nome_inicializacao = nome_variavel_inicializacao
                declaracao_variavel = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                    tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['iniciacao'] == '0')]

                if len(declaracao_variavel) == 0:
                    declaracao_variavel_global = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                        tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == '0')]

                    if len(declaracao_variavel_global) > 0:
                        tipo_variavel_novo = declaracao_variavel_global['tipo'].values[0]
                else:
                    tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                if nome_variavel_inicializacao in funcoes:
                    tipo_atribuicao = tabela_simbolos.loc[tabela_simbolos['lex']
                                                          == nome_variavel_inicializacao]
                    tipo_atribuicao = tipo_atribuicao['tipo'].values
                    tipo_atribuicao = tipo_atribuicao[0]

                    if tipo_variavel_novo == tipo_atribuicao:
                        status = True
                    else:
                        status = False

                    if status == False:

                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=[nome_variavel,
                                                                                  tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao]))

                    return status, tipo_variavel_inicializacao, tipo_variavel_novo, nome_inicializacao

                elif nome_variavel_inicializacao in variaveis['lex'].values:
                    tipo_atribuicao = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel_inicializacao) & (
                        tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['iniciacao'] == '0')]

                    if len(tipo_atribuicao) == 0:
                        tipo_atribuicao = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel_inicializacao) & (
                            tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == '0')]

                    tipo_atribuicao = tipo_atribuicao['tipo'].values
                    if len(tipo_atribuicao) > 0:
                        tipo_atribuicao = tipo_atribuicao[0]

                    if len(tipo_variavel_novo) > 0 and len(tipo_atribuicao) > 0:
                        if tipo_variavel_novo == tipo_atribuicao:
                            status = True
                        else:
                            status = False

                    if status == False:
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=(nome_variavel,
                              tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao)))

                elif tipo_variavel_inicializacao == 'inteiro' or tipo_variavel_inicializacao == 'flutuante':

                    declaracao_variavel_valor = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                        tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['iniciacao'] == '0')]

                    if len(declaracao_variavel_valor) == 0:
                        declaracao_variavel_global_valor = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                            tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == '0')]

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
                        print(error_handler.newError('WAR-ATR-TIP-INCOMP', value=(nome_variavel,
                              tipo_variavel_novo, nome_variavel_inicializacao, tipo_variavel_inicializacao)))
                tipo_variavel_inicializacao_retorno = tipo_variavel_inicializacao

    return status, tipo_variavel_inicializacao_retorno, tipo_variavel_novo, nome_inicializacao


def verifica_regras_semanticas(tabela_simbolos):
    variaveis = tabela_simbolos.loc[tabela_simbolos['funcao'] == '0']

    funcoes = tabela_simbolos.loc[tabela_simbolos['funcao'] != '0']
    funcoes = funcoes['lex'].unique()

    i = 0

    variaveis_repetidas_valores_inicio = variaveis['lex'].unique()
    var_verificacao = variaveis
    for var in variaveis_repetidas_valores_inicio:

        linhas = tabela_simbolos[tabela_simbolos['lex'] == var].index.tolist()
        linha = tabela_simbolos[tabela_simbolos['lex'] == var]

        if len(linhas) > 1:
            linhas = linha[linha['iniciacao'] == '0'].index.tolist()
            if len(linhas) > 1:
                var_verificacao.drop(linhas[0])

    for index, row in variaveis.iterrows():
        lista_declaracao_variavel = tabela_simbolos.loc[(tabela_simbolos['lex'] == row['lex']) & (
            tabela_simbolos['iniciacao'] == '0') & (tabela_simbolos['escopo'] == row['escopo'])]

        if len(lista_declaracao_variavel) > 1:
            print(error_handler.newError(
                'WAR-ALR-DECL', value=row['lex']))

    escopo_variaveis_verificacao = var_verificacao['escopo'].unique()
    for e in escopo_variaveis_verificacao:
        for var in variaveis_repetidas_valores_inicio:
            mesmo_escopo = var_verificacao[(var_verificacao['escopo'] == e) & (
                var_verificacao['lex'] == var)]

            if len(mesmo_escopo) > 1:
                linha_mesmo_escopo = mesmo_escopo.index.tolist()
                var_verificacao.drop(linha_mesmo_escopo[0])

    for linha in var_verificacao.index:
        inicializacao_variaveis = tabela_simbolos.loc[(tabela_simbolos['lex'] == variaveis['lex'][linha]) & (
            tabela_simbolos['escopo'] == variaveis['escopo'][linha]) & (tabela_simbolos['iniciacao'] == 'S')]
        inicializacao_variaveis = inicializacao_variaveis['valor'].values

        inicializacao_variaveis_valores = []
        if len(inicializacao_variaveis) > 0:
            inicializacao_variaveis_valores = inicializacao_variaveis

        if len(inicializacao_variaveis_valores) > 0:
            boolen_tipo_igual, tipo_variavel_atribuida, tipo_atribuicao, nome_variavel_inicializacao = verifica_tipo_atribuicao(
                variaveis.iloc[i], variaveis['tipo'][linha], variaveis['escopo'][linha], inicializacao_variaveis_valores, variaveis, funcoes, tabela_simbolos)

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
            print(error_handler.newError('ERR-VAR-NOT-DECL', value=var_rep))

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
                        'ERR-IND-ARRAY', value=row['lex']))

            elif int(dimensao_variavel) == 2:
                if '.' in str(row['tamanho dimensional 2']):
                    print(error_handler.newError(
                        'ERR-IND-ARRAY', value=row['lex']))

        inicializada = False

        df = tabela_simbolos.loc[tabela_simbolos['lex'] == row['lex']]

        if (len(df) > 1):
            for lin in range(len(df)):
                if (df.iloc[lin]['iniciacao'] != '0'):
                    inicializada = True
        else:
            if (tabela_simbolos.iloc[0]['iniciacao'] != '0'):
                inicializada = True

        retorna_parametros = tabela_simbolos.loc[(tabela_simbolos['lex'] == 'retorna') & (
            tabela_simbolos['escopo'] == row['escopo'])]
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
                'WAR-SEM-VAR-DECL-NOT-USED', value=row['lex']))

    for func in funcoes:
        if func == 'principal':
            tabela_retorno = tabela_simbolos.loc[tabela_simbolos['lex'] == 'retorno']

            if (tabela_retorno.shape[0] == 0):
                print(error_handler.newError(
                    'ERR-RET-TIP-INCOMP', value=['inteiro']))

            chamada_funcao_principal = tabela_simbolos.loc[(
                tabela_simbolos['funcao'] == 'chamada_funcao') & (tabela_simbolos['lex'] == 'principal')]

            if len(chamada_funcao_principal) > 0:
                verifica_escopo = chamada_funcao_principal['escopo'].values[0]

                if verifica_escopo == 'principal':
                    print(error_handler.newError(
                        'WAR-REC-PRIN'))
                else:
                    print(error_handler.newError(
                        'ERR-REC-PRIN'))
        else:
            chamada_funcao = tabela_simbolos.loc[(tabela_simbolos['lex'] == func) & (
                tabela_simbolos['funcao'] == 'chamada_funcao')]
            declaracao_funcao = tabela_simbolos.loc[(
                tabela_simbolos['lex'] == func) & (tabela_simbolos['funcao'] == 'S')]

            if (func == 'retorna'):
                escopo_retorno = declaracao_funcao['escopo'].values
                escopo_retorno = escopo_retorno[0]

                variavel_retornada = declaracao_funcao['valor'].values[0]
                for var in variavel_retornada:
                    for n, t in var.items():
                        variavel_retornada = n

                tipo_retorno_funcao = declaracao_funcao['tipo'].values
                tipo_retorno_funcao = tipo_retorno_funcao[0]

                if variavel_retornada in tabela_simbolos['lex'].unique():
                    declaracao_variavel = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_retornada) & (
                        tabela_simbolos['escopo'] == escopo_retorno) & (tabela_simbolos['iniciacao'] == '0')]

                    if len(declaracao_variavel) == 0:

                        declaracao_variavel_global = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_retornada) & (
                            tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == '0')]

                        if len(declaracao_variavel_global) == 0:
                            declaracao_variavel_global = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_retornada) & (
                                tabela_simbolos['escopo'] == escopo_retorno) & (tabela_simbolos['iniciacao'] == 'S')]

                        tipo_retorno_funcao = declaracao_variavel_global['tipo'].values[0]

                procura_funcao_escopo = tabela_simbolos.loc[(tabela_simbolos['funcao'] == 'S') & (
                    tabela_simbolos['escopo'] == escopo_retorno) & (tabela_simbolos['lex'] != 'retorna')]

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
                        'ERR-CHAMA-FUNC', value=func))
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
                                quantidade_parametros_declaracao_funcao) else 'MAIS', value=func))

            else:
                if len(declaracao_funcao) > 0:
                    if func != 'retorna':
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
            tab_sym = monta_tabela_simbolos(
                root, tab_sym)  # monta a tabela de simbolos

            # verifica as regras semanticas
            verifica_regras_semanticas(tab_sym)

            # salva a tabela de simbolos em um arquivo csv
            tab_sym.to_csv(f'{argv[1]}.csv', index=None, header=True)
            poda_arvore(root, tokens, nodes)  # poda a arvore
            UniqueDotExporter(root).to_picture(
                f'{sys.argv[1]}.podada.unique.ast.png')
