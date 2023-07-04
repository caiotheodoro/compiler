import pandas as pd


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
    'MAIOR']


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
]


def adiciona_no(no, nodes, auxiliar_arvore):
    for filho in nodes:
        if filho.name == no.name:
            auxiliar_arvore.extend(no.children)
        else:
            auxiliar_arvore.append(filho)


def retira_no(no_remover, tokens, nodes):
    auxiliar_arvore = []
    pai = no_remover.parent

    if no_remover.name in tokens or no_remover.name.split(':')[0] in tokens:
        for filho in pai.children:
            if filho.name != no_remover.name:
                auxiliar_arvore.append(filho)
            else:
                auxiliar_arvore.extend(no_remover.children)
        pai.children = auxiliar_arvore

    if no_remover.name in nodes or no_remover.name.split(':')[0] in nodes:
        if len(no_remover.children) == 0:
            for filho in pai.children:
                if filho.name != no_remover.name and filho.name.split(':')[0] != no_remover.name:
                    auxiliar_arvore.append(filho)
                else:
                    auxiliar_arvore.extend(no_remover.children)
            pai.children = auxiliar_arvore


def poda_arvore(arvore_abstrata, tokens, nodes):
    for no in arvore_abstrata.children:
        poda_arvore(no, tokens, nodes)
    retira_no(arvore_abstrata, tokens, nodes)


def aux_simbolos_tabela():
    return pd.DataFrame(data=[],
                        columns=symbol_table)


conv_tipo = {
    'NUM_INTEIRO': 'inteiro',
    'NUM_PONTO_FLUTUANTE': 'flutuante',
    'NUM_FLUTUANTE': 'flutuante'
}


def processa_numero(ret, retorno, ret_lista):
    indice = ret.children[0].children[0].label
    ret_tipo = ret.children[0].label
    ret_tipo = conv_tipo.get(ret_tipo)

    retorno[indice] = ret_tipo
    ret_lista.append(retorno)

    return ret_lista


def processa_id(ret, retorno, ret_lista):
    indice = ret.children[0].label
    ret_tipo = 'parametro'
    retorno[indice] = ret_tipo
    ret_lista.append(retorno)

    return ret_lista


def processa_parametro(param, tipo, nome):
    mapping = {
        'INTEIRO': (param.children[0].label, nome),
        'FLUTUANTE': (param.children[0].label, nome),
        'id': (tipo, param.children[0].label)
    }
    return mapping.get(param.label, (tipo, nome))


def aux_tipo(tipo):
    return conv_tipo.get(tipo)


def processa_tipo(filho):
    return filho.children[0].children[0].label


def processa_lista_parametros(filho):
    if filho.children[0].label == 'vazio':
        return 'vazio'
    else:
        return None


def processa_cabecalho(filho, nome_funcao):
    return filho.children[0].children[0].label, nome_funcao


def checa_declaracao_variavel(varss, var, tab_sym, error_handler):
    for _, row in varss.iterrows():
        declaracoes = tab_sym.loc[(tab_sym['lex'] == row['lex']) &
                                  (tab_sym['iniciacao'] == 'N') &
                                  (tab_sym['escopo'] == row['escopo'])]

    if len(declaracoes) > 1:
        print(error_handler.newError(
            'WAR-ALR-DECL', var['lex']))


def checa_inicializacao_variavel(tab_sym, var, error_handler):
    inicializacao_variaveis = tab_sym.loc[(tab_sym['lex'] == var['lex']) &
                                          (tab_sym['escopo'] == var['escopo']) &
                                          (tab_sym['iniciacao'] == 'S')]
    if len(inicializacao_variaveis) == 0:
        print(error_handler.newError(
            'WAR-SEM-VAR-DECL-NOT-USED', value=var['lex']))


def checa_retorno_funcao(tab_sym, error_handler):
    main_func = tab_sym.loc[(tab_sym['funcao'] == 'S') & (
        tab_sym['lex'] == 'principal')]
    if not main_func.empty:
        retorno_principal = tab_sym.loc[(tab_sym['funcao'] == 'S') &
                                        (tab_sym['escopo'] == 'principal') &
                                        (tab_sym['lex'] == 'retorna')]
        if retorno_principal.empty:
            print(error_handler.newError('ERR-RET-TIP-INCOMP'))
    else:
        print(error_handler.newError('ERR-SEM-MAIN-NOT-DECL'))


def checa_chamada_funcao(chamada, tab_sym, error_handler):
    declaracao_funcao = tab_sym.loc[(tab_sym['funcao'] == 'S') & (
        tab_sym['lex'] == chamada['lex'])]
    if declaracao_funcao.empty:
        print(error_handler.newError(
            'WAR-SEM-VAR-DECL-NOT-USED', value=chamada['lex']))
    else:
        qtd_params = len(chamada['parametros'])
        quantidade_parametros_declaracao = len(
            declaracao_funcao.iloc[0]['parametros'])
        if qtd_params != quantidade_parametros_declaracao:
            print(error_handler.newError(
                'ERR-PARAM-FUNC-INCOMP', value=chamada['lex']))
