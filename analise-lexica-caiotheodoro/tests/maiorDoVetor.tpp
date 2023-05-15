inteiro maiorvetor(inteiro:v[], inteiro:tam)
	inteiro: maior
	maior := v[0]
	inteiro i:= 0
	repita
		se v[i] > maior
			maior := v[i]
		i := i +1
	ate i = 5
	retorna maior

inteiro main()
	inteiro v[5] := {1,2,3,4,5}
	inteiro maior := maiorvetor(v,5)
	escreva (maior)