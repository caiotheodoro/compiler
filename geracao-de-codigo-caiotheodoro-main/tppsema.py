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
            processa_numero(filho, aux_dict, valss)
        elif filho.label == 'ID':
            processa_id(filho, aux_dict, valss)  # verifica se o no é um ID

        # processa a expressao recursivamente
        valss = atribuicao_expressao(filho, valss)

    return valss


def encontra_indice_retorno(expressao):

    indice = ''
    tipo_retorno = ''
    aux_dict = {}
    valss = []
    for filho in expressao.children:  # percorre os filhos do no retorna
        if filho.label == 'numero':  # verifica se o no é um numero
            return processa_numero(filho, aux_dict, valss)
        elif filho.label == 'ID':  # verifica se o no é um ID
            return processa_id(filho, aux_dict, valss)

        tipo_retorno, indice = encontra_indice_retorno(
            filho)  # processa a expressao recursivamente

    return tipo_retorno, indice


def encontra_atribuicao_valor(expressao, valss):
    tipo_retorno = ''
    aux_dict = {}
    for filho in expressao.children:  # percorre os filhos do no retorna
        if filho.label == 'numero':
            return processa_numero(filho, aux_dict, valss)
        elif filho.label == 'ID':
            return processa_id(filho, aux_dict, valss)

        tipo_retorno, _ = encontra_indice_retorno(filho)

    return tipo_retorno, valss


def encontra_expressao_retorno(retorna, lista_retorno):

    for ret in retorna.children:  # percorre os filhos do no retorna
        if ret.label == 'ID':  # verifica se o no é um ID
            return processa_id(ret, aux_dict, lista_retorno)
        if ret.label == 'numero':  # verifica se o no é um numero
            return processa_numero(ret, aux_dict, lista_retorno)

        lista_retorno = encontra_expressao_retorno(
            ret, lista_retorno)  # processa a expressao recursivamente

    return lista_retorno


def processa_expressao(ret):
    global retorno
    expressoes = ['expressao_aditiva',
                  'expressao_multiplicativa']  # lista de expressoes
    if ret.label in expressoes:  # verifica se o no é uma expressao
        retorno = encontra_expressao_retorno(
            ret, retorno)  # retorna o tipo do retorno
        return retorno
    encontra_valores_retorno(ret, retorno)


def encontra_valores_retorno(retorna, retorno):

    for ret in retorna.children:  # percorre os filhos do no retorna
        processa_expressao(ret)  # processa a expressao

    return retorno  # retorna o tipo do retorno


def encontra_tipo_nome_parametro(parametro, tipo, nome):

    for param in parametro.children:  # percorre os filhos do no parametro
        # retorna o tipo e o nome do parametro
        tipo, nome = processa_parametro(param, tipo, nome)

    return tipo, nome  # retorna o tipo e o nome do parametro


def encontra_parametro_funcao(no, parametros):

    parametro = {}

    for n in no.children:
        if (no.label == 'parametro'):
            tipo, nome = encontra_tipo_nome_parametro(
                no, '', '')  # retorna o tipo e o nome do parametro

            parametro[nome] = tipo  # adiciona o parametro no dicionario

            parametros.append(parametro)  # adiciona o parametro na lista

            return parametros
        encontra_parametro_funcao(n, parametros)  # percorre os filhos do no

    return parametros


def encontra_parametros(no_parametro, parametros):  # encontra os parametros da funcao
    no_parametro = no_parametro
    parametros = parametros
    parametro = {}
    tipo = ''
    nome = ''

    for no in no_parametro.children:  # percorre os filhos do no parametro
        if (no.label == 'expressao'):
            # retorna o tipo e o nome do parametro
            tipo, nome = encontra_indice_retorno(no)
            parametro[nome] = tipo  # adiciona o parametro no dicionario
            # adiciona o dicionario na lista de parametros
            parametros.append(parametro)

            return parametros

        # percorre os filhos do no parametro
        encontra_parametros(no, parametros)
    return parametros


def encontra_indice_retorno(expressao):
    for filhos in expressao.children:
        if filhos.label == 'numero':  # verifica se o filho é um numero
            indice = filhos.children[0].children[0].label
            tipo_retorno = filhos.children[0].label  # retorna o tipo do numero

            # converte o tipo do numero
            tipo_retorno = conv_tipo.get(tipo_retorno)

            return tipo_retorno, indice

        elif filhos.label == 'ID':
            indice = filhos.children[0].label  # retorna o nome do ID
            tipo_retorno = 'parametro'  # retorna o tipo do ID

            return tipo_retorno, indice

        tipo_retorno, indice = encontra_indice_retorno(
            filhos)  # verifica se o filho tem filhos

    return tipo_retorno, indice


def processa_indice(filho):
    if filho.children[0].label == 'indice':
        # retorna a dimensao e o indice
        return 2, *encontra_indice_retorno(filho.children[0].children[1]), *encontra_indice_retorno(filho.children[2])
    else:
        # retorna a dimensao e o indice
        return 1, *encontra_indice_retorno(filho.children[1]), 0


def verifica_dimensoes(tree, dimensao, indice_1, indice_2):

    for filho in tree.children:  # percorre os filhos da arvore
        if filho.label == 'indice':  # verifica se o filho é um indice
            # processa o indice
            dimensao, indice_1, *indice_2 = processa_indice(filho)
            return dimensao, indice_1, indice_2

        dimensao, indice_1, indice_2 = verifica_dimensoes(
            filho, dimensao, indice_1, indice_2)  # verifica se o filho tem filhos

    return dimensao, indice_1, indice_2


def processa_retorna(filho, tipo, func_name, parametros):
    valor_tipo_ret = encontra_valores_retorno(
        filho, 'n/a')  # retorna o tipo e o valor do retorno
    linha_retorno = ''
    if len(filho.label.split(':')) > 1:
        linha_retorno = filho.label.split(':')[1]  # retorna a linha do retorno
    tipo_retorno = 'vazio'  # retorna o tipo do retorno
    return tipo, func_name, parametros, valor_tipo_ret, tipo_retorno, linha_retorno


def encontra_dados_funcao(declaracao_funcao, tipo, func_name, parametros, valor_tipo_ret, tipo_retorno, linha_retorno):

    for filho in declaracao_funcao.children:  # percorre os filhos da declaracao de funcao
        if filho.label == 'tipo':  # se for tipo
            tipo = processa_tipo(filho)
        elif filho.label == 'lista_parametros':  # se for lista de parametros
            parametros = processa_lista_parametros(filho)
        elif filho.label == 'cabecalho':  # se for cabecalho
            func_name, _ = processa_cabecalho(filho, func_name)
        elif 'retorna' in filho.label:  # se for retorna
            return processa_retorna(filho, tipo, func_name, parametros)
        tipo, func_name, parametros, valor_tipo_ret, tipo_retorno, linha_retorno = encontra_dados_funcao(
            filho, tipo, func_name, parametros, valor_tipo_ret, tipo_retorno, linha_retorno
        )

    return tipo, func_name, parametros, valor_tipo_ret, tipo_retorno, linha_retorno


def insere_tabela(tab_sym, args):
    tab_sym.loc[len(tab_sym)] = args  # insere na tabela de simbolos


def processa_declaracao_variaveis(filho, tab_sym, dim):
    dim[0], dim[1], dim[2] = verifica_dimensoes(filho, 0, 0, 0)

    global linha_declaracao
    linha_declaracao = filho.label.split(':')
    linha_declaracao = linha_declaracao[0] if len(
        linha_declaracao) == 1 else linha_declaracao[1]  # retorna linha

    insere_tabela(tab_sym,
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
                  ])  # insere na tabela de simbolos

    return tab_sym


def processa_declaracao_funcao(filho, tab_sym):
    global parametros
    global linha_declaracao

    linha_declaracao = ''
    parametros = encontra_parametro_funcao(
        filho, parametros)  # retorna parametros
    if len(filho.label.split(':')) > 1:
        linha_declaracao = filho.label.split(':')[1]  # retorna linha

    tipo, func_name, _, retorno, tipo_retorno, linha_retorno = encontra_dados_funcao(
        filho, '', '', '', '', '', '')  # retorna tipo, nome, parametros, retorno, tipo_retorno, linha_retorno

    # se tipo for vazio, retorna vazio, senão retorna tipo
    tipo = tipo if tipo != '' else 'vazio'

    insere_tabela(tab_sym, ['ID', func_name, tipo, 0, 0,
                  0, escopo, 'N', linha_declaracao, 'S', parametros, 'n/a'])  # insere na tabela de simbolos

    for p in parametros:
        for nome_param, tipo_param in p.items():  # para cada parametro, insere na tabela de simbolos
            insere_tabela(tab_sym, [
                          'ID', nome_param, tipo_param, 0, 0, 0, escopo, 'S', linha_declaracao, 'N', 'n/a', 'n/a'])  # insere na tabela de simbolos

    if retorno and retorno != 'n/a':  # se houver retorno, insere na tabela de simbolos
        tipo_ret_dict = []  # lista de retorno
        for ret in retorno:  # para cada retorno, insere na tabela de simbolos
            for nome_retorno, tipo_retorno in ret.items():  # para cada retorno, insere na tabela de simbolos
                tipo_retorno = tab_sym.loc[tab_sym['lex']
                                           == nome_retorno]['tipo'].values  # encontra o tipo do retorno
                tipo_variaveis_retorno = tipo_retorno[0] if len(
                    tipo_retorno) > 0 else 'vazio'  # se não tiver tipo, retorna vazio

                # cria um dicionario com o nome e o tipo do retorno
                tipo_ret = {nome_retorno: tipo_variaveis_retorno}
                # adiciona na lista de retorno
                tipo_ret_dict.append(tipo_ret)

                # adiciona na lista de tipos
                tipos.append(tipo_variaveis_retorno)

        # se tiver flutuante, retorna flutuante, senão retorna inteiro
        tipo = 'flutuante' if 'flutuante' in tipos else 'inteiro'

        insere_tabela(tab_sym, ['ID', 'retorna', tipo, 0, 0, 0, escopo,
                                'N', linha_retorno, 'S', 'n/a', tipo_ret_dict])  # insere na tabela de simbolos


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
            for nome_retorno, tipo_retorno in ret.items():  # para cada nome e tipo do retorno
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
    # encontra o nome da funcao
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
            for nome_param, tipo_param in param.items():  # para cada nome e tipo do parametro
                parametro_dic = {}
                parametro_inicializado = tab_sym.loc[(
                    tab_sym['lex'] == nome_param) & (tab_sym['iniciacao'] == 'S')]  # encontra o parametro na tabela de simbolos
                # cria um dicionario com o nome e tipo do parametro
                parametro_dic[nome_param] = tipo_param
                # adiciona o dicionario na lista de parametros
                parametro_list.append(parametro_dic)

                # se o parametro foi inicializado
                iniciacao = 'S' if len(parametro_inicializado) > 0 else 'N'

    insere_tabela(tab_sym, ['ID', filho.children[0].children[0].label, tipo_funcao, 0, 0, 0,
                            escopo, iniciacao, linha_declaracao, 'chamada_funcao', parametro_list, 'n/a'])  # insere na tabela de simbolos


def atribuicao_funcao_aux(tab_sym, filho):
    tipo_valor = atribuicao_expressao(filho.children[2], 'n/a')  # expressao
    # ID
    variavel_atribuicao_nome = filho.children[0].children[0].children[0].label

    if len(filho.label.split(':')) > 1:  # se tiver linha de declaracao
        linha_declaracao = filho.label.split(':')[1]

    for i in tipo_valor:
        for valor, tipo in i.items():  # para cada valor e tipo da expressao
            if tipo == 'parametro':  # se for parametro
                variavel_declarada = tab_sym.loc[(
                    tab_sym['lex'] == valor) & (tab_sym['iniciacao'] == 'N')]  # procura na tabela de simbolos

                if len(variavel_declarada) > 0:  # se tiver na tabela de simbolos
                    tipo = variavel_declarada['tipo'].values[0]  # pega o tipo
                elif len(variavel_declarada) == 0:  # se nao tiver na tabela de simbolos
                    print(error_handler.newError(
                        'ERR-VAR-NOT-DECL', value=valor))
            tipo = aux_tipo(tipo)  # auxiliar para pegar o tipo

            valor_atribuido[valor] = tipo  # atribui o valor e o tipo
            valss.append(valor_atribuido)  # adiciona na lista de valss

            var_tipo = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == 'N') & (tab_sym['escopo'] == escopo)]  # procura na tabela de simbolos

            if tipo == 'ID':  # se for ID
                global_var = var_tipo
                var_tipo = var_tipo['tipo'].values  # pega o tipo

            if len(var_tipo) > 0:
                var_tipo = var_tipo[0]

            if len(var_tipo) == 0 and (tipo != 'inteiro' and tipo != 'flutuante'):
                global_var = tab_sym.loc[(
                    tab_sym['lex'] == variavel_atribuicao_nome) & (tab_sym['iniciacao'] == 'N')]

                if len(global_var) > 0:
                    global_var = global_var['tipo'].values
                    global_var = global_var[0]  # pega o tipo
                    var_tipo = global_var  # atribui o tipo

            else:
                tipo_variavel_valor = tipo  # atribui o tipo
                var_tipo = tipo_variavel_valor  # atribui o tipo

            dimensoes = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == 'N')]  # procura na tabela de simbolos
            dims[0] = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == 'N')]  # procura na tabela de simbolos
            dims[1] = tab_sym.loc[(tab_sym['lex'] == variavel_atribuicao_nome) & (
                tab_sym['iniciacao'] == 'N')]  # procura na tabela de simbolos

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
                                    dims[0], dims[1], escopo, 'S', linha_declaracao, 'N', 'n/a', valss])  # insere na tabela de simbolos


def tab_sym_aux(tree, tab_sym):  # monta a tabela de simbolos

    dim = [0, '', '']

    for filho in tree.children:  # percorre os filhos da arvore

        if ('retorna' in filho.label):  # verifica se é um retorno
            retorna_funcao(tab_sym)  # chama a função de retorno
        elif ('declaracao_variaveis' in filho.label):  # verifica se é uma declaração de variaveis
            # chama a função de declaração de variaveis
            return processa_declaracao_variaveis(filho, tab_sym, dim)
        elif ('declaracao_funcao' in filho.label):  # verifica se é uma declaração de função
            # chama a função de declaração de função
            processa_declaracao_funcao(filho, tab_sym)

        elif ('chamada_funcao' in filho.label):  # verifica se é uma chamada de função
            chamada_funcao_aux(tab_sym, filho)
        elif ('atribuicao' in filho.label):  # verifica se é uma atribuição
            atribuicao_funcao_aux(tab_sym, filho)

        tab_sym_aux(filho, tab_sym)  # chama a função recursivamente

    return tab_sym


def retorna_tipo_var(tipo_var_inicializacao, tipo_var, tipo_variavel_novo):
    if tipo_var_inicializacao == 'flutuante':  # verifica se variavel é flutuante
        if tipo_var == 'flutuante':
            status = True
            tipo_variavel_novo = 'flutuante'
        else:
            status = False
            tipo_variavel_novo = 'inteiro'
    else:  # verifica se variavel é inteira
        if tipo_variavel_novo == 'inteiro':
            status = True
            tipo_variavel_novo = 'inteiro'
        else:
            status = False
            tipo_variavel_novo = 'flutuante'

    return status, tipo_variavel_novo  # retorna o status e o tipo da variavel


def verifica_regras_semanticas(tab_sym):  # função principal

    # variaveis globais
    variaveis = tab_sym.loc[tab_sym['funcao'] == 'N']
    funcoes = tab_sym.loc[tab_sym['funcao']
                          != 'N', 'lex'].unique()  # funcoes declaradas

    for var in variaveis['lex'].unique():  # verifica se variavel foi declarada
        checa_declaracao_variavel(
            variaveis, var, tab_sym, error_handler)
    for _, var in variaveis.iterrows():  # verifica se variavel foi inicializada
        checa_inicializacao_variavel(tab_sym, var, error_handler)

    # verifica se funcao tem retorno
    checa_retorno_funcao(tab_sym, error_handler)

    for _, func in tab_sym.iterrows():  # verifica se funcao foi chamada
        if func['lex'] in funcoes:
            parametros = tab_sym.loc[(tab_sym['funcao'] == 'N') &
                                     (tab_sym['escopo'] == func['lex'])]  # parametros da funcao
            chamada = {'lex': func['lex'], 'parametros': parametros}
            # verifica se funcao foi chamada
            checa_chamada_funcao(chamada, tab_sym, error_handler)


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


def retorna_arvore_tabela(data):
    root = retorna_arvore(data)  # retorna a arvore do parser

    if root:
        tab_sym = aux_simbolos_tabela()  # cria a tabela de simbolos
        tab_sym = tab_sym_aux(
            root, tab_sym)

        verifica_regras_semanticas(tab_sym)

        poda_arvore(root, tokens, nodes)  # poda a arvore

        return root, tab_sym
    else:
        return None, None
