import tpplex
import subprocess
import os, fnmatch

def execute_test(input_file):
    path_file = 'tests/' + input_file
    process = subprocess.Popen(['python', 'tpplex.py', path_file],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout, stderr

    output_file = open(path_file + ".out", "r")

    #read whole file to a string
    expected_output = output_file.read()

    output_file.close()

    print(stdout)
    print(expected_output)

    return stdout.decode("utf-8") == expected_output

#def testes():
#    for file in fnmatch.filter(os.listdir('tests'), '*.tpp'):
#        assert execute_test(file) == True

def test_001():
    assert execute_test("teste-001.tpp") == True

def test_002():
    assert execute_test("teste-002.tpp") == True

def test_003():
    assert execute_test("teste-003.tpp") == True

def test_004():
    assert execute_test("bubble_sort-2020-2.tpp") == True

def test_005():
    assert execute_test("bubble_sort_2.tpp") == True

def test_006():
    assert execute_test("bubble_sort.tpp") == True

def test_007():
    assert execute_test("Busca_Linear_1061992.tpp") == True

def test_008():
    assert execute_test("buscaLinear-2020-2.tpp") == True

def test_009():
    assert execute_test("comp.tpp") == True

def test_010():
    assert execute_test("fatorial-2020-2.tpp") == True

def test_011():
    assert execute_test("fatorial.tpp") == True

def test_012():
    assert execute_test("fat.tpp") == True

def test_013():
    assert execute_test("fibonacci-2020-2.tpp") == True

def test_014():
    assert execute_test("fibonacci.tpp") == True

def test_015():
    assert execute_test("hanoi-2020-2.tpp") == True

def test_016():
    assert execute_test("insertionSort-2020-2.tpp") == True

def test_017():
    assert execute_test("insertSort-2020-2.tpp") == True

def test_018():
    assert execute_test("maiorDoVetor.tpp") == True

def test_019():
    assert execute_test("multiplicavetor.tpp") == True

def test_020():
    assert execute_test("operacao_vetor-2020-2.tpp") == True

def test_021():
    assert execute_test("paraBinario-2020-2.tpp") == True

def test_022():
    assert execute_test("primo.tpp") == True

def test_023():
    assert execute_test("produtoEscalar.tpp") == True

def test_024():
    assert execute_test("prog_test.tpp") == True

def test_025():
    assert execute_test("sample.tpp") == True

def test_026():
    assert execute_test("selectionSort-2020-2.tpp") == True

def test_027():
    assert execute_test("selectionsort.tpp") == True

def test_028():
    assert execute_test("soma_maior_que_3.tpp") == True

def test_029():
    assert execute_test("somavet.tpp") == True

def test_030():
    assert execute_test("subtraiVetores.tpp") == True

def test_031():
    assert execute_test("verifica_valor_10.tpp") == True

def test_032():
    assert execute_test("verif_num_negativo.tpp") == True
