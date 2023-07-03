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
    '(',
    ')',
    ':',
    ',',
    'id',
    'lista_parametros',
    'var',
    'tipo',
    'dois_pontos',
    'numero',
    'cabecalho',
    'vazio',
    'declaracao',
    'lista_declaracoes',
    'atribuicao',
    'expressao',
    'expressao_logica',
    'expressao_simples',
    'expressao_aditiva',
    'expressao_multiplicativa',
    'expressao_unaria',
    'operador_relacional',
    'operador_logico',
    'operador_negacao',
    'fator',
    'lista_variaveis',
    'abre_colchete',
    'senão',
    'então',
    'fecha_colchete',
    'indice',
    'chamada_funcao',
    'lista_argumentos',
    'operador_soma',
    'MAIS',
    'MENOS',
    'virgula',
    'VIRGULA',
    'ESCREVA',
    'SE',
    'MAIOR',
    'ENTAO',
    'REPITA',
    'ATE',
    'IGUAL',
    'LEIA',
    'SENAO',
    'ID',
    'ABRE_PARENTESE',
    'FECHA_PARENTESE',
    'FIM',
    'NUM_INTEIRO',
    'NUM_PONTO_FLUTUANTE',
    'RETORNA',
    'INTEIRO',
    'FLUTUANTE',
    'ATRIBUICAO',
]

symbol_table = [
    'Token',
    'Lexema',
    'Tipo',
    'Escopo',
    'Linha',
    'Coluna',
    'Parametros',
    'Retorno',
    'Tamanho',
    'Valor',
    'Funcao',
]


def retira_no(no, tree):
    tree.children.remove(no)  # remove o nó da árvore
    # adiciona os filhos do nó removido ao pai do nó removido
    tree.children.extend(no.children)


def gera_poda(root):
    def poda_aux_rec(no):
        for child in no.children:  # percorre os filhos do nó
            # chama a função recursivamente para cada filho
            poda_aux_rec(child)

        if no.name in nodes and not no.children:  # se o nó for um dos nós da lista e não tiver filhos
            retira_no(no, no.parent)

    poda_aux_rec(root)
    return root


def aux_simbolos_tabela():
    return pd.DataFrame(data=[],
                        columns=symbol_table)
