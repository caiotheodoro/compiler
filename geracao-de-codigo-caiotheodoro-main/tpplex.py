from ply.lex import TOKEN
import ply.lex as lex
from sys import argv, exit
from utils import define_column
import logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="lex.log",
    filemode="w",
    format="%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()


tokens = [
    # identificador
    "ID",
    # numerais
    "NUM_NOTACAO_CIENTIFICA",   # ponto flutuante em notaçao científica
    "NUM_PONTO_FLUTUANTE",      # ponto flutuate
    "NUM_INTEIRO",              # inteiro
    # operadores binarios
    "MAIS",                     # +
    "MENOS",                    # -
    "MULTIPLICACAO",            # *
    "DIVISAO",                  # /
    "E_LOGICO",                 # &&
    "OU_LOGICO",                # ||
    "DIFERENCA",                # <>
    "MENOR_IGUAL",              # <=
    "MAIOR_IGUAL",              # >=
    "MENOR",                    # <
    "MAIOR",                    # >
    "IGUAL",                    # =
    # operadores unarios
    "NEGACAO",                  # !
    # simbolos
    "ABRE_PARENTESE",           # (
    "FECHA_PARENTESE",          # )
    "ABRE_COLCHETE",            # [
    "FECHA_COLCHETE",           # ]
    "VIRGULA",                  # ,
    "DOIS_PONTOS",              # :
    "ATRIBUICAO",               # :=
]

reserved_words = {
    "se": "SE",
    "então": "ENTAO",
    "senão": "SENAO",
    "fim": "FIM",
    "repita": "REPITA",
    "flutuante": "FLUTUANTE",
    "retorna": "RETORNA",
    "até": "ATE",
    "leia": "LEIA",
    "escreva": "ESCREVA",
    "inteiro": "INTEIRO",
}


tokens = tokens + list(reserved_words.values())

digito = r"([0-9])"
letra = r"([a-zA-ZáÁãÃàÀéÉíÍóÓõÕ])"
sinal = r"([\-\+]?)"

""" 
    id deve começar com uma letra
"""
id = (
    r"(" + letra + r"(" + digito + r"+|_|" + letra + r")*)"
)  # o mesmo que '((letra)(letra|_|([0-9]))*)'

# inteiro = r"(" + sinal + digito + r"+)"
# inteiro = r"(" + digito + r"+)"
inteiro = r"\d+"

flutuante = (
    # r"(" + digito + r"+\." + digito + r"+?)"
    # (([-\+]?)([0-9]+)\.([0-9]+))'
    r'\d+[eE][-+]?\d+|(\.\d+|\d+\.\d*)([eE][-+]?\d+)?'
    # r'[-+]?[0-9]+(\.([0-9]+)?)'
    # r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?'
    # r"(([-\+]?)([0-9]+)\.([0-9]+))"
)

notacao_cientifica = (
    r"(" + sinal + r"([1-9])\." + digito + r"+[eE]" + sinal + digito + r"+)"
)  # o mesmo que '(([-\+]?)([1-9])\.([0-9])+[eE]([-\+]?)([0-9]+))'

# Expressões Regulaes para tokens simples.
# Símbolos.
t_MAIS = r'\+'
t_MENOS = r'-'
t_VEZES = r'\*'
t_DIVIDE = r'/'
t_ABRE_PARENTESE = r'\('
t_FECHA_PARENTESE = r'\)'
t_ABRE_COLCHETE = r'\['
t_FECHA_COLCHETE = r'\]'
t_VIRGULA = r','
t_ATRIBUICAO = r':='
t_DOIS_PONTOS = r':'

# Operadores Lógicos.
t_E = r'&&'
t_OU = r'\|\|'
t_NAO = r'!'

# Operadores Relacionais.
t_DIFERENTE = r'<>'
t_MENOR_IGUAL = r'<='
t_MAIOR_IGUAL = r'>='
t_MENOR = r'<'
t_MAIOR = r'>'
t_IGUAL = r'='


@TOKEN(id)
def t_ID(token):
    token.type = reserved_words.get(token.value, "ID")
    # não é necessário fazer regras/regex para cada palavra reservada
    # se o token não for uma palavra reservada automaticamente é um id
    # As palavras reservadas têm precedências sobre os ids

    return token


@TOKEN(notacao_cientifica)
def t_NUM_NOTACAO_CIENTIFICA(token):
    return token


@TOKEN(flutuante)
def t_NUM_PONTO_FLUTUANTE(token):
    return token


@TOKEN(inteiro)
def t_NUM_INTEIRO(token):
    return token


t_ignore = " \t"


# t_COMENTARIO = r'(\{((.|\n)*?)\})'
# para poder contar as quebras de linha dentro dos comentarios
def t_COMENTARIO(token):
    r"(\{((.|\n)*?)\})"
    token.lexer.lineno += token.value.count("\n")
    # return token


def t_newline(token):
    r"\n+"
    token.lexer.lineno += len(token.value)


def t_error(token):

    # file = token.lexer.filename
    line = token.lineno
    #
    column = define_column(token.lexer.lexdata, token.lexpos)
    message = "Erro[%s,%s]: Caracter inválido '%s'" % (
        token.lineno, column, token.lexpos)

    # print(f"[{file}]:[{line},{column}]: {message}.")
    print(message)

    token.lexer.skip(1)

    # token.lexer.has_error = True


def main():
    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
        raise IOError("Not a .tpp file!")
    data = open(argv[1])

    source_file = data.read()
    lexer.input(source_file)

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break      # No more input
        # print(tok)
        print(tok.type)
        # print(tok.value)


def test(pdata):
    data = open(pdata)
    source_file = data.read()
    lexer.input(source_file)

    s = ""

    while True:
        tok = lexer.token()
        if not tok:
            break      # No more input
        s += str(tok.type) + '\n'

    return s


# Build the lexer.
lexer = lex.lex(optimize=True, debug=True, debuglog=log)

if __name__ == "__main__":
    main()
