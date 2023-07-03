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
'VIRGULA','virgula',
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


def retira_no(no, tokens, nodes):
    auxiliar_arvore = []
    pai = no.parent

    if no.name in tokens or no.name.split(':')[0] in tokens:
        for filho in pai.children:
            if filho.name == no.name:
                auxiliar_arvore.extend(no.children)
            else:
                auxiliar_arvore.append(filho)
        pai.children = auxiliar_arvore

    elif no.name in nodes or no.name.split(':')[0] in nodes:
        if len(no.children) == 0:
            adiciona_no(pai.children, no, auxiliar_arvore)
            pai.children = auxiliar_arvore


def poda_arvore(arvore_abstrata, tokens, nodes):
    for no in arvore_abstrata.children:
        poda_arvore(no, tokens, nodes)
    retira_no(arvore_abstrata, tokens, nodes)


def aux_simbolos_tabela():
    return pd.DataFrame(data=[],
                        columns=symbol_table)