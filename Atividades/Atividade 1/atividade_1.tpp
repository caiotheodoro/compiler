

{algoritmo de quick sort (funcao raiz)}
quick_sort(inteiro: list[])
    inteiro: first
    first:= 0

   quick_sort_helper(list,first, SIZE-1)
FIM

{metodo para ordenar o vetor}
quick_sort_helper(inteiro: list[], inteiro: first, inteiro: last)
    inteiro: split_point

    SE first < last ENTAO
        split_point := partition(list, first, last)
        quick_sort_helper(list, first, split_point-1)
        quick_sort_helper(list, split_point+1, last)
    FIM

FIM

{metodo para particionar o vetor}
inteiro partition(inteiro: list[], inteiro: first, inteiro: last)

    inteiro: pivot_value, leftmark, rightmark, temp
    pivot_value := list[first]
    leftmark := first+1
    rightmark := last

    REPITA
      
        REPITA 
            SE leftmark <= rightmark E list[leftmark] <= pivot_value ENTAO
                leftmark := leftmark + 1
            FIM
        ATE leftmark > rightmark OU list[leftmark] > pivot_value

        REPITA
            SE list[rightmark] >= pivot_value E rightmark >= leftmark ENTAO
                rightmark := rightmark - 1
            FIM
        ATE list[rightmark] < pivot_value OU rightmark < leftmark

        SE rightmark < leftmark ENTAO
            temp := list[first]
            list[first] := list[rightmark]
            list[rightmark] := temp
        SENAO
            temp := list[leftmark]
            list[leftmark] := list[rightmark]
            list[rightmark] := temp
        FIM
    ATE rightmark < leftmark

    return rightmark

FIM
    

{funcao principal}
inteiro main()
    inteiro: SIZE
    SIZE := 5
	inteiro: vector[SIZE] 
	arr := [5, 2, 1, 4, 3]

    quick_sort(arr)

    retorne 0
	
FIM