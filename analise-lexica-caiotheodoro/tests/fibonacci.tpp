
fibonacci(inteiro: n)
	inteiro: i
	inteiro: j
	inteiro: k
	
	i := 0
	j := 1
	k := 1	
	
	repita
		k := k+1
		inteiro: t
		t := i + j
		i := j
		j := t
	até k <= n	
	retorna j
fim

inteiro principal ()
	inteiro: n
	leia(n)
	fibonacci(n)
	retorna(0)
fim


