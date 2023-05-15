somar(inteiro: n[10])
    inteiro: soma
    inteiro: i
    i := 0
    soma := 0
    repita
        soma := n[i] + soma
        i := i + 1
    ate i = 10
    retorna(soma)
fim


inteiro Principal()
    
    inteiro: vet[10]
    inteiro: i
    i := 0

    repita
        leia(vet[i])
        i := i + 1
    ate i = 10

    inteiro: total

    total := somar(vet)
    escreva(total)

    retorna(0)
fim