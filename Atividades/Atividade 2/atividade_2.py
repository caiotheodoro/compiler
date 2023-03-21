# Aluno: Caio Eduardo Theodoro da Silva
## RA: 2044560

import re

regex = re.compile(
    r'([a-zA-Z0-9]+[.-_])*[a-zA-Z0-9]+@[a-zA-Z0-9-]+[\.a-z|A-Z]{2,}')

# ([a-zA-Z0-9] -> Primeiro caractere do email, verifica se há alguma letra de a-z,  A-Z, ou 0-9
# [.-_] -> Verifica se há um caractere especial, como ., -, ou _
# )* -> Indica que o grupo ([a-zA-Z0-9][.-_])  pode ser repetido 0 ou mais vezes, por exemplo, a.b.cde.f.g ...@ etc
# [a-zA-Z0-9]+ -> indica que antes do @ deve haver pelo menos um caractere, previnindo casos como a.@gmail.com
# @ -> Verifica se há um @
# [a-zA-Z0-9-]+ -> Verifica se há mais de um caractere a-z,  A-Z, ou 0-9 depois do @
# [\.a-z|A-Z]-> Verifica se há pelo menos um . , e após letras de a-z, A-Z
# {2,} -> Verifica se ha dois ou mais caracteres. exemplo,  .com, .com.br, .br


def verificaEmail(email): # Função que verifica se o email é válido
    if re.fullmatch(regex, email): # faz o match total das regras do regex com o email fornecido, retorna o email se for valido
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
