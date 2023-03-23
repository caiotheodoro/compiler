import os
import re
import sys

content = []
with open("utfpr-cm.html") as arquivo:
    content = arquivo.readlines()


def mountRegex(tag):
    return f'(<{tag}>([a-zA-Z0-9])*<{tag}/>)'

def findTags(regex):
    p = re.compile(regex)
    tags = p.search(content)
    return tags.group(1)
def main():
    if not sys.argv[1:]:
        print("Nenhuma tag informada.")
    else:
        regex = mountRegex(sys.argv[1])
        tags = findTags(regex) 
        print(tags)

main()
