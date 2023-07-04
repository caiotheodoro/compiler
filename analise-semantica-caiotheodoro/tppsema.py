from myerror import MyError
from anytree import RenderTree, AsciiStyle
from anytree.exporter import DotExporter, UniqueDotExporter
from mytree import MyNode
from tppparser import retorna_arvore
import pandas as pd
import ply.yacc as yacc
import sys
import os
from utils import check_chamada_funcao, check_retorno_funcao, check_inicializacao_variavel, check_declaracao_variavel, aux_tipo, aux_simbolos_tabela, nodes, poda_arvore, processa_cabecalho, processa_lista_parametros, processa_tipo, tokens, processa_numero, processa_id, processa_parametro
from sys import argv, exit

import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="sema.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

aux_dict = {}
error_handler = MyError('SemaErrors')
escopo = 'global'
root = None
tipo = ''
nome_funcao = ''
tipo_retorno = ''
parametros = []
retorno = []
tipos = []
valor_atribuido = {}
valores = []
tipo_valor = []
dimensoes = 0
dims = [0, 0]


def atribuicao_expressao(expressao, valores):
    valores = valores
    aux_dict = {}
    valores = []
    for filho in expressao.children:
        if filho.label == 'numero':
            processa_numero(filho, aux_dict, valores)
        elif filho.label == 'ID':
            processa_id(filho, aux_dict, valores)

        valores = atribuicao_expressao(filho, valores)

    return valores


def encontra_indice_retorno(expressao):

    indice = ''
    tipo_retorno = ''
    aux_dict = {}
    valores = []
    for filho in expressao.children:
        if filho.label == 'numero':
            return processa_numero(filho, aux_dict, valores)
        elif filho.label == 'ID':
            return processa_id(filho, aux_dict, valores)

        tipo_retorno, indice = encontra_indice_retorno(filho)

    return tipo_retorno, indice


def encontra_atribuicao_valor(expressao, valores):
    tipo_retorno = ''
    aux_dict = {}
    for filho in expressao.children:
        if filho.label == 'numero':
            return processa_numero(filho, aux_dict, valores)
        elif filho.label == 'ID':
            return processa_id(filho, aux_dict, valores)

        tipo_retorno, indice = encontra_indice_retorno(filho)

    return tipo_retorno, valores


def encontra_expressao_retorno(retorna, lista_retorno):

    for ret in retorna.children:
        if ret.label == 'ID':
            return processa_id(ret, aux_dict, lista_retorno)
        if ret.label == 'numero':
            return processa_numero(ret, aux_dict, lista_retorno)

        lista_retorno = encontra_expressao_retorno(ret, lista_retorno)

    return lista_retorno


def processa_expressao(ret):
    global retorno
    expressoes = ['expressao_aditiva', 'expressao_multiplicativa']
    if ret.label in expressoes:
        retorno = encontra_expressao_retorno(ret, retorno)
        return retorno
    encontra_valores_retorno(ret, retorno)


def encontra_valores_retorno(retorna, retorno):

    for ret in retorna.children:
        processa_expressao(ret)

    return retorno


def encontra_tipo_nome_parametro(parametro, tipo, nome):

    for param in parametro.children:
        tipo, nome = processa_parametro(param, tipo, nome)

    return tipo, nome


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


def encontra_indice_retorno(expressao):
    for filhos in expressao.children:
        if filhos.label == 'numero':
            indice = filhos.children[0].children[0].label
            tipo_retorno = filhos.children[0].label

            if tipo_retorno == 'NUM_INTEIRO':
                tipo_retorno = 'inteiro'
            elif tipo_retorno == 'NUM_PONTO_FLUTUANTE':
                tipo_retorno = 'flutuante'

            return tipo_retorno, indice

        elif filhos.label == 'ID':
            indice = filhos.children[0].label
            tipo_retorno = 'parametro'

            return tipo_retorno, indice

        tipo_retorno, indice = encontra_indice_retorno(filhos)

    return tipo_retorno, indice


def processa_indice(filho):
    if filho.children[0].label == 'indice':
        return 2, *encontra_indice_retorno(filho.children[0].children[1]), *encontra_indice_retorno(filho.children[2])
    else:
        return 1, *encontra_indice_retorno(filho.children[1]), 0


def verifica_dimensoes(tree, dimensao, indice_1, indice_2):

    for filho in tree.children:
        if filho.label == 'indice':
            dimensao, indice_1, *indice_2 = processa_indice(filho)
            return dimensao, indice_1, indice_2

        dimensao, indice_1, indice_2 = verifica_dimensoes(
            filho, dimensao, indice_1, indice_2)

    return dimensao, indice_1, indice_2


def processa_retorna(filho, tipo, nome_funcao, parametros):
    retorno_tipo_valor = encontra_valores_retorno(filho, 'n/a')
    linha_retorno = ''
    if len(filho.label.split(':')) > 1:
        linha_retorno = filho.label.split(':')[1]
    tipo_retorno = 'vazio'
    return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno


def encontra_dados_funcao(declaracao_funcao, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno):

    for filho in declaracao_funcao.children:
        if filho.label == 'tipo':
            tipo = processa_tipo(filho)
        elif filho.label == 'lista_parametros':
            parametros = processa_lista_parametros(filho)
        elif filho.label == 'cabecalho':
            nome_funcao, _ = processa_cabecalho(filho, nome_funcao)
        elif 'retorna' in filho.label:
            return processa_retorna(filho, tipo, nome_funcao, parametros)
        tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno = encontra_dados_funcao(
            filho, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno
        )

    return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno


def insere_tabela(tabela_simbolos, args):
    tabela_simbolos.loc[len(tabela_simbolos)] = args


def processa_declaracao_variaveis(filho, tabela_simbolos, dim):
    dim[0], dim[1], dim[2] = verifica_dimensoes(filho, 0, 0, 0)

    # Descomentar isso depois
    global linha_declaracao
    linha_declaracao = filho.label.split(':')
    linha_declaracao = linha_declaracao[0] if len(
        linha_declaracao) == 1 else linha_declaracao[1]

    insere_tabela(tabela_simbolos,
                  [
                      'ID',
                      str(filho.children[2].children[0]
                          .children[0].children[0].label),
                      str(filho.children[0].children[0].children[0].label),
                      *dim,
                      escopo,
                      'N',
                      linha_declaracao,
                      'N',
                      'n/a',
                      'n/a'
                  ])

    return tabela_simbolos


def processa_declaracao_funcao(filho, tabela_simbolos):
    global parametros
    global linha_declaracao

    linha_declaracao = ''
    parametros = encontra_parametro_funcao(filho, parametros)
    if len(filho.label.split(':')) > 1:
        linha_declaracao = filho.label.split(':')[1]

    tipo, nome_funcao, _, retorno, tipo_retorno, linha_retorno = encontra_dados_funcao(
        filho, '', '', '', '', '', '')

    tipo = tipo if tipo != '' else 'vazio'

    insere_tabela(tabela_simbolos, ['ID', nome_funcao, tipo, 0, 0,
                  0, escopo, 'N', linha_declaracao, 'S', parametros, 'n/a'])

    for p in parametros:
        for nome_param, tipo_param in p.items():
            insere_tabela(tabela_simbolos, [
                          'ID', nome_param, tipo_param, 0, 0, 0, escopo, 'S', linha_declaracao, 'N', 'n/a', 'n/a'])

    if retorno and retorno != 'n/a':
        muda_tipo_retorno_lista = []
        for ret in retorno:
            for nome_retorno, tipo_retorno in ret.items():
                tipo_retorno = tabela_simbolos.loc[tabela_simbolos['lex']
                                                   == nome_retorno]['tipo'].values
                tipo_variaveis_retorno = tipo_retorno[0] if len(
                    tipo_retorno) > 0 else 'vazio'

                muda_tipo_retorno = {nome_retorno: tipo_variaveis_retorno}
                muda_tipo_retorno_lista.append(muda_tipo_retorno)

                tipos.append(tipo_variaveis_retorno)

        tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        linha_dataframe = ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                           'N', linha_retorno, 'S', 'n/a', muda_tipo_retorno_lista]
        tabela_simbolos.loc[len(tabela_simbolos)] = linha_dataframe


def retorna_funcao(tabela_simbolos):
    tipos = []

    linha_retorno = tabela_simbolos.loc[(tabela_simbolos['lex'] == 'retorna') & (
        tabela_simbolos['escopo'] == escopo)]

    if not linha_retorno.empty:
        linha_retorno_index = linha_retorno.index[0]
    retorno_linha = linha_retorno['valor'].values.tolist()
    if retorno_linha:
        retorno = retorno_linha[0]

    if len(linha_retorno) > 0:
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
                        print("Erro: Variável '%s' não declarada" %
                              nome_retorno)
                        variavel_nao_declarada.append(nome_retorno)
                    tipo_variaveis_retorno = 'vazio'

                muda_tipo_retorno = {nome_retorno: tipo_variaveis_retorno}
                muda_tipo_retorno_lista.append(muda_tipo_retorno)

                tipos.append(tipo_variaveis_retorno)

        if len(tipos) > 0:
            tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        tabela_simbolos.at[linha_retorno_index,
                           'valor'] = muda_tipo_retorno_lista
        tabela_simbolos.at[linha_retorno_index, 'tipo'] = tipo


def chamada_funcao_aux(tabela_simbolos, filho):
    nome_funcao = ''
    parametros = []
    iniciacao = ''
    linha_declaracao = ''
    nome_funcao = filho.children[0].children[0].label
    parametros = encontra_parametros(filho, parametros)

    if len(filho.label.split(':')) > 1:
        linha_declaracao = filho.label.split(':')[1]

    # Check if the function has a declaration
    declaracao_funcao = tabela_simbolos.loc[tabela_simbolos['lex']
                                            == nome_funcao]
    tipo_funcao = declaracao_funcao['tipo'].values[0] if len(
        declaracao_funcao) > 0 else 'vazio'

    parametro_list = []

    if len(parametros) >= 1:
        for param in parametros:
            for nome_param, tipo_param in param.items():
                parametro_dic = {}
                parametro_inicializado = tabela_simbolos.loc[(
                    tabela_simbolos['lex'] == nome_param) & (tabela_simbolos['iniciacao'] == 'S')]
                parametro_dic[nome_param] = tipo_param
                parametro_list.append(parametro_dic)

                iniciacao = 'S' if len(parametro_inicializado) > 0 else 'N'

    insere_tabela(tabela_simbolos, ['ID', filho.children[0].children[0].label, tipo_funcao, 0, 0, 0,
                                    escopo, iniciacao, linha_declaracao, 'chamada_funcao', parametro_list, 'n/a'])


def atribuicao_funcao_aux(tabela_simbolos, filho):
    tipo_valor = atribuicao_expressao(filho.children[2], 'n/a')
    variavel_atribuicao_nome = filho.children[0].children[0].children[0].label

    if len(filho.label.split(':')) > 1:
        linha_declaracao = filho.label.split(':')[1]

    for i in tipo_valor:
        for valor, tipo in i.items():
            if tipo == 'parametro':
                variavel_declarada = tabela_simbolos.loc[(
                    tabela_simbolos['lex'] == valor) & (tabela_simbolos['iniciacao'] == 'N')]

                if len(variavel_declarada) > 0:
                    tipo = variavel_declarada['tipo'].values[0]
                elif len(variavel_declarada) == 0:
                    print("Erro: Variável '%s' não declarada" % valor)

            tipo = aux_tipo(tipo)

            valor_atribuido[valor] = tipo
            valores.append(valor_atribuido)

            tipo_variavel_recebendo = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                tabela_simbolos['iniciacao'] == 'N') & (tabela_simbolos['escopo'] == escopo)]

            if tipo == 'ID':
                tipo_variavel_recebendo_global = tipo_variavel_recebendo
                tipo_variavel_recebendo = tipo_variavel_recebendo['tipo'].values

            if len(tipo_variavel_recebendo) > 0:
                tipo_variavel_recebendo = tipo_variavel_recebendo[0]

            if len(tipo_variavel_recebendo) == 0 and (tipo != 'inteiro' and tipo != 'flutuante'):
                tipo_variavel_recebendo_global = tabela_simbolos.loc[(
                    tabela_simbolos['lex'] == variavel_atribuicao_nome) & (tabela_simbolos['iniciacao'] == 'N')]

                if len(tipo_variavel_recebendo_global) > 0:
                    tipo_variavel_recebendo_global = tipo_variavel_recebendo_global['tipo'].values
                    tipo_variavel_recebendo_global = tipo_variavel_recebendo_global[0]
                    tipo_variavel_recebendo = tipo_variavel_recebendo_global

            else:
                tipo_variavel_valor = tipo
                tipo_variavel_recebendo = tipo_variavel_valor

            dimensoes = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                tabela_simbolos['iniciacao'] == 'N')]
            dims[0] = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                tabela_simbolos['iniciacao'] == 'N')]
            dims[1] = tabela_simbolos.loc[(tabela_simbolos['lex'] == variavel_atribuicao_nome) & (
                tabela_simbolos['iniciacao'] == 'N')]

            dimensoes = dimensoes['dimensao'].values

            if len(dimensoes) > 0:
                dimensoes = dimensoes[0]
            else:
                dimensoes = 0

            dims[0] = dims[0]['tamanho dimensional 1'].values

            if len(dims[0]) > 0:
                dims[0] = dims[0][0]

            if len(dims[1]) > 0:
                dims[1] = dims[1][0]

            if int(dimensoes) > 0:
                dimensoes, dims[0], dims[1] = verifica_dimensoes(
                    filho, 0, 0, 0)

            insere_tabela(tabela_simbolos, ['ID', variavel_atribuicao_nome, tipo_variavel_recebendo, dimensoes,
                                            dims[0], dims[1], escopo, 'S', linha_declaracao, 'N', 'n/a', valores])


def monta_tabela_simbolos(tree, tabela_simbolos):

    dim = [0, '', '']

    for filho in tree.children:
        if ('declaracao_variaveis' in filho.label):
            return processa_declaracao_variaveis(filho, tabela_simbolos, dim)
        elif ('declaracao_funcao' in filho.label):
            processa_declaracao_funcao(filho, tabela_simbolos)

        elif ('retorna' in filho.label):
            retorna_funcao(tabela_simbolos)

        elif ('chamada_funcao' in filho.label):
            chamada_funcao_aux(tabela_simbolos, filho)
        elif ('atribuicao' in filho.label):
            atribuicao_funcao_aux(tabela_simbolos, filho)

        monta_tabela_simbolos(filho, tabela_simbolos)

    return tabela_simbolos


def retorna_tipo_var(tipo_var_inicializacao, tipo_var, tipo_variavel_novo):
    if tipo_var_inicializacao == 'flutuante':
        if tipo_var == 'flutuante':
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

    return status, tipo_variavel_novo


def verifica_tipo_atribuicao(variavel_atual, tipo_variavel, escopo_variavel, inicializacao_variaveis, variaveis, funcoes, tabela_simbolos):
    nome_variavel = variavel_atual['lex']
    status = ''
    tipo_var_inicializacao_retorno = ''
    tipo_variavel_novo = ''
    nome_inicializacao = ''

    for ini_variaveis in inicializacao_variaveis:
        for ini_var in ini_variaveis:
            if ini_variaveis != 'n/a':
                for nome_var_inicializacao, tipo_var_inicializacao in ini_var.items():
                    status = True
                    nome_inicializacao = nome_var_inicializacao

                    declaracao_variavel = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                        tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['iniciacao'] == 'N')]
                    if len(declaracao_variavel) == 0:
                        declaracao_variavel_global = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                            tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == 'N')]
                        if len(declaracao_variavel_global) > 0:
                            tipo_variavel_novo = declaracao_variavel_global['tipo'].values[0]
                    else:
                        tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                    if nome_var_inicializacao in funcoes:
                        tipo_atribuicao = tabela_simbolos.loc[tabela_simbolos['lex']
                                                              == nome_var_inicializacao, 'tipo'].values
                        if len(tipo_atribuicao) > 0:
                            tipo_atribuicao = tipo_atribuicao[0]

                        if tipo_variavel_novo == tipo_atribuicao:
                            status = True
                        else:
                            status = False

                        if not status:
                            print(error_handler.newError('WAR-ATR-TIP-INCOMP'))

                        return status, tipo_var_inicializacao, tipo_variavel_novo, nome_inicializacao

                    elif nome_var_inicializacao in variaveis['lex'].values:
                        tipo_atribuicao = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_var_inicializacao) & (
                            tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['iniciacao'] == 'N'), 'tipo'].values
                        if len(tipo_atribuicao) == 0:
                            tipo_atribuicao = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_var_inicializacao) & (
                                tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == 'N'), 'tipo'].values

                        if len(tipo_atribuicao) > 0:
                            tipo_atribuicao = tipo_atribuicao[0]

                        if tipo_variavel_novo and tipo_atribuicao:
                            if tipo_variavel_novo == tipo_atribuicao:
                                status = True
                            else:
                                status = False

                        if not status:
                            print(error_handler.newError('WAR-ATR-TIP-INCOMP'))
                    elif tipo_var_inicializacao == 'inteiro' or tipo_var_inicializacao == 'flutuante':
                        declaracao_variavel_valor = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                            tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['iniciacao'] == 'N')]
                        if len(declaracao_variavel_valor) == 0:
                            declaracao_variavel_global_valor = tabela_simbolos.loc[(tabela_simbolos['lex'] == nome_variavel) & (
                                tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['iniciacao'] == 'N')]
                            if len(declaracao_variavel_global_valor) > 0:
                                tipo_variavel_novo = declaracao_variavel_global_valor['tipo'].values[0]
                        else:
                            tipo_variavel_novo = declaracao_variavel['tipo'].values[0]

                        if '.' in str(nome_var_inicializacao):
                            tipo_var = 'flutuante'

                        status, tipo_variavel_novo = retorna_tipo_var(
                            tipo_var, nome_var_inicializacao, tipo_variavel_novo)

                        if not status:
                            print(error_handler.newError('WAR-ATR-TIP-INCOMP'))

                    tipo_var_inicializacao_retorno = tipo_var_inicializacao

    return status, tipo_var_inicializacao_retorno, tipo_variavel_novo, nome_inicializacao


def verifica_regras_semanticas(tabela_simbolos):

    variaveis = tabela_simbolos.loc[tabela_simbolos['funcao'] == 'N']
    funcoes = tabela_simbolos.loc[tabela_simbolos['funcao']
                                  != 'N', 'lex'].unique()

    for var in variaveis['lex'].unique():
        check_declaracao_variavel(
            variaveis, var, tabela_simbolos, error_handler)
    for _, var in variaveis.iterrows():
        check_inicializacao_variavel(tabela_simbolos, var, error_handler)

    check_retorno_funcao(tabela_simbolos, error_handler)

    for _, func in tabela_simbolos.iterrows():
        if func['lex'] in funcoes:
            parametros = tabela_simbolos.loc[(tabela_simbolos['funcao'] == 'N') &
                                             (tabela_simbolos['escopo'] == func['lex'])]
            chamada = {'lex': func['lex'], 'parametros': parametros}
            check_chamada_funcao(chamada, tabela_simbolos, error_handler)


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
        root = retorna_arvore(source_file)

        if root:
            tab_sym = aux_simbolos_tabela()
            tab_sym = monta_tabela_simbolos(root, tab_sym)

            verifica_regras_semanticas(tab_sym)

            tab_sym.to_csv(f'{argv[1]}.csv', index=None, header=True)
            poda_arvore(root, tokens, nodes)
            UniqueDotExporter(root).to_picture(
                f'{sys.argv[1]}.podada.unique.ast.png')
