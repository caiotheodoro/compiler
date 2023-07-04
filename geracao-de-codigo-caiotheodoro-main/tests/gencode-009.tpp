flutuante: A[10]
flutuante: B[10]
flutuante: C[10]

somaVetores(inteiro: n)
    inteiro: i
    i := 0
    repita
        C[i] := A[i] + B[i]
        i := i + 1
    até i = n 
fim

inteiro principal()
    inteiro: i
    i := 0
    repita
        A[i] := 1
        B[i] := 1
        i := i + 1
    até i = 10

    somaVetores(10)

    i := 0
    repita
        escreva(C[i])
        i := i + 1
    até i = 10

    retorna(0)
fim
