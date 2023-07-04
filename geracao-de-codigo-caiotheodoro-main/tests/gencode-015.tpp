{Parametros de função}

inteiro func(inteiro: p1, inteiro: p2)
  inteiro: r
  r := p1 + p2
  retorna(r)
fim

inteiro principal()
  inteiro: x
  x := func(1,2)
  escreva(x)
  retorna(0)
fim

