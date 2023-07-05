from myerror import MyError
from anytree import RenderTree, AsciiStyle
from anytree.exporter import DotExporter, UniqueDotExporter
from mytree import MyNode
from tppsema import retorna_arvore_tabela
from tpplex import tokens
import ply.yacc as yacc
import sys
import os
from utils import instancia_llvm, instancia_modulo, op_list, comp_list
from llvmlite import ir as llvmir
from llvmlite import binding


from sys import argv, exit

import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="gencode.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()


# Get the token map from the lexer.  This is required.


error_handler = MyError('GenCodeErrors')

root = None

tem_se = False
escopo = ''
pilha_loop = []
pilha_loop_validacao = []
pilha_bloco_saida = []
variaveis_declaradas = []
nome_escopo_alocada = []
lista_declaracao_funcao = []
lista_escopo = []
parametros_lista = []


def verifica_expressao_parametros(parametro, escopo, parametros_lista):
    funcao_tab_sym = tab_sym[(
        tab_sym['lex'] == escopo) & (tab_sym['funcao'] == 'S')]

    parametros_funcao_tab_sym = ''
    if not funcao_tab_sym.empty:
        parametros_funcao_tab_sym = funcao_tab_sym['parametros'].values[0]
    funcao_variaveis_parametro = [
        retorno_nome_tab_sym for param_tab_sym in parametros_funcao_tab_sym for retorno_nome_tab_sym, _ in param_tab_sym.items()]

    if parametro in funcao_variaveis_parametro:
        posicao_variavel = funcao_variaveis_parametro.index(parametro)
        expressao_esquerda_temp = parametros_lista[-1].args[posicao_variavel]
    else:
        expressao_esquerda_temp = encontra_variavel_declarada(parametro)

    return expressao_esquerda_temp


def get_operador_declaracao_funcao(label):
    return encontra_variavel_declarada(label)


def build_chamada_funcao(label, operador_esquerdo, operador_direito):
    chamada_funcao = encontra_funcao_declarada(label)
    return constructor.call(chamada_funcao, [constructor.load(operador_esquerdo), constructor.load(operador_direito)])


def chama_funcao_chamando_funcao(no_chama_funcao):

    indices = [4, 5, 7, 8]
    chamadas_funcao = []

    for i in range(0, len(indices), 2):
        operador_esquerdo_declaracao_funcao = get_operador_declaracao_funcao(
            no_chama_funcao.children[indices[i]].label)
        operador_direito_declaracao_funcao = get_operador_declaracao_funcao(
            no_chama_funcao.children[indices[i + 1]].label)
        chamada_funcao = build_chamada_funcao(
            no_chama_funcao.children[3 + i // 2].label, operador_esquerdo_declaracao_funcao, operador_direito_declaracao_funcao)  # 3 + i // 2 = 3, 5, 7, 9
        chamadas_funcao.append(chamada_funcao)

    return chamadas_funcao


def realiza_operacoes(expressao_esquerda_temp, expressao_direita_temp, operacao_sinal):
    operacoes = {
        op_list[0]: constructor.sdiv,
        op_list[1]: constructor.add,
        op_list[2]: constructor.sub,
        op_list[3]: constructor.mul,
    }

    if operacao_sinal in operacoes:
        return operacoes[operacao_sinal](expressao_esquerda_temp, expressao_direita_temp)

    return None


def encontra_expressao(expressao):

    for filhos_expressao in expressao.children:
        if len(filhos_expressao.children) > 0:
            if filhos_expressao.children[0].label in op_list:
                return expressao.children[0].label, expressao.children[1].children[0].label, expressao.children[2].label
        else:
            if filhos_expressao.label in op_list:
                return expressao.children[0].label, expressao.children[1].label, expressao.children[2].label

    return None


def procura_comparacao(no_ate):
    repita = no_ate.parent
    posicao_filho = 0
    posicao_ate = 0

    for filho_repita in repita.children:
        if filho_repita.label == 'ATE':
            posicao_ate = posicao_filho
        posicao_filho += 1

    quantidade_filhos_comparacao = (len(repita.children) - 1) - posicao_ate

    if quantidade_filhos_comparacao == 3:
        return (
            repita.children[posicao_ate + 1].label,
            repita.children[posicao_ate + 2].children[0].label,
            repita.children[posicao_ate + 3].label
        )

    return None


def declara_operacoes_condicionais(if_verdade, if_falso, se):
    filhos = []

    for filho in se.children:
        if filho.label in comp_list:
            filhos.append(se.children[filho.position - 1].label)
            filhos.append(se.children[filho.position + 1].label)

            for filho_adjacente in filhos:
                if filho_adjacente.isdigit():
                    pass
                else:
                    pass


def encontra_funcao_declarada(nome_funcao):
    funcao_encontrada = ''

    if nome_funcao == 'principal':
        nome_funcao = 'main'

    if nome_funcao in lista_escopo:
        funcao_encontrada = lista_declaracao_funcao[lista_escopo.index(
            nome_funcao)]

    return funcao_encontrada


def encontra_variavel_declarada(nome_variavel):
    variavel_encontrada = ''

    # Primeiro procuro no escopo local e depois no global
    if nome_variavel+escopo in nome_escopo_alocada:
        # Pegar a posição onde se encontra esse valor e acessar as variaveis declaradas
        variavel_encontrada = variaveis_declaradas[nome_escopo_alocada.index(
            nome_variavel+escopo)]
    else:
        if nome_variavel+'global' in nome_escopo_alocada:
            variavel_encontrada = variaveis_declaradas[nome_escopo_alocada.index(
                nome_variavel+'global')]

    return variavel_encontrada


def gera_codigo(arvore):
    global builder
    global modulo
    global pilha_bloco_saida
    global pilha_loop_validacao
    global pilha_loop
    global variaveis_declaradas
    global escopo
    global nome_escopo_alocada

    global escreva_inteiro
    global escreva_float
    global leia_inteiro
    global leia_float
    global parametros_lista
    global tem_se

    linha = 0

    for no in arvore.children:
        if ('declaracao_variaveis' in no.label):
            linha = no.label.split(':')
            linha = linha[1]

            # procuro na tabela de símbolos
            variavel = tab_sym[tab_sym['linha'] == linha]

            # Verifico o escopo da variável
            if 'global' == str(variavel['escopo'].values[0]):
                if 'inteiro' == str(variavel['tipo'].values[0]):

                    # Verifica se é um array de uma dimensao
                    if (len(no.children) > 3):

                        # Tamanho da dimensão
                        tamanho_primeira_dimensao = no.children[3].label
                        array_tipo = llvmir.ArrayType(llvmir.IntType(
                            32), int(tamanho_primeira_dimensao))
                        array_global = llvmir.GlobalVariable(
                            modulo, array_tipo, variavel['lex'].values[0])

                        array_global.initializer = llvmir.Constant(
                            array_tipo, None)
                        array_global.linkage = "common"
                        array_global.align = 4

                        variaveis_declaradas.append(array_global)
                        nome_escopo_alocada.append(
                            variavel['lex'].values[0] + 'global')

                    else:
                        if (len(no.children) > 3):
                            # Tamanho da dimensão
                            tamanho_primeira_dimensao = no.children[3].label
                            array_tipo = llvmir.ArrayType(
                                llvmir.FloatType(), int(tamanho_primeira_dimensao))
                            array_global = llvmir.GlobalVariable(
                                modulo, array_tipo, variavel['lex'].values[0])

                            array_global.initializer = llvmir.Constant(
                                array_tipo, None)
                            array_global.linkage = "common"
                            array_global.align = 4

                            variaveis_declaradas.append(array_global)
                            nome_escopo_alocada.append(
                                variavel['lex'].values[0] + 'global')

                        else:
                            # Declara variável global
                            variavel_global = llvmir.GlobalVariable(
                                modulo, llvmir.IntType(32), variavel['lex'].values[0])
                            variavel_global.initializer = llvmir.Constant(
                                llvmir.IntType(32), 0)
                            variavel_global.linkage = "common"
                            variavel_global.align = 4

                            variaveis_declaradas.append(variavel_global)
                            nome_escopo_alocada.append(
                                variavel['lex'].values[0] + 'global')
            else:
                # Caso não seja no escopo global, verifico o tipo da variável
                # Aloca a variável com valor zero
                if ('inteiro' == variavel['tipo'].values[0]):
                    variavel_declarada = builder.alloca(
                        llvmir.IntType(32), name=variavel['lex'].values[0])
                    variavel_declarada.initalizer = llvmir.Constant(
                        llvmir.IntType(32), 0)

                    variavel_declarada.linkage = "common"
                    variavel_declarada.align = 4

                    # Adiciona na lista de variáveis declaradas
                    variaveis_declaradas.append(variavel_declarada)
                    nome_escopo_alocada.append(
                        variavel['lex'].values[0] + escopo)

                else:
                    variavel_declarada = builder.alloca(
                        llvmir.FloatType(), name=str(variavel['lex'].values[0]))
                    variavel_declarada_constante = llvmir.Constant(
                        llvmir.FloatType(), 0.0)

                    builder.store(variavel_declarada_constante,
                                  variavel_declarada)

                    variavel_declarada.linkage = "common"
                    variavel_declarada.align = 4

                    # Adiciona na lista de variáveis declaradas
                    variaveis_declaradas.append(variavel_declarada)
                    nome_escopo_alocada.append(
                        variavel['lex'].values[0] + escopo)

                # Defino o retorno da função onde a variável foi declarada
        elif ('declaracao_funcao' in no.label):
            linha = no.label.split(':')
            if len(linha) > 1:
                linha = linha[1]
            funcao_encontrada = None
            if len(tab_sym['linha']) == len(linha):
                funcao_encontrada = tab_sym[tab_sym['linha'] == linha]

            if funcao_encontrada is not None:
                escopo = funcao_encontrada['lex'].values[0]

            criacao_funcao = llvmir.FunctionType(llvmir.IntType(32), [])
            # Cria a função, porém é necessário verificar o tipo da função
            if ('inteiro' == no.children[0].label):
                if funcao_encontrada is not None:
                    if len(funcao_encontrada['parametros'].values[0]) == 0:
                        criacao_funcao = llvmir.FunctionType(
                            llvmir.IntType(32), ())

                    elif len(funcao_encontrada['parametros'].values[0]) == 1:
                        criacao_funcao = llvmir.FunctionType(
                            llvmir.IntType(32), llvmir.IntType(32))

                    else:
                        criacao_funcao = llvmir.FunctionType(
                            llvmir.IntType(32), [llvmir.IntType(32), llvmir.IntType(32)])

            # Declara a função
            declaracao_funcao = llvmir.Function(
                modulo, criacao_funcao, name='main')
            if funcao_encontrada is not None:
                if funcao_encontrada['lex'].values[0] == 'principal':
                    declaracao_funcao = llvmir.Function(
                        modulo, criacao_funcao, name='main')
                    lista_escopo.append('main')
                    lista_declaracao_funcao.append(declaracao_funcao)

                else:
                    # Necessário verifica se tem parâmetros
                    declaracao_funcao = llvmir.Function(
                        modulo, criacao_funcao, name=funcao_encontrada['lex'].values[0])
                    lista_escopo.append(funcao_encontrada['lex'].values[0])
                    lista_declaracao_funcao.append(declaracao_funcao)

            parametros_funcao = ''
            if funcao_encontrada is not None:
                parametros_funcao = funcao_encontrada['parametros'].values[0]

            # Passa por todos os argumentos e declara eles como argumentos
            quantidade_parametros = 0
            for parametros in parametros_funcao:
                for param_nome, _ in parametros.items():
                    declaracao_funcao.args[quantidade_parametros].name = param_nome
                    quantidade_parametros += 1

            parametros_lista.append(declaracao_funcao)
            # Declara os blocos de entrada e saída
            bloco_entrada = declaracao_funcao.append_basic_block('entry')
            bloco_saida = declaracao_funcao.append_basic_block('exit')

            # Coloca os blocos de saída em uma pilha
            pilha_bloco_saida.append(bloco_saida)

            # Adiciona o bloco de entrada
            builder = llvmir.IRBuilder(bloco_entrada)

        elif ('retorna' in no.label):
            linha = no.label.split(':')
            if len(linha) > 1:
                linha = linha[1]

            # Pesquiso o retorno na tabela de símbolos utilizando a linha declarada
            retorno_encontrado = {}
            if len(tab_sym['linha']) == len(linha):
                retorno_encontrado = tab_sym[(
                    tab_sym['lex'] == 'retorna') & (tab_sym['linha'] == linha)]
            if retorno_encontrado:
                retorno_valor = retorno_encontrado['valor'].values[0]

            # Pego o último da pilha de blocos de saída
            topo_bloco_saida = pilha_bloco_saida.pop()

            # Crio um salto para o bloco de saída
            if (not tem_se):
                builder.branch(topo_bloco_saida)

            # Adiciona o bloco de saída
            if topo_bloco_saida:
                builder.position_at_end(topo_bloco_saida)

            variavel_retornada_encontrada = ''

            # Está retornando apena uma variável ou um valor
            if len(no.children) == 1:
                # Cria o valor de retorno, verificar ainda o retorno correto de cada função
                if retorno_encontrado:
                    if ('inteiro' == retorno_encontrado['tipo'].values[0]):
                        for ret in retorno_valor:
                            for variavel_retornada, tipo_retornado in ret.items():
                                variavel_retornada_encontrada = variavel_retornada

                    elif ('float' == retorno_encontrado['tipo'].values[0]):
                        pass

                # Verifico se é um dígito
                if variavel_retornada_encontrada:
                    if variavel_retornada_encontrada.isdigit():
                        retorno_zero = llvmir.Constant(
                            llvmir.IntType(32), variavel_retornada)
                        builder.ret(retorno_zero)
                    else:
                        # Estou retornando uma variável
                        declaracao = encontra_variavel_declarada(
                            variavel_retornada_encontrada)
                        builder.ret(builder.load(declaracao, ""))

            else:
                # Está retornando uma expressão
                expressao_esquerda, operacao_sinal, expressao_direita = encontra_expressao(
                    no)

                if (expressao_esquerda.isdigit()):
                    # Primeiramente é necessário encontrar as duas variáveis utilizadas na operação
                    expressao_esquerda_temp = llvmir.Constant(
                        llvmir.IntType(32), expressao_esquerda)
                    expressao_direita_temp = llvmir.Constant(
                        llvmir.IntType(32), expressao_direita)

                else:
                    funcao_variaveis_parametro = []
                    funcao_tab_sym = tab_sym[(
                        tab_sym['lex'] == escopo) & (tab_sym['funcao'] == 'S')]
                    if funcao_tab_sym:
                        parametros_funcao_tab_sym = funcao_tab_sym['parametros'].values[0]

                    # Adiciona apenas o nome dos parametros recebidos na função em uma lista
                    for param_tab_sym in parametros_funcao_tab_sym:
                        for retorno_nome_tab_sym, _ in param_tab_sym.items():
                            funcao_variaveis_parametro.append(
                                retorno_nome_tab_sym)

                    parametros_argumentos = parametros_lista.pop()

                    # Verifica se as variáveis utilizadas na operação são as passadas por parametro
                    if expressao_esquerda in funcao_variaveis_parametro:
                        posicao_variavel = funcao_variaveis_parametro.index(
                            expressao_esquerda)
                        expressao_esquerda_temp = parametros_argumentos.args[posicao_variavel]
                    else:
                        variavel_expressao_esquerda = encontra_variavel_declarada(
                            expressao_esquerda)
                        expressao_esquerda_temp = builder.load(
                            variavel_expressao_esquerda, name=str(expressao_esquerda) + '_temp')

                    if expressao_direita in funcao_variaveis_parametro:
                        posicao_variavel_direita = funcao_variaveis_parametro.index(
                            expressao_direita)
                        expressao_direita_temp = parametros_argumentos.args[posicao_variavel_direita]
                    else:
                        variavel_expressao_direita = encontra_variavel_declarada(
                            expressao_direita)
                        # Fazer o load das valores em uma variável temporária
                        expressao_direita_temp = builder.load(
                            variavel_expressao_direita, name=str(expressao_direita) + '_temp')

                resultado_op = realiza_operacoes(
                    expressao_esquerda_temp, expressao_direita_temp, operacao_sinal)
                builder.ret(resultado_op)

        elif ('acao' == no.label):
            if len(no.children) > 1:
                if (no.children[1].label == ':=' or no.children[1].label == '['):
                    # Verificar se o primeiro valor da atribuição é uma função ou não
                    verifica_nome_funcao = no.children[2].label

                    pesquisa_nome_funcao = tab_sym[(
                        tab_sym['lex'] == verifica_nome_funcao) & (tab_sym['funcao'] == 'S')]

                    if len(pesquisa_nome_funcao) > 0:

                        # Encontra a variável que recebe a chamada de função
                        recebe_chamada_funcao = encontra_variavel_declarada(
                            no.children[0].label)

                        # Verificar se na chamada da função, ele passa como parametro outra chamada de função
                        if len(no.children) > 5:
                            resultado_chamada_funcao_esquerda, resultado_chamada_funcao_direita = chama_funcao_chamando_funcao(
                                no)

                            # Cria variaveis temporarias para guardar as respostas das chamadas das funções
                            esquerda_temp = builder.alloca(
                                llvmir.IntType(32), name='chamada_temp_1')
                            builder.store(
                                resultado_chamada_funcao_esquerda, esquerda_temp)

                            direita_temp = builder.alloca(
                                llvmir.IntType(32), name='chamada_temp_2')
                            builder.store(
                                resultado_chamada_funcao_direita, direita_temp)

                            encontra_chamada_funcao_inicial = encontra_funcao_declarada(
                                no.children[2].label)

                            chamada_funcao = builder.call(encontra_chamada_funcao_inicial, [
                                                          builder.load(esquerda_temp), builder.load(direita_temp)])
                            builder.store(chamada_funcao,
                                          recebe_chamada_funcao)
                        else:
                            # Encontra função
                            encontra_chamada_funcao = encontra_funcao_declarada(
                                no.children[2].label)
                            operador_esquerdo_declaracao = encontra_variavel_declarada(
                                no.children[3].label)
                            operador_direito_declaracao = encontra_variavel_declarada(
                                no.children[4].label)

                            chamada_funcao = builder.call(encontra_chamada_funcao, [builder.load(
                                operador_esquerdo_declaracao), builder.load(operador_direito_declaracao)])
                            builder.store(chamada_funcao,
                                          recebe_chamada_funcao)

                    else:

                        # Identifica se é uma atribuição
                        if len(no.children) == 3:

                            # x := y, representa o nome da variável x
                            nome_variavel_recebendo = no.children[0].label

                            # representa o nome da variável y
                            nome_variavel_atribuida = no.children[2].label

                            # Procuro o tipo da variável atribuída
                            tipo_variavel_atribuida = tab_sym[tab_sym['lex']
                                                              == nome_variavel_atribuida]

                            if len(tipo_variavel_atribuida) > 0:
                                tipo_variavel_atribuida = tipo_variavel_atribuida['tipo'].values[0]
                            else:
                                # Verifico se é um valor
                                if nome_variavel_atribuida.isdigit():
                                    # Verifico se é inteiro ou flutuante
                                    tipo_variavel_atribuida = 'inteiro'

                                elif '.' in nome_variavel_atribuida:
                                    # É flutuante
                                    tipo_variavel_atribuida = 'flutuante'

                            variavel_declaracao_encontrada = ''
                            # Primeiro procuro no escopo local e depois no global
                            if nome_variavel_recebendo+escopo in nome_escopo_alocada:
                                # Pegar a posição onde se encontra esse valor e acessar as variaveis declaradas
                                variavel_declaracao_encontrada = variaveis_declaradas[nome_escopo_alocada.index(
                                    nome_variavel_recebendo+escopo)]

                            else:
                                if nome_variavel_recebendo+'global' in nome_escopo_alocada:
                                    variavel_declaracao_encontrada = variaveis_declaradas[nome_escopo_alocada.index(
                                        nome_variavel_recebendo+'global')]

                            # Verifica se o valor que está sendo atribuído é uma variável
                            valor_encontrado_atribuindo = encontra_variavel_declarada(
                                nome_variavel_atribuida)

                            if valor_encontrado_atribuindo == '':
                                # Significa que o valor que está sendo atribuído não é uma variável
                                if variavel_declaracao_encontrada != '':
                                    if tipo_variavel_atribuida == 'inteiro':
                                        builder.store(llvmir.Constant(llvmir.IntType(
                                            32), nome_variavel_atribuida), variavel_declaracao_encontrada)
                                    else:
                                        builder.store(llvmir.Constant(llvmir.FloatType(), float(
                                            nome_variavel_atribuida)), variavel_declaracao_encontrada)
                            else:
                                # Significa que o valor que está sendo atribuído é uma variável
                                variavel_temporaria = builder.load(
                                    valor_encontrado_atribuindo, "")
                                builder.store(variavel_temporaria,
                                              variavel_declaracao_encontrada)

                        # Significa que é uma atribuição com uma operação matemática
                        # Ou é uma atribuição em um vetor
                        else:
                            # É uma atribuição de um vetor
                            if no.children[1].label == '[':
                                # A[ i] := a
                                if len(no.children) == 6:
                                    nome_variavel_recebendo = encontra_variavel_declarada(
                                        no.children[0].label)

                                    # sempre vai ser uma variável
                                    posicao_array = no.children[2].label
                                    posicao_array_variavel = encontra_variavel_declarada(
                                        posicao_array)

                                    posicao_variavel_temporaria = builder.alloca(
                                        llvmir.IntType(32), name='pos_temp_1')
                                    builder.store(builder.load(posicao_array_variavel), builder.load(
                                        posicao_variavel_temporaria))

                                    valor_recebendo = no.children[5].label
                                    if valor_recebendo.isdigit():
                                        # recebe um digito
                                        # A[i]
                                        tipo_inteiro = llvmir.IntType(32)
                                        atribuicao_esquerda = builder.gep(nome_variavel_recebendo, [tipo_inteiro(
                                            0), tipo_inteiro(int(valor_recebendo))], name=str(no.children[0].label) + '_pos')

                                        # A[i] := a
                                        builder.store(
                                            atribuicao_esquerda, builder.load(valor_recebendo))
                                    else:
                                        # recebe uma variável
                                        valor_recebendo_declaracao = encontra_variavel_declarada(
                                            valor_recebendo)
                                        # A[i]
                                        tipo_inteiro = llvmir.IntType(32)
                                        atribuicao_esquerda = builder.gep(nome_variavel_recebendo, [tipo_inteiro(
                                            0), tipo_inteiro(posicao_variavel_temporaria)], name=str(no.children[0].label) + '_pos')

                                        # A[i] := a
                                        builder.store(builder.load(
                                            valor_recebendo_declaracao), builder.load(atribuicao_esquerda))

                            else:
                                # Pegar a variável que estará recebendo a operação
                                nome_variavel_recebendo = encontra_variavel_declarada(
                                    no.children[0].label)

                                # Verifica o primeira parametro da operação, para ver se é uma variável ou um digito
                                nome_variavel_atribuida_esquerda = no.children[2].label
                                operacao_sinal = no.children[3].label
                                nome_variavel_atribuida_direita = no.children[4].label

                                # Verifica para variável a esquerda da expressao (esquerda + direita)
                                if (nome_variavel_atribuida_esquerda.isdigit()):
                                    nome_variavel_atribuida_esquerda_declarada = llvmir.Constant(
                                        llvmir.IntType(32), name=nome_variavel_atribuida_esquerda)

                                else:
                                    nome_variavel_atribuida_esquerda_encontrada = encontra_variavel_declarada(
                                        nome_variavel_atribuida_esquerda)
                                    # Se não estiver nas variaveis é necessário pegar os parametros
                                    if nome_variavel_atribuida_esquerda_encontrada == '':
                                        nome_variavel_atribuida_esquerda = verifica_expressao_parametros(
                                            nome_variavel_atribuida_esquerda, escopo, parametros_lista)

                                        nome_variavel_atribuida_esquerda_encontrada = builder.alloca(
                                            llvmir.IntType(32), name='param')

                                        builder.store(
                                            nome_variavel_atribuida_esquerda, nome_variavel_atribuida_esquerda_encontrada)

                                    nome_variavel_atribuida_esquerda_declarada = builder.load(
                                        nome_variavel_atribuida_esquerda_encontrada, name='_temp')

                                # Verifica para variável a direita da expressao (esquerda + direita)
                                if (nome_variavel_atribuida_direita.isdigit()):
                                    nome_variavel_atribuida_direita_declarada = llvmir.Constant(
                                        llvmir.IntType(32), int(nome_variavel_atribuida_direita))

                                else:
                                    nome_variavel_atribuida_direita_declarada_encontrada = encontra_variavel_declarada(
                                        nome_variavel_atribuida_direita)
                                    if nome_variavel_atribuida_direita_declarada_encontrada == '':
                                        nome_variavel_atribuida_direita_declarada = verifica_expressao_parametros(
                                            nome_variavel_atribuida_direita)

                                        nome_variavel_atribuida_direita_declarada_encontrada = builder.alloca(
                                            llvmir.IntType(32), name='param')
                                        builder.store(nome_variavel_atribuida_direita_declarada_encontrada,
                                                      nome_variavel_atribuida_direita_declarada_encontrada)
                                        nome_variavel_atribuida_direita_declarada_encontrada = builder.load(
                                            nome_variavel_atribuida_direita_declarada_encontrada)

                                    nome_variavel_atribuida_direita_declarada = builder.load(
                                        nome_variavel_atribuida_direita_declarada_encontrada, name='_temp')

                                # Chama função que vai declarar a operação
                                operacao_declarada = realiza_operacoes(
                                    nome_variavel_atribuida_esquerda_declarada, nome_variavel_atribuida_direita_declarada, operacao_sinal)

                                builder.store(operacao_declarada,
                                              nome_variavel_recebendo)

        # Gera código da estrutura condicional se/senão
        elif (no.label == 'se'):
            tem_se = True

            # Tenho que procurar, utilizando o escopo atual, a declaração dessa função
            declaracao_funcao_encontrada = encontra_funcao_declarada(escopo)

            print(declaracao_funcao_encontrada)

            # Crio os blocos de entrada e saída do 'se'
            if declaracao_funcao_encontrada:
                if_verdade_1 = declaracao_funcao_encontrada.append_basic_block(
                    'iftrue_1')
                if_falso_1 = declaracao_funcao_encontrada.append_basic_block(
                    'iffalse_1')

                if_saida_1 = declaracao_funcao_encontrada.append_basic_block(
                    'ifend1')
                # Adiciono o bloco de saída na pilha
                print(if_saida_1, if_falso_1)

                pilha_bloco_saida.append(if_saida_1)
                pilha_bloco_saida.append(if_falso_1)

            # Tenho que carregar as variáveis para realizar a comparação
            comparacao_variavel_esquerda = encontra_variavel_declarada(
                no.children[0].label)
            comparacao_variavel_direita = llvmir.Constant(
                llvmir.IntType(32), int(no.children[2].label))

            if comparacao_variavel_esquerda:
                if len(no.children[1].children) > 0:
                    comparacao_operacao = builder.icmp_signed(str(no.children[1].children[0].label), builder.load(
                        comparacao_variavel_esquerda), comparacao_variavel_direita)
                else:
                    comparacao_operacao = builder.icmp_signed(str(no.children[1].label), builder.load(
                        comparacao_variavel_esquerda), comparacao_variavel_direita)

                builder.cbranch(comparacao_operacao, if_verdade_1, if_falso_1)

                builder.position_at_end(if_verdade_1)

        elif ('senão' == no.label):
            # posiciona para o if falso
            topo_bloco_saida = []
            bloco_falsidade = pilha_bloco_saida.pop()
            if len(pilha_bloco_saida) > 1:
                topo_bloco_saida = pilha_bloco_saida.pop()

            builder.branch(topo_bloco_saida)

            builder.position_at_end(bloco_falsidade)

            pilha_bloco_saida.append(topo_bloco_saida)

        elif ('fim' == no.label):
            if 'se' == no.parent.label:
                bloco_topo = pilha_bloco_saida.pop()
                saida_bloco_principal = []
                if len(saida_bloco_principal) > 1:
                    saida_bloco_principal = pilha_bloco_saida.pop()

                # branch do bloco falsidade para o bloco fim do if
                builder.branch(bloco_topo)
                if bloco_topo:
                    builder.position_at_end(bloco_topo)
                    builder.branch(saida_bloco_principal)

                pilha_bloco_saida.append(saida_bloco_principal)

        # Caso encontre o token Repita
        elif ('repita' == no.label):

            # Cria os blocos de repetição
            loop = builder.append_basic_block('loop')
            loop_validacao = builder.append_basic_block('loop_val')
            loop_end = builder.append_basic_block('loop_end')

            # Adiciona na pila de blocos finais
            pilha_loop_validacao.append(loop_validacao)
            pilha_loop.append(loop)
            pilha_bloco_saida.append(loop_end)

            # Pula para o laço do loop
            builder.branch(loop)

            # Posiciona no inicio do bloco do loop
            builder.position_at_end(loop)

        elif ('ATE' == no.label):
            validacao = pilha_loop_validacao.pop()
            builder.branch(validacao)

            builder.position_at_end(validacao)

            saida = pilha_bloco_saida.pop()
            loop_inicial = pilha_loop.pop()

            comparacao_esquerda, comparacao_sinal, comparacao_direita = procura_comparaca(
                no)

            if (comparacao_direita.isdigit()):
                # Declara o uma constante que será utilizada para comparação
                comparacao_valor = llvmir.Constant(
                    llvmir.IntType(32), int(comparacao_direita))

            # Procura a variável nas variáveis declaradas para realizar o load
            comparacao_variavel = encontra_variavel_declarada(
                comparacao_esquerda)

            if ('=' == comparacao_sinal):
                expressao = builder.icmp_signed('==', builder.load(
                    comparacao_variavel), comparacao_valor, name='expressao_igualdade')

            # Verifica se a expressão é verdadeira ou não
            builder.cbranch(expressao, loop_inicial, saida)

            # Define o que será executado após o fim do loop
            builder.position_at_end(saida)

        elif ('escreva' == no.label):
            # Verificar se vai ser necessário escrever qualquer coisa que não seja uma variável ou número, como uma expressaõ por exemplo
            valor_escrita = no.children[0].label

            tipo_variavel_escrita = tab_sym[tab_sym['lex'] == str(
                valor_escrita)]
            tipo_variavel_escrita = tipo_variavel_escrita['tipo'].values[0]

            if (valor_escrita.isdigit()):
                valor_escrita_constante = llvmir.Constant(
                    llvmir.IntType(32), int(valor_escrita))
                builder.call(escreva_inteiro, args=[valor_escrita_constante])

            else:
                # Significa que está escrevendo uma variável
                variavel_escrever = encontra_variavel_declarada(valor_escrita)
                if tipo_variavel_escrita == 'inteiro':
                    builder.call(escreva_inteiro, args=[
                                 builder.load(variavel_escrever)])
                else:
                    builder.call(escreva_float, args=[
                                 builder.load(variavel_escrever)])

        elif ('leia' == no.label):
            # Variável onde será guardado o conteúdo lido
            variavel_leia = no.children[0].label

            tipo_variavel_leitura = tab_sym[tab_sym['lex']
                                            == variavel_leia]
            tipo_variavel_leitura = tipo_variavel_leitura['tipo'].values[0]

            variavel_recebe_leitura = encontra_variavel_declarada(
                variavel_leia)

            if tipo_variavel_leitura == 'inteiro':
                leia_funcao_chamada = builder.call(leia_inteiro, args=[])
                builder.store(leia_funcao_chamada,
                              variavel_recebe_leitura, align=4)
            else:
                leia_funcao_chamada = builder.call(leia_float, args=[])
                builder.store(leia_funcao_chamada,
                              variavel_recebe_leitura, align=4)

        gera_codigo(no)


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
        root, tab_sym = retorna_arvore_tabela(source_file)

        global constructor

        binding.initialize()
        binding.initialize_all_targets()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

        # Cria módulo
        modulo = llvmir.Module('main.bc')
        modulo.triple = binding.get_process_triple()
        target = binding.Target.from_triple(modulo.triple)
        target_machine = target.create_target_machine()
        modulo.data_layout = target_machine.target_data

        escreva_inteiro_funcao = llvmir.FunctionType(
            llvmir.VoidType(), [llvmir.IntType(32)])
        escreva_inteiro = llvmir.Function(
            modulo, escreva_inteiro_funcao, "escrevaInteiro")

        escreva_float_funcao = llvmir.FunctionType(
            llvmir.VoidType(), [llvmir.FloatType()])
        escreva_float = llvmir.Function(
            modulo, escreva_float_funcao, "escrevaFlutuante")

        leia_inteiro_funcao = llvmir.FunctionType(llvmir.IntType(32), [])
        leia_inteiro = llvmir.Function(
            modulo, leia_inteiro_funcao, "leiaInteiro")

        leia_float_funcao = llvmir.FunctionType(llvmir.FloatType(), [])
        leia_float = llvmir.Function(
            modulo, leia_float_funcao, "leiaFlutuante")

        gera_codigo(root)
        arquivo = open('modulo_geracao_cod.ll', 'w')
        arquivo.write(str(modulo))
        arquivo.close()

        print('------------------------------------')
        print('Código gerado')
        print(modulo)
