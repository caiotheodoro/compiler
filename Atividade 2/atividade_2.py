## Aluno: Caio Eduardo Theodoro da Silva
## RA: 2044560

import re

regex = re.compile(r'([a-zA-Z0-9]+[.-_])*[a-zA-Z0-9]+@[a-zA-Z0-9-]+[\.a-z|A-Z]{2,}')

# [a-zA-Z0-9]+ - verifica se há 1 ou mais caracteres de a á z, A á Z e 0 á 9
# [.-_])* - verifica se há 0 ou mais caracteres 
def verificaEmail(email):
    if re.fullmatch(regex,email):
        return email


with open("emails.txt", "r") as arquivo:
    lines = arquivo.readlines()

newLines = []
for line in lines:
    email = line.split('<')[1].split('>')[0]
    if verificaEmail(email):
        newLines.append(line.split('<')[1].split('>')[0])

with open("new_list.txt", "w") as novoArquivo:
    for newLine in newLines:
        novoArquivo.write(f'{newLine}\n')
