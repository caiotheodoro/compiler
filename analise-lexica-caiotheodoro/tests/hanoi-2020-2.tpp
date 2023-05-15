inteiro: count {Contador de Movimentos}
inteiro: quantidade {Numero de Discos}
{Funçao recursiva que movimenta os discos entre os pinos}
{Pino Origem = 0}
{ Pino Auxiliar = 1}
{Pino Destino = 2}
{Fonte: https://updatedcode.wordpress.com/2015/03/19/torre-de-hanoi-em-c/}
inteiro TorreHanoi(inteiro origem, inteiro destino, inteiro auxiliar, inteiro quantidade)
    se quantidade == 1 então
        count := coun+1
    senão
    	TorreHanoi(origem, auxiliar, destino, quantidade-1)
        TorreHanoi(origem, destino, auxiliar, 1)
        TorreHanoi(auxiliar, destino, origem, quantidade-1)
    fim
fim

inteiro principal()
    count := 0
    quantidade := 5
    TorreHanoi(0, 2, 1, quantidade)
    escreva(quantidade) {Quantidade de Discos}
    escreva(count)  {Numero de movimentos}
    retorna(0)
fim
