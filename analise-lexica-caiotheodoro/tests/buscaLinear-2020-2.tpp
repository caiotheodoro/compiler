
inteiro: A[20]

inteiro busca(inteiro: e)
	
	inteiro: retorno
	inteiro: i

	retorno := 0
	i := 0

	repita 
		se A[i] = e
			retorno := 1
		fim		
		i := i + 1
	até i = 20

	retorna(retorno)
fim

inteiro principal()
	inteiro: e
	inteiro: i

	i := 0

	repita 
		A[i] := i
		i := i + 1
	até i = 20

	leia(e)
	escreva(busca(e))
	retorno(0)
fim