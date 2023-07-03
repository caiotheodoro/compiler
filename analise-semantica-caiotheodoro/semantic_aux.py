def encontra_expressao_retorno(retorna, lista_retorno):
    retorno_dict = {}
    tipo_retorno = ''
    indice = ''

    def processa_numero(numero):
        indice = numero.children[0].children[0].label
        tipo_retorno = numero.children[0].label

        if tipo_retorno == 'NUM_INTEIRO':
            tipo_retorno = 'inteiro'
        elif tipo_retorno == 'NUM_FLUTUANTE':
            tipo_retorno = 'flutuante'

        retorno_dict[indice] = tipo_retorno
        lista_retorno.append(retorno_dict)

    def processa_id(id_node):
        indice = id_node.children[0].label
        tipo_retorno = 'parametro'

        retorno_dict[indice] = tipo_retorno
        lista_retorno.append(retorno_dict)

    def processa_ret(ret):
        nonlocal indice
        nonlocal tipo_retorno

        if ret.label == 'numero':
            processa_numero(ret)

        elif ret.label == 'ID':
            processa_id(ret)

        else:
            encontra_expressao_retorno(ret, lista_retorno)

    for ret in retorna.children:
        processa_ret(ret)

    return lista_retorno


def encontra_valores_retorno(retorna, retorno):
    def is_expression(label):
        expressions = ['expressao_aditiva', 'expressao_multiplicativa']
        return label in expressions

    for ret in retorna.children:
        if is_expression(ret.label):
            retorno = encontra_expressao_retorno(ret, retorno)
            return retorno

        encontra_valores_retorno(ret, retorno)

    return retorno


def encontra_atribuicao_valor(expressao, valores):
    valores_dict = {}
    tipo_retorno = ''

    def processa_numero(numero):
        indice = numero.children[0].children[0].label
        tipo_retorno = numero.children[0].label

        if tipo_retorno == 'NUM_INTEIRO':
            tipo_retorno = 'inteiro'
        elif tipo_retorno == 'NUM_PONTO_FLUTUANTE':
            tipo_retorno = 'flutuante'

        valores_dict[indice] = tipo_retorno
        valores.append(valores_dict)

    def processa_id(id_node):
        indice = id_node.children[0].label
        tipo_retorno = 'parametro'

        valores_dict[indice] = tipo_retorno
        valores.append(valores_dict)

    def processa_expressao(filho):
        nonlocal valores

        if filho.label == 'numero':
            processa_numero(filho)

        elif filho.label == 'ID':
            processa_id(filho)

        else:
            encontra_indice_retorno(filho)

    for filho in expressao.children:
        processa_expressao(filho)

    return tipo_retorno, valores


def encontra_tipo_nome_parametro(parametro, tipo, nome):
    def processa_inteiro(inteiro_node):
        tipo = inteiro_node.children[0].label
        return tipo, nome

    def processa_flutuante(flutuante_node):
        tipo = flutuante_node.children[0].label
        return tipo, nome

    def processa_id(id_node):
        nome = id_node.children[0].label
        return tipo, nome

    for param in parametro.children:
        if param.label == 'INTEIRO':
            return processa_inteiro(param)

        elif param.label == 'FLUTUANTE':
            return processa_flutuante(param)

        elif param.label == 'id':
            return processa_id(param)

        tipo, nome = encontra_tipo_nome_parametro(param, tipo, nome)

    return tipo, nome


def verifica_dimensoes(tree, dimensao, indice_1, indice_2):

    def processa_indice(indice_node):
        nonlocal dimensao
        nonlocal indice_1
        nonlocal indice_2

        dimensao = 1
        _, indice_1 = encontra_indice_retorno(indice_node.children[1])
        indice_2 = 0

        return dimensao, indice_1, indice_2

    def processa_indice_indice(indice_indice_node):
        nonlocal dimensao
        nonlocal indice_1
        nonlocal indice_2

        dimensao = 2
        _, indice_1 = encontra_indice_retorno(
            indice_indice_node.children[0].children[1])
        _, indice_2 = encontra_indice_retorno(indice_indice_node.children[2])

        return dimensao, indice_1, indice_2

    for filho in tree.children:
        if filho.label == 'indice':
            if filho.children[0].label == 'indice':
                return processa_indice_indice(filho)
            else:
                return processa_indice(filho)

        dimensao, indice_1, indice_2 = verifica_dimensoes(
            filho, dimensao, indice_1, indice_2)

    return dimensao, indice_1, indice_2


def atribuicao_expressao(expressao, valores):
    valores_dict = {}

    def processa_numero(numero):
        indice = numero.children[0].children[0].label
        tipo_retorno = numero.children[0].label

        if tipo_retorno == 'NUM_INTEIRO':
            tipo_retorno = 'inteiro'
        elif tipo_retorno == 'NUM_PONTO_FLUTUANTE':
            tipo_retorno = 'flutuante'

        valores_dict[indice] = tipo_retorno
        valores.append(valores_dict)

    def processa_id(id_node):
        indice = id_node.children[0].label
        tipo_retorno = 'parametro'

        valores_dict[indice] = tipo_retorno
        valores.append(valores_dict)

    def processa_expressao(filho):
        nonlocal valores

        if filho.label == 'numero':
            processa_numero(filho)

        elif filho.label == 'ID':
            processa_id(filho)

        else:
            atribuicao_expressao(filho, valores)

    for filho in expressao.children:
        processa_expressao(filho)

    return valores


def encontra_indice_retorno(expressao):
    def processa_numero(numero):
        indice = numero.children[0].children[0].label
        tipo_retorno = numero.children[0].label

        if tipo_retorno == 'NUM_INTEIRO':
            tipo_retorno = 'inteiro'
        elif tipo_retorno == 'NUM_PONTO_FLUTUANTE':
            tipo_retorno = 'flutuante'

        return tipo_retorno, indice

    def processa_id(id_node):
        indice = id_node.children[0].label
        tipo_retorno = 'parametro'

        return tipo_retorno, indice

    tipo_retorno = ''
    indice = ''

    for filho in expressao.children:
        if filho.label == 'numero':
            return processa_numero(filho)

        elif filho.label == 'ID':
            return processa_id(filho)

        tipo_retorno, indice = encontra_indice_retorno(filho)

    return tipo_retorno, indice


def encontra_atribuicao_valor(expressao, valores):
    def processa_numero(numero):
        indice = numero.children[0].children[0].label
        tipo_retorno = numero.children[0].label

        if tipo_retorno == 'NUM_INTEIRO':
            tipo_retorno = 'inteiro'
        elif tipo_retorno == 'NUM_PONTO_FLUTUANTE':
            tipo_retorno = 'flutuante'

        valores_dict[indice] = tipo_retorno
        valores.append(valores_dict)

    def processa_id(id_node):
        indice = id_node.children[0].label
        tipo_retorno = 'parametro'

        valores_dict[indice] = tipo_retorno
        valores.append(valores_dict)

    valores_dict = {}
    tipo_retorno = ''
    indice = ''

    for filho in expressao.children:
        if filho.label == 'numero':
            processa_numero(filho)

        elif filho.label == 'ID':
            processa_id(filho)

        tipo_retorno, indice = encontra_indice_retorno(filho)

    return tipo_retorno, valores


def verifica_dimensoes(tree, dimensao, indice_1, indice_2):
    def processa_indice(indice_node):
        dimensao = 1
        _, indice_1 = encontra_indice_retorno(indice_node.children[1])
        indice_2 = 0
        return dimensao, indice_1, indice_2

    def processa_indice_indice(indice_indice_node):
        dimensao = 2
        _, indice_1 = encontra_indice_retorno(
            indice_indice_node.children[0].children[1])
        _, indice_2 = encontra_indice_retorno(indice_indice_node.children[2])
        return dimensao, indice_1, indice_2

    for filho in tree.children:
        if filho.label == 'indice':
            if filho.children[0].label == 'indice':
                return processa_indice_indice(filho)
            else:
                return processa_indice(filho)

        dimensao, indice_1, indice_2 = verifica_dimensoes(
            filho, dimensao, indice_1, indice_2)

    return dimensao, indice_1, indice_2


def encontra_dados_funcao(declaracao_funcao, tipo=None, nome_funcao=None, parametros=None, retorno_tipo_valor=None, tipo_retorno=None, linha_retorno=None):
    if tipo is None:
        tipo = ""
    if nome_funcao is None:
        nome_funcao = ""
    if parametros is None:
        parametros = []
    if retorno_tipo_valor is None:
        retorno_tipo_valor = []
    if tipo_retorno is None:
        tipo_retorno = ""
    if linha_retorno is None:
        linha_retorno = ""

    global escopo

    for filho in declaracao_funcao.children:
        if filho.label == 'tipo':
            tipo = filho.children[0].children[0].label

        elif filho.label == 'lista_parametros':
            if filho.children[0].label == 'vazio':
                parametros = 'vazio'

        elif filho.label == 'cabecalho':
            nome_funcao = filho.children[0].children[0].label
            escopo = nome_funcao

        elif 'retorna' in filho.label:
            retorno_tipo_valor = encontra_valores_retorno(filho, [])
            linha_retorno = filho.label.split(':')[1]
            token = filho.children[0].label
            retorno = ''
            tipo_retorno = 'vazio'

            return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno

        tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno = encontra_dados_funcao(
            filho, tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno)

    return tipo, nome_funcao, parametros, retorno_tipo_valor, tipo_retorno, linha_retorno


def encontra_parametro_funcao(no, parametros):

    parametros = parametros
    parametro = {}

    for n in no.children:
        if (no.label == 'parametro'):
            tipo, nome = encontra_tipo_nome_parametro(no, '', '')

            parametro[nome] = tipo

            parametros.append(parametro)

            return parametros
        encontra_parametro_funcao(n, parametros)

    return parametros
