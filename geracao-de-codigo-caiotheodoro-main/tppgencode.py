from myerror import MyError
from tppsema import retorna_arvore_tabela
import sys
import os
from utils import op_list, cria_modulo, var_aloca, func_aloca, cria_modulo, func_inicializa
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


global constructor
global modulo
global bloco_out
global varss
global escopo
global lista_escopo

global w_int
global w_float
global r_int
global r_float
global parametros_lista

root = None

escopo = ''
bloco_out = []
varss = []
lista_escopo = []
lista_declara_func = []
lista_escopo = []
parametros_lista = []


# função para realizar as operações aritméticas
def realiza_operacoes(param_func, exp_aux_temp, sinal_op):
    operacoes = {
        op_list[0]: constructor.sdiv,  # divisão inteira
        op_list[1]: constructor.add,  # soma
        op_list[2]: constructor.sub,  # subtração
        op_list[3]: constructor.mul,  # multiplicação
    }

    if sinal_op in operacoes:  # verifica se a operação é válida
        # retorna a operação realizada
        return operacoes[sinal_op](param_func, exp_aux_temp)

    return None


def encontra_expressao(expressao):  # função para encontrar a expressão

    for filhos_expressao in expressao.children:
        if len(filhos_expressao.children) > 0:  # verifica se o filho tem filhos
            # verifica se o filho é uma operação
            if filhos_expressao.children[0].label in op_list:
                return expressao.children[0].label, expressao.children[1].children[0].label, expressao.children[2].label
        else:
            if filhos_expressao.label in op_list:
                return expressao.children[0].label, expressao.children[1].label, expressao.children[2].label

    return None


# função para encontrar a variavel
def busca_var_escopo(nome_variavel):
    retorno = ''

    if nome_variavel+escopo in lista_escopo:  # verifica se a variavel está no escopo
        retorno = varss[lista_escopo.index(
            nome_variavel+escopo)]  # retorna a variavel encontrada
    else:  # caso não esteja no escopo
        if nome_variavel+'global' in lista_escopo:  # verifica se a variavel ta no escopo global
            retorno = varss[lista_escopo.index(
                nome_variavel+'global')]

    return retorno


# def processo_aloca(variavel, no, tab_sym, bloco_out, escopo, parametros_lista): # função para alocar a variavel
#     retorno = tab_sym[(tab_sym['lex'] == 'retorna') & (
#         tab_sym['linha'] == variavel)] if variavel and len(tab_sym['linha']) == len(variavel) else {} # verifica se a variavel existe
#     vals = retorno['valor'].values[0] if retorno else None

#     topo_bloco_saida = bloco_out.pop() # remove o topo do bloco de saida

#     if topo_bloco_saida:
#         constructor.position_at_end(topo_bloco_saida)

#     busca_ret = ''

#     if len(no.children) == 1: # verifica se o nó tem apenas um filho
#         if retorno:
#             if 'inteiro' == retorno['tipo'].values[0]:
#                 for ret in vals:
#                     for variavel_retornada, tipo_retornado in ret.items(): # percorre a lista de variaveis retornadas
#                         busca_ret = variavel_retornada # retorna a variavel encontrada
#             elif 'float' == retorno['tipo'].values[0]:
#                 pass

#         if busca_ret:
#             if busca_ret.isdigit():
#                 aux = llvmir.Constant(
#                     llvmir.IntType(32), variavel_retornada)
#                 constructor.ret(aux)
#             else:
#                 declaracao = busca_var_escopo(
#                     busca_ret)
#                 constructor.ret(constructor.load(declaracao, ""))

#     else:
#         exp, sinal_op, exp_aux = encontra_expressao(
#             no)

#         if exp.isdigit():
#             param_func = llvmir.Constant(
#                 llvmir.IntType(32), exp)
#             exp_aux_temp = llvmir.Constant(
#                 llvmir.IntType(32), exp_aux)
#         else:
#             param_func = []
#             funcao_tab_sym = tab_sym[(tab_sym['lex'] == escopo) & (
#                 tab_sym['funcao'] == '1')]
#             if funcao_tab_sym:
#                 parametros_funcao_tab_sym = funcao_tab_sym['parametros'].values[0]
#                 for param_tab_sym in parametros_funcao_tab_sym:
#                     for retorno_nome_tab_sym, _ in param_tab_sym.items():
#                         param_func.append(retorno_nome_tab_sym)

#             arg_param = parametros_lista.pop()

#             if exp in param_func:
#                 posicao_variavel = param_func.index(
#                     exp)
#                 param_func = arg_param.args[posicao_variavel]
#             else:
#                 variavel_exp = busca_var_escopo(
#                     exp)
#                 param_func = constructor.load(
#                     variavel_exp, name=str(exp) + '_temp')

#             if exp_aux in param_func:
#                 posicao_variavel_direita = param_func.index(
#                     exp_aux)
#                 exp_aux_temp = arg_param.args[posicao_variavel_direita]
#             else:
#                 variavel_exp_aux = busca_var_escopo(
#                     exp_aux)
#                 exp_aux_temp = constructor.load(
#                     variavel_exp_aux, name=str(exp_aux) + '_temp')

#         resultado_op = realiza_operacoes(
#             param_func, exp_aux_temp, sinal_op)
#         constructor.ret(resultado_op)


def gera_codigo(arvore):
    # global constructor
    # global modulo
    # global bloco_out
    # global varss
    # global escopo
    # global lista_escopo

    # global w_int
    # global w_float
    # global r_int
    # global r_float
    # global parametros_lista

    constructor = llvmir.IRBuilder()  # cria o construtor do llvm

    for no in arvore.children:  # percorre os filhos da arvore
        if ('declaracao_variaveis' in no.label):  # verifica se é uma declaração de variavel
            variavel = tab_sym[tab_sym['linha'] == no.label.split(
                ':')[1]]  # busca a variavel na tabela de simbolos
            var_aloca(no, modulo, constructor, variavel,
                      escopo, vars, lista_escopo)  # aloca a variavel
        elif ('declaracao_funcao' in no.label):
            variavel = no.label.split(':')[1] if len(
                no.label.split(':')) > 1 else None
            func_aloca(variavel, modulo, no, tab_sym, lista_escopo,
                       lista_declara_func, parametros_lista, bloco_out)  # aloca a função

        elif ('escreva' == no.label):  # verifica se é uma escrita
            valor_escrita = no.children[0].label  # busca o valor a ser escrito

            tipo_variavel_escrita = tab_sym[tab_sym['lex'] == str(
                valor_escrita)]  # busca o tipo da variavel a ser escrita
            # pega o tipo da variavel
            tipo_variavel_escrita = tipo_variavel_escrita['tipo'].values[0] if tipo_variavel_escrita else None

            if valor_escrita.isdigit():  # verifica se o valor a ser escrito é um numero
                valor_escrita_constante = llvmir.Constant(
                    llvmir.IntType(32), int(valor_escrita))  # aloca o valor como uma constante
                constructor.call(w_int, args=[
                                 valor_escrita_constante])  # chama a função de escrita

            else:
                variavel_escrever = busca_var_escopo(
                    valor_escrita)  # busca a variavel a ser escrita
                if tipo_variavel_escrita == 'inteiro':  # verifica se a variavel é do tipo inteiro
                    constructor.call(w_int, args=[
                        constructor.load(variavel_escrever)])  # chama a função de escrita
                else:
                    constructor.call(w_float, args=[
                        constructor.load(variavel_escrever)])  # chama a função de escrita

        elif ('leia' == no.label):  # verifica se é uma leitura
            variavel_leia = no.children[0].label

            tipo_variavel_leitura = tab_sym[tab_sym['lex'] == variavel_leia]
            tipo_variavel_leitura = tipo_variavel_leitura['tipo'].values[0]

            variavel_recebe_leitura = busca_var_escopo(
                variavel_leia)

            if tipo_variavel_leitura == 'inteiro':  # verifica se a variavel é do tipo inteiro
                leia_funcao_chamada = constructor.call(
                    r_int, args=[])  # chama a função de leitura
                constructor.store(leia_funcao_chamada,
                                  variavel_recebe_leitura, align=4)  # armazena o valor lido na variavel
            else:
                leia_funcao_chamada = constructor.call(
                    r_float, args=[])  # chama a função de leitura
                constructor.store(leia_funcao_chamada,
                                  variavel_recebe_leitura, align=4)  # armazena o valor lido na variavel

        gera_codigo(no)


def out_arq(modulo):
    with open('main.ll', 'w') as arquivo:
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
        root, tab_sym = retorna_arvore_tabela(source_file)

        binding.initialize()  # inicializa o binding do llvm
        binding.initialize_all_targets()  # inicializa os targets do llvm
        binding.initialize_native_target()  # inicializa o target nativo do llvm
        binding.initialize_native_asmprinter()  # inicializa o asmprinter do llvm

        modulo = cria_modulo()  # cria o modulo do llvm
        w_int, w_float, r_int, r_float = func_inicializa(
            modulo)  # inicializa as funções de escrita e leitura (serão usadas para a escrita e leitura de variaveis)

    gera_codigo(root)
    out_arq(modulo)
