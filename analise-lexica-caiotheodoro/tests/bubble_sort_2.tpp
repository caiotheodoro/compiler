inteiro: a[100]
inteiro: b[100]
inteiro: c[100]

inteiro[] bubble_sort(inteiro: n[], inteito tam)
	inteiro: i
	inteiro: j
	inteiro: aux
	i := 0
	j := 1
	repita
		repita
			se a[i] > a[j] então
				aux = a[i]
				a[i] = a[j]
				a[j] = aux
				j = j + 1
		até j < tam
		i = i + 1
	até i < tam
retorna a
fim

inteiro principal()
	inteiro: tamanho
	tamanho := 100
	escreva (bubble_sort(a,tamanho))
	retorna (0)
fim



