
inteiro principal()

  inteiro: t1
  inteiro: t2
  inteiro: t3

  t1 := 0
  t2 := 1
  t3 := 1

  escreva(t1)

  repita
    escreva(t3)
    t3 := t1 + t2
    t1 := t2
    t2 := t3
  até t3 >= 100
fim