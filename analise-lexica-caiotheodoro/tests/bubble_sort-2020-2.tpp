flutuante: A[20]

bubbleSort(inteiro: n)
    inteiro: i
    inteiro: j
    
    i := 0
    j := 0

    repita
        repita
            se A[j] > A[j+1] então
                inteiro: aux

                aux := A[j]
                A[j] := A[j+1]
                A[j+1] := aux
            fim

            j := j + 1
        até j = (n-i-1)

        i := i + 1
    até i = n
fim


inteiro principal()
    inteiro: i
    i := 20
    repita
        A[i - 1] := i
        i := i - 1
    até i = 0

    bubbleSort(20)
fim

