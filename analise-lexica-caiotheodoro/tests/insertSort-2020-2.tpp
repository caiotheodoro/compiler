{ insertion sort }

inteiro: i, j, x, tam
inteiro: vet[10]

tam := 10

{ implementação do insertion sort }
insert_sort()
  i := 2
  repita
    x := vet[i]
    j := i - 1
    vet[0] := x

    se x < vet[j] então
      repita
        vet[j+1] := vet[j]
        j := j - 1
      até x < vet[j]
    fim
  
    vet[j+1] := x

    i := i + 1
  até i <= tam
fim

{ implementação da funcao para imprimir o vetor }
printArray()
  inteiro: p
    p := 0
    repita
      escreva(vet[p])
    até p < tam
fim

inteiro principal()

  { preenche o vetor }
  inteiro: z
	z := 0
	repita 
		vet[z] := z
		z := z + 1
	até z < tam

  { chama a funcao insertion sort }
  insert_sort()

  { chama a funcao para imprimir }
  printArray()

  retorna(0)
fim