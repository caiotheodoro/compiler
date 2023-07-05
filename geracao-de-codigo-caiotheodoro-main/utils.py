import pandas as pd
from llvmlite import binding
from llvmlite import ir as llvmir


def define_column(input, lexpos):
    begin_line = input.rfind("\n", 0, lexpos) + 1
    return (lexpos - begin_line) + 1


def auxiliar_p_parametro_error(p):
    if len(p) == 3:
        return define_column(p.lexer.lexdata, p.lexpos(0))

    elif len(p) == 4:
        return define_column(p.lexer.lexdata, p.lexpos(1))
    else:
        if p[2] == '(':
            return define_column(p.lexer.lexdata, p.lexpos(1))
        else:
            return define_column(p.lexer.lexdata, p.lexpos(2))


def get_parameter_error(character):
    if character == ':':
        return "Tipo"
    elif character == '[':
        return "Abre colchete"
    elif character == ']':
        return "Fecha colchete"
    else:
        return "Dois pontos"


def get_se_error(p):
    if len(p) == 6:
        if p[1] != 'se':
            return 'se', define_column(p.lexer.lexdata, p.lexpos(0))
        else:
            return 'então', define_column(p.lexer.lexdata, p.lexpos(2))
    else:
        if p[1] != 'se':
            return 'se', define_column(p.lexer.lexdata, p.lexpos(0))
        else:
            if p[3] != 'então':
                return 'então', define_column(p.lexer.lexdata, p.lexpos(2))
            else:
                return 'senão', define_column(p.lexer.lexdata, p.lexpos(4))


def caps(word):
    return word.upper()


nodes = ['se', 'corpo', 'retorna', 'escreva', 'repita', 'até', 'leia']

tokens = [
    'ID',
    'var',
    'lista_variaveis',
    'dois_pontos',
    'tipo',
    'INTEIRO',
    'NUM_INTEIRO',
    'lista_declaracoes',
    'declaracao',
    'indice',
    'numero',
    'fator',
    'abre_colchete',
    'fecha_colchete',
    'menos',
    'menor_igual',
    'maior_igual',
    'expressao',
    'DOIS_PONTOS',
    'expressao_logica',
    'ABRE_PARENTESE',
    'FECHA_PARENTESE',
    'MAIS',
    'chamada_funcao',
    'MENOS',
    'expressao_simples',
    'expressao_aditiva',
    'expressao_multiplicativa',
    'expressao_unaria',
    'inicializacao_variaveis',
    'ATRIBUICAO',
    'NUM_NOTACAO_CIENTIFICA',
    'LEIA',
    'abre_parentese',
    'fecha_parentese',
    'atribuicao',
    'fator',
    'cabecalho',
    'FIM',
    'operador_soma',
    'mais',
    'chamada_funcao',
    'lista_argumentos',
    'VIRGULA', 'virgula',
    'lista_parametros',
    'vazio',
    '(', ')',
    ':',
    ',',
    'FLUTUANTE',
    'NUM_PONTO_FLUTUANTE',
    'RETORNA',
    'ESCREVA',
    'SE',
    'ENTAO',
    'SENAO',
    'maior',
    'menor',
    'REPITA',
    'igual',
    'menos',
    'menor_igual',
    'maior_igual',
    'operador_logico',
    'operador_multiplicacao',
    'vezes',
    'id',
    'declaracao_variaveis',
    'atribuicao',
    'operador_relacional',
    'MAIOR']  # lista de tokens para poda


symbol_table = [
    'token',
    'lex',
    'tipo',
    'dimensao',
    "tamanho dimensional 1",
    'tamnho dimensional 2',
    'escopo',
    'iniciacao',
    'linha',
    'funcao',
    'parametros',
    'valor',
]  # tabela de simbolos

op_list = ['/', '+', '-', '*']
comp_list = ['<', '>']


def retira_no(no_remover, tokens, nodes):
    auxiliar_arvore = []
    pai = no_remover.parent

    # se for um token
    if no_remover.name in tokens or no_remover.name.split(':')[0] in tokens:
        for filho in pai.children:  # percorre os filhos do pai
            if filho.name != no_remover.name:  # se o filho for diferente do no que queremos remover
                # adiciona o filho na lista auxiliar
                auxiliar_arvore.append(filho)
            else:  # se o filho for igual ao no que queremos remover
                # adiciona os filhos do no que queremos remover na lista auxiliar
                auxiliar_arvore.extend(no_remover.children)
        pai.children = auxiliar_arvore  # o pai recebe a lista auxiliar

    # se for um no
    if no_remover.name in nodes or no_remover.name.split(':')[0] in nodes:
        if len(no_remover.children) == 0:  # se o no nao tiver filhos
            for filho in pai.children:  # percorre os filhos do pai
                # se o filho for diferente do no que queremos remover
                if filho.name != no_remover.name and filho.name.split(':')[0] != no_remover.name:
                    # adiciona o filho na lista auxiliar
                    auxiliar_arvore.append(filho)
                else:  # se o filho for igual ao no que queremos remover
                    # adiciona os filhos do no que queremos remover na lista auxiliar
                    auxiliar_arvore.extend(no_remover.children)
            pai.children = auxiliar_arvore  # o pai recebe a lista auxiliar


def poda_arvore(arvore_abstrata, tokens, nodes):  # funcao que poda a arvore
    for no in arvore_abstrata.children:
        poda_arvore(no, tokens, nodes)  # recursao para percorrer a arvore
    retira_no(arvore_abstrata, tokens, nodes)  # chama a funcao que retira o no


def aux_simbolos_tabela():
    return pd.DataFrame(data=[],
                        columns=symbol_table)  # cria um dataframe vazio com as colunas da tabela de simbolos


conv_tipo = {
    'NUM_INTEIRO': 'inteiro',
    'NUM_PONTO_FLUTUANTE': 'flutuante',
    'NUM_FLUTUANTE': 'flutuante'
}  # dicionario para converter o tipo do no para o tipo da tabela de simbolos


def processa_numero(ret, retorno, ret_lista):
    indice = ret.children[0].children[0].label  # pega o indice do no
    ret_tipo = ret.children[0].label  # pega o tipo do no
    # converte o tipo do no para o tipo da tabela de simbolos
    ret_tipo = conv_tipo.get(ret_tipo)

    # adiciona o tipo do no no dicionario de retorno
    retorno[indice] = ret_tipo
    # adiciona o dicionario de retorno na lista de retorno
    ret_lista.append(retorno)

    return ret_lista  # retorna a lista de retorno


def processa_id(ret, retorno, ret_lista):
    indice = ret.children[0].label  # pega o indice do no
    ret_tipo = 'parametro'  # define o tipo do no como parametro
    # adiciona o tipo do no no dicionario de retorno
    retorno[indice] = ret_tipo
    # adiciona o dicionario de retorno na lista de retorno
    ret_lista.append(retorno)

    return ret_lista


def processa_parametro(param, tipo, nome):
    mapping = {
        'INTEIRO': (param.children[0].label, nome),
        'FLUTUANTE': (param.children[0].label, nome),
        'id': (tipo, param.children[0].label)
    }  # dicionario para mapear o tipo do no para o tipo da tabela de simbolos
    # retorna o tipo e o nome do parametro
    return mapping.get(param.label, (tipo, nome))


def aux_tipo(tipo):  # funcao para converter o tipo do no para o tipo da tabela de simbolos
    return conv_tipo.get(tipo)


def processa_tipo(filho):
    return filho.children[0].children[0].label  # retorna o tipo do no


# funcao para processar a lista de parametros
def processa_lista_parametros(filho):
    if filho.children[0].label == 'vazio':
        return 'vazio'
    else:
        return None


# funcao para processar o cabecalho da funcao
def processa_cabecalho(filho, func_nome):
    return filho.children[0].children[0].label, func_nome


def checa_declaracao_variavel(varss, var, tab_sym, error_handler):
    for _, row in varss.iterrows():
        declaracoes = tab_sym.loc[(tab_sym['lex'] == row['lex']) &
                                  (tab_sym['iniciacao'] == '0') &
                                  (tab_sym['escopo'] == row['escopo'])]  # procura por declaracoes de variaveis

    if len(declaracoes) > 1:
        print(error_handler.newError(
            'WAR-ALR-DECL', var['lex']))  # se tiver mais de uma declaracao, printa o erro


def checa_inicializacao_variavel(tab_sym, var, error_handler):
    inicializacao_variaveis = tab_sym.loc[(tab_sym['lex'] == var['lex']) &
                                          (tab_sym['escopo'] == var['escopo']) &
                                          (tab_sym['iniciacao'] == '1')]  # procura por inicializacoes de variaveis
    if len(inicializacao_variaveis) == 0:  # se nao tiver inicializacao, printa o erro
        print(error_handler.newError(
            'WAR-SEM-VAR-DECL-NOT-USED', value=var['lex']))


# funcao para checar se a funcao tem retorno
def checa_retorno_funcao(tab_sym, error_handler):
    main_func = tab_sym.loc[(tab_sym['funcao'] == '1') & (
        tab_sym['lex'] == 'principal')]  # procura pela funcao principal
    if not main_func.empty:
        retorno_principal = tab_sym.loc[(tab_sym['funcao'] == '1') &
                                        (tab_sym['escopo'] == 'principal') &
                                        (tab_sym['lex'] == 'retorna')]  # procura pelo retorno da funcao principal
        if retorno_principal.empty:
            # se nao tiver retorno, printa o erro
            print(error_handler.newError('ERR-RET-TIP-INCOMP'))
    else:
        # se nao tiver funcao principal, printa o erro
        print(error_handler.newError('ERR-SEM-MAIN-NOT-DECL'))


def checa_chamada_funcao(chamada, tab_sym, error_handler):
    declara_func = tab_sym.loc[(tab_sym['funcao'] == '1') & (
        tab_sym['lex'] == chamada['lex'])]  # procura pela declaracao da funcao
    if declara_func.empty:
        print(error_handler.newError(
            'WAR-SEM-VAR-DECL-NOT-USED', value=chamada['lex']))  # se nao tiver declaracao, printa o erro
    else:
        qtd_params = len(chamada['parametros'])
        params_declaracao = len(
            declara_func.iloc[0]['parametros'])  # pega a quantidade de parametros da declaracao da funcao
        if qtd_params != params_declaracao:
            print(error_handler.newError(
                'ERR-PARAM-FUNC-INCOMP', value=chamada['lex']))  # se a quantidade de parametros for diferente, printa o erro


def instancia_llvm():
    llmv = binding.initialize()  # instancia o llvm
    llmv.initialize_native_target()  # inicializa o target
    llmv.initialize_native_asmprinter()   # inicializa o asm printer
    return llmv


def instancia_modulo(name):
    return llvmir.Module(name)  # instancia o modulo


def var_aloca(no, modulo, builder, variavel, escopo, vars, escopo_atual):
    lex_val = variavel['lex'].values[0]  # pega o lexema da variavel
    tipo_val = variavel['tipo'].values[0]  # pega o tipo da variavel
    # verifica se a variavel eh global
    # verifica se a variavel eh global
    global_val = (variavel['escopo'].values[0] == 'global')

    if tipo_val == 'inteiro':
        if global_val:
            if len(no.children) > 3:  # se for um vetor
                dim_1 = no.children[3].label  # pega a dimensao do vetor
                tipo_list = llvmir.ArrayType(
                    llvmir.IntType(32), int(dim_1))  # cria o tipo do vetor
                global_list = llvmir.GlobalVariable(
                    modulo, tipo_list, lex_val)
                global_list.initializer = llvmir.Constant(
                    tipo_list, None)  # inicializa o vetor
                global_list.linkage = "common"
                global_list.align = 4
                vars.append(global_list)
                escopo_atual.append(lex_val + 'global')
            else:
                global_var = llvmir.GlobalVariable(
                    modulo, llvmir.IntType(32), lex_val)  # cria a variavel global
                global_var.initializer = llvmir.Constant(
                    llvmir.IntType(32), 0)
                global_var.linkage = "common"
                global_var.align = 4
                vars.append(global_var)
                # adiciona a variavel no escopo atual
                escopo_atual.append(lex_val + 'global')
        else:
            variavel_declarada = builder.alloca(
                llvmir.IntType(32), name=lex_val)  # aloca a variavel
            variavel_declarada.initalizer = llvmir.Constant(
                llvmir.IntType(32), 0)  # inicializa a variavel
            variavel_declarada.linkage = "common"
            variavel_declarada.align = 4
            # adiciona a variavel na lista de variaveis
            vars.append(variavel_declarada)
            escopo_atual.append(lex_val + escopo)
    else:  # repete o processo para float
        if global_val:
            if len(no.children) > 3:
                dim_1 = no.children[3].label
                tipo_list = llvmir.ArrayType(
                    llvmir.FloatType(), int(dim_1))
                global_list = llvmir.GlobalVariable(
                    modulo, tipo_list, lex_val)
                global_list.initializer = llvmir.Constant(tipo_list, None)
                global_list.linkage = "common"
                global_list.align = 4
                vars.append(global_list)
                escopo_atual.append(lex_val + 'global')
            else:
                global_var = llvmir.GlobalVariable(
                    modulo, llvmir.FloatType(), lex_val)
                global_var.initializer = llvmir.Constant(
                    llvmir.FloatType(), 0.0)
                global_var.linkage = "common"
                global_var.align = 4
                vars.append(global_var)
                escopo_atual.append(lex_val + 'global')
        else:
            variavel_declarada = builder.alloca(
                llvmir.FloatType(), name=lex_val)
            variavel_declarada_constante = llvmir.Constant(
                llvmir.FloatType(), 0.0)
            builder.store(variavel_declarada_constante, variavel_declarada)
            variavel_declarada.linkage = "common"
            variavel_declarada.align = 4
            vars.append(variavel_declarada)
            escopo_atual.append(lex_val + escopo)


def func_aloca(variavel, modulo, no, tab_sym, lista_escopo, lista_declara_func, parametros_lista, pilha_out_bloco):
    f_func = tab_sym[tab_sym['linha'] == variavel] if variavel and len(
        tab_sym['linha']) == len(variavel) else None  # pega a funcao da tabela de simbolos

    func_cria = llvmir.FunctionType(llvmir.IntType(32), [])  # cria a funcao
    if 'inteiro' == no.children[0].label:  # se o tipo da funcao for inteiro
        if f_func is not None:
            # pega os parametros da funcao
            params = f_func['parametros'].values[0]
            if len(params) == 0:
                func_cria = llvmir.FunctionType(llvmir.IntType(32), ())
            elif len(params) == 1:
                func_cria = llvmir.FunctionType(
                    llvmir.IntType(32), llvmir.IntType(32))
            else:
                tipo_params = [llvmir.IntType(32)
                               for _ in range(len(params))]
                func_cria = llvmir.FunctionType(
                    llvmir.IntType(32), tipo_params)

    func_nome = 'main' if (
        f_func is not None and f_func['lex'].values[0] == 'principal') else f_func['lex'].values[0]  # pega o nome da funcao
    declara_func = llvmir.Function(
        modulo, func_cria, name=func_nome)  # declara a funcao
    lista_declara_func.append(declara_func)
    lista_escopo.append(func_nome)

    # pega os parametros da funcao
    params_func = f_func['parametros'].values[0] if f_func is not None else ''
    params = 0
    for param in params_func:  # adiciona os parametros na funcao
        for param_nome, _ in param.items():
            declara_func.args[params].name = param_nome
            params += 1

    parametros_lista.append(declara_func)  # adiciona os parametros na lista
    in_bloco = declara_func.append_basic_block('entry')
    out_bloco = declara_func.append_basic_block('exit')

    pilha_out_bloco.append(out_bloco)


def cria_modulo():
    modulo = llvmir.Module('main.bc')  # cria o modulo
    modulo.triple = binding.get_process_triple()  # pega a arquitetura do processador
    target = binding.Target.from_triple(modulo.triple)  # cria o target
    target_machine = target.create_target_machine()  # cria a maquina virtual
    modulo.data_layout = target_machine.target_data  # cria o layout de dados
    return modulo


def func_inicializa(modulo):
    escreva_inteiro_funcao = llvmir.FunctionType(
        llvmir.VoidType(), [llvmir.IntType(32)])  # cria a funcao de escrever inteiro
    # declara a funcao de escrever inteiro
    w_int = llvmir.Function(modulo, escreva_inteiro_funcao, "w_int_var")

    escreva_float_funcao = llvmir.FunctionType(
        llvmir.VoidType(), [llvmir.FloatType()])  # cria a funcao de escrever float
    # declara a funcao de escrever float
    w_float = llvmir.Function(modulo, escreva_float_funcao, "w_float_var")

    leia_inteiro_funcao = llvmir.FunctionType(
        llvmir.IntType(32), [])  # cria a funcao de ler inteiro
    # declara a funcao de ler inteiro
    r_int = llvmir.Function(modulo, leia_inteiro_funcao, "r_int_var")

    leia_float_funcao = llvmir.FunctionType(
        llvmir.FloatType(), [])  # cria a funcao de ler float
    # declara a funcao de ler float

    # declara a funcao de ler float
    leia_float = llvmir.Function(modulo, leia_float_funcao, "r_float_var")

    return w_int, w_float, r_int, leia_float
