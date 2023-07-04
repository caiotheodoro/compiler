# Aluno: Caio Eduardo Theodoro da Silva
## RA: 2044560


import re
import sys


def read_file(filename):  # leitura do arquivo
    with open(filename, "r", encoding="utf-8") as file:
        return file.readlines()


def mountRegex(tag):  # montagem do regex a partir da tag
    tagType = tag.split()[0]
    return r"<" + tag + r">(.*)</" + tagType + r">"


# operação de regex encima do arquivo, retornando o conteudo da tag
def getContentFromTag(regex):

    for line in content:
        match = re.search(regex, line)
        if match:
            return match.group(1).strip()


content = read_file("utfpr-cm.html")


def __main__():

    if not sys.argv[1:]:
        print("Nenhuma tag informada.")
    else:

        tag = " ".join(sys.argv[1:])  # junta os args da tag
        regex = mountRegex(tag)  # monta o regex
        print(getContentFromTag(regex))  # retorna o conteudo da tag


if __name__ == "__main__":
    __main__()


# Exemplo de execução:
# python extract.py span class='"menuTrigger"'
# python extract.py div class='"menu"'
