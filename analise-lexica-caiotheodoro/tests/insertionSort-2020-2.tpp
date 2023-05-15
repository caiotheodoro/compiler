inteiro: n
n := 10
inteiro: a[n]

inteiro insertionSort(inteiro: vet[], inteiro: tam)
    inteiro: i
    inteiro: chave
    inteiro: j

    i := 1
    repita
        chave := vet[i]
        j := i - 1

        repita
            vet[j+1] := vet[j]
            j := j-1     
        até j>=0 && vet[j] > chave 

        vet[j+1] = chave
        
        i := i+1
    até i < n



