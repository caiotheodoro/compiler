from semantic_aux import verifica_dimensoes, encontra_parametro_funcao, encontra_dados_funcao
from myerror import MyError
from anytree import RenderTree, AsciiStyle
from anytree.exporter import DotExporter, UniqueDotExporter
from mytree import MyNode
from tppparser import parser
from tpplex import tokens
import ply.yacc as yacc
import sys
import os
from utils import aux_simbolos_tabela
from sys import argv, exit

import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="sema.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

warr = []
error_handler = MyError('SemaErrors')
escopo = 'global'
root = None


def cria_linha_dataframe(lexema, tipo, escopo, linha_retorno):
    linha_dataframe = {
        'Lexema': lexema,
        'Tipo': tipo,
        'TipoParametros': 'N',
        'Dimensoes': 0,
        'Tamanho1': 0,
        'Tamanho2': 0,
        'Escopo': escopo,
        'Inicializado': 'N',
        'Linha': linha_retorno,
        'Funcao': 'S',
        'Parametros': [],
        'DadosFuncao': []
    }
    return linha_dataframe


def tab_sym_aux(tree, tab_sym):
    for filho in tree.children:
        if 'declaracao_variaveis' in filho.label:
            dimensao, dimensao_1, dimensao_2 = verifica_dimensoes(
                filho, 0, 0, 0)
            linha_declaracao = filho.label.split(':')
            linha_dataframe = [
                'ID',
                str(filho.children[2].children[0].children[0].children[0].label),
                str(filho.children[0].children[0].children[0].label),
                dimensao, dimensao_1, dimensao_2,
                escopo, 'N', linha_declaracao[1], 'N', [], []
            ]
            tab_sym.loc[len(tab_sym)] = linha_dataframe
            if int(dimensao) > 1:
                return tab_sym
            else:
                return tab_sym

        elif 'declaracao_funcao' in filho.label:
            tipo, nome_funcao, tipo_retorno = '', '', ''
            parametros, retorno, tipos = [], [], []

            parametros = encontra_parametro_funcao(filho, parametros)
            linha_declaracao = filho.label.split(':')
            linha_declaracao = linha_declaracao[1]

            tipo, nome_funcao, _, retorno, tipo_retorno, linha_retorno = encontra_dados_funcao(
                filho, '', '', '', '', '', '')
            if tipo == '':
                tipo = 'vazio'

            linha_dataframe = ['ID', nome_funcao, tipo, 0, 0, 0,
                               escopo, 'N', linha_declaracao, 'S', parametros, []]
            tab_sym.loc[len(tab_sym)] = linha_dataframe

            for p in parametros:
                for nome_param, tipo_param in p.items():
                    linha_dataframe = ['ID', nome_param, tipo_param, 0,
                                       0, 0, escopo, 'S', linha_declaracao, 'N', [], []]
                    tab_sym.loc[len(tab_sym)] = linha_dataframe

            if retorno != '':
                pos = 0
                muda_tipo_retorno_lista = []
                for ret in retorno:
                    for nome_retorno, tipo_retorno in ret.items():
                        tipo_retorno = tab_sym.loc[tab_sym['Lexema']
                                                   == nome_retorno]

                        tipo_variaveis_retorno = tipo_retorno['Tipo'].values
                        tipo_variaveis_retorno = tipo_variaveis_retorno[0] if len(
                            tipo_variaveis_retorno) > 0 else 'vazio'

                        muda_tipo_retorno = {
                            nome_retorno: tipo_variaveis_retorno}
                        muda_tipo_retorno_lista.append(muda_tipo_retorno)

                        tipos.append(tipo_variaveis_retorno)
                        pos += 1

                if len(tipos) > 0:
                    tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

                linha_dataframe = ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                                   'N', linha_retorno, 'S', [], muda_tipo_retorno_lista]
                tab_sym.loc[len(tab_sym)] = linha_dataframe

        elif 'retorna' in filho.label:
            tipos = []
            linha_retorno = tab_sym.loc[(
                tab_sym['Lexema'] == 'retorna')]['Linha'].values
            linha_retorno = linha_retorno[0] if len(
                linha_retorno) > 0 else ''
            for ret in filho.children:
                tipo_retorno = tab_sym.loc[tab_sym['Lexema'] == ret.label]
                tipo_variaveis_retorno = tipo_retorno['Tipo'].values
                tipo_variaveis_retorno = tipo_variaveis_retorno[0] if len(
                    tipo_variaveis_retorno) > 0 else 'vazio'
                tipos.append(tipo_variaveis_retorno)

            if len(tipos) > 0:
                tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

            linha_dataframe = ['ID', 'retorna', tipo, 0, 0,
                               0, escopo, 'N', linha_retorno, 'S', [], []]
            tab_sym.loc[len(tab_sym)] = linha_dataframe

        for filho in tree.children:
            tab_sym = tab_sym_aux(filho, tab_sym)

    return tab_sym


def verifica_tipo_atribuicao(variavel_atual, tipo_variavel, escopo_variavel, inicializacao_variaveis, variaveis, funcoes, tabela_simbolos):
    status = True
    tipo_variavel_novo = ''
    nome_inicializacao = ''
    tipo_variavel_inicializacao_retorno = ''
    tipos_distintos = []

    nome_variavel = variavel_atual['Lexema']

    for ini_variaveis in inicializacao_variaveis:
        for ini_var in ini_variaveis:
            for nome_variavel_inicializacao, tipo_variavel_inicializacao in ini_var.items():
                status = True
                nome_inicializacao = nome_variavel_inicializacao

                declaracao_variavel = tabela_simbolos.loc[(tabela_simbolos['Lexema'] == nome_variavel) & (
                    tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['init'] == 'N')]

                if len(declaracao_variavel) == 0:
                    declaracao_variavel_global = tabela_simbolos.loc[(tabela_simbolos['Lexema'] == nome_variavel) & (
                        tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['init'] == 'N')]

                    if len(declaracao_variavel_global) > 0:
                        tipo_variavel_novo = declaracao_variavel_global['Tipo'].values[0]
                else:
                    tipo_variavel_novo = declaracao_variavel['Tipo'].values[0]

                if nome_variavel_inicializacao in funcoes:
                    tipo_atribuicao = tabela_simbolos.loc[tabela_simbolos['Lexema']
                                                          == nome_variavel_inicializacao, 'Tipo'].values[0]

                    if tipo_variavel_novo == tipo_atribuicao:
                        status = True
                    else:
                        status = False

                    if status == False:
                        aviso_string = f"Aviso: Atribuição de tipos distintos '{nome_variavel}' {tipo_variavel_novo} e '{nome_variavel_inicializacao}' {tipo_variavel_inicializacao}"
                        if aviso_string not in warr:
                            warr.append(aviso_string)
                            print(aviso_string)

                    return status, tipo_variavel_inicializacao, tipo_variavel_novo, nome_inicializacao

                elif nome_variavel_inicializacao in variaveis['Lexema'].values:
                    tipo_atribuicao = tabela_simbolos.loc[(tabela_simbolos['Lexema'] == nome_variavel_inicializacao) & (
                        tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['init'] == 'N')]

                    if len(tipo_atribuicao) == 0:
                        tipo_atribuicao = tabela_simbolos.loc[(tabela_simbolos['Lexema'] == nome_variavel_inicializacao) & (
                            tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['init'] == 'N')]

                    tipo_atribuicao = tipo_atribuicao['Tipo'].values

                    if len(tipo_atribuicao) > 0:
                        tipo_atribuicao = tipo_atribuicao[0]

                    if len(tipo_variavel_novo) > 0 and len(tipo_atribuicao) > 0:
                        if tipo_variavel_novo == tipo_atribuicao:
                            status = True
                        else:
                            status = False

                    if status == False:
                        aviso_variavel_string = f"Aviso: Atribuição de tipos distintos '{nome_variavel}' {tipo_variavel_novo} e '{nome_variavel_inicializacao}' {tipo_variavel_inicializacao}"
                        if aviso_variavel_string not in warr:
                            warr.append(aviso_variavel_string)
                            print(aviso_variavel_string)

                elif tipo_variavel_inicializacao == 'inteiro' or tipo_variavel_inicializacao == 'flutuante':
                    declaracao_variavel_valor = tabela_simbolos.loc[(tabela_simbolos['Lexema'] == nome_variavel) & (
                        tabela_simbolos['escopo'] == escopo_variavel) & (tabela_simbolos['init'] == 'N')]

                    if len(declaracao_variavel_valor) == 0:
                        declaracao_variavel_global_valor = tabela_simbolos.loc[(tabela_simbolos['Lexema'] == nome_variavel) & (
                            tabela_simbolos['escopo'] == 'global') & (tabela_simbolos['init'] == 'N')]

                        if len(declaracao_variavel_global_valor) > 0:
                            tipo_variavel_novo = declaracao_variavel_global_valor['Tipo'].values[0]
                    else:
                        tipo_variavel_novo = declaracao_variavel['Tipo'].values[0]

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
                        aviso_variavel_string = f"Aviso: Atribuição de tipos distintos '{nome_variavel}' {tipo_variavel_novo} e '{nome_variavel_inicializacao}' {tipo_variavel_inicializacao}"

                        if aviso_variavel_string not in warr:
                            warr.append(aviso_variavel_string)
                            print(aviso_variavel_string)

                tipo_variavel_inicializacao_retorno = tipo_variavel_inicializacao

    return status, tipo_variavel_inicializacao_retorno, tipo_variavel_novo, nome_inicializacao


def verifica_regras_semanticas(tabela_simbolos):
    variaveis = tabela_simbolos.loc[tabela_simbolos['funcao'] == 'N']
    funcoes = tabela_simbolos.loc[tabela_simbolos['funcao']
                                  != 'N', 'Lexema'].unique()

    i = 0
    variaveis_repetidas_valores_inicio = variaveis['Lexema'].unique()
    var_verificacao = variaveis.copy()

    for var in variaveis_repetidas_valores_inicio:
        linhas = tabela_simbolos[(
            tabela_simbolos['Lexema'] == var)].index.tolist()
        linha = tabela_simbolos[tabela_simbolos['Lexema'] == var]

        if len(linhas) > 1:
            linhas = linha[linha['init'] == 'N'].index.tolist()
            if len(linhas) > 1:
                var_verificacao.drop(linhas[0], inplace=True)

    for index, row in variaveis.iterrows():
        lista_declaracao_variavel = tabela_simbolos.loc[
            (tabela_simbolos['Lexema'] == row['Lexema']) &
            (tabela_simbolos['init'] == 'N') &
            (tabela_simbolos['escopo'] == row['escopo'])
        ]

        if len(lista_declaracao_variavel) > 1:
            string_variavel_declarada = "Aviso: Variável '%s' já declarada anteriormente" % row[
                'Lexema']
            if string_variavel_declarada not in warr:
                warr.append(string_variavel_declarada)
                print("Aviso: Variável '%s' já declarada anteriormente" %
                      row['Lexema'])

    escopo_variaveis_verificacao = var_verificacao['escopo'].unique()

    for e in escopo_variaveis_verificacao:
        for var in variaveis_repetidas_valores_inicio:
            mesmo_escopo = var_verificacao[(var_verificacao['escopo'] == e) & (
                var_verificacao['Lexema'] == var)]

            if len(mesmo_escopo) > 1:
                linha_mesmo_escopo = mesmo_escopo.index.tolist()
                var_verificacao.drop(linha_mesmo_escopo[0], inplace=True)

    for linha in var_verificacao.index:
        variavel = variaveis['Lexema'][linha]
        escopo = variaveis['escopo'][linha]
        inicializacao_variaveis = tabela_simbolos.loc[
            (tabela_simbolos['Lexema'] == variavel) &
            (tabela_simbolos['escopo'] == escopo) &
            (tabela_simbolos['init'] == 'S')
        ]

        inicializacao_variaveis_valores = []

        if len(inicializacao_variaveis) > 0:
            inicializacao_variaveis_valores = inicializacao_variaveis['valor'].values

        if len(inicializacao_variaveis_valores) > 0:
            boolen_tipo_igual, tipo_variavel_atribuida, tipo_atribuicao, nome_variavel_inicializacao = verifica_tipo_atribuicao(
                variaveis.iloc[i], variaveis['Tipo'][linha], variaveis['escopo'][linha], inicializacao_variaveis.iloc[0])
            if boolen_tipo_igual == False:
                tipo_variavel_atribuida = tipo_variavel_atribuida[0]
                tipo_atribuicao = tipo_atribuicao[0]
                nome_variavel_inicializacao = nome_variavel_inicializacao[0]
                string_tipo_diferente = "Aviso: Atribuição de tipo '%s' à variável '%s' de tipo '%s'" % (
                    tipo_atribuicao, nome_variavel_inicializacao, tipo_variavel_atribuida)
                if string_tipo_diferente not in warr:
                    warr.append(string_tipo_diferente)
                    print("Aviso: Atribuição de tipo '%s' à variável '%s' de tipo '%s'" % (
                        tipo_atribuicao, nome_variavel_inicializacao, tipo_variavel_atribuida))
        i += 1

    for func in funcoes:
        linhas = tabela_simbolos.loc[tabela_simbolos['Lexema']
                                     == func].index.tolist()

        if len(linhas) > 1:
            linhas_sem_parametros = tabela_simbolos[
                (tabela_simbolos['Lexema'] == func) & (
                    tabela_simbolos['funcao'] != 'N')
            ].index.tolist()
            if len(linhas_sem_parametros) > 1:
                tabela_simbolos.drop(linhas_sem_parametros[0], inplace=True)

    return tabela_simbolos, warr


# Programa Principal.
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
        root = parser.parse(source_file, debug=log)

        if root:
            tab_sym = aux_simbolos_tabela()
            tab_sym = tab_sym_aux(root, tab_sym)

            print(tab_sym)
