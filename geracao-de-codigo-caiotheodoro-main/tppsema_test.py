import tpplex
import subprocess
import os, fnmatch

def execute_test(input_file):
    path_file = 'tests/' + input_file
    process = subprocess.Popen(['python', 'tppsema.py', path_file],
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
    assert execute_test("sema-001.tpp") == True

def test_002():
    assert execute_test("sema-002.tpp") == True

def test_003():
    assert execute_test("sema-003.tpp") == True

def test_004():
    assert execute_test("sema-004.tpp") == True

def test_005():
    assert execute_test("sema-005.tpp") == True

def test_006():
    assert execute_test("sema-006.tpp") == True

def test_007():
    assert execute_test("sema-007.tpp") == True

def test_008():
    assert execute_test("sema-008.tpp") == True

def test_009():
    assert execute_test("sema-009.tpp") == True

def test_010():
    assert execute_test("sema-010.tpp") == True

def test_011():
    assert execute_test("sema-011.tpp") == True

def test_012():
    assert execute_test("sema-012.tpp") == True

def test_013():
    assert execute_test("sema-013.tpp") == True

def test_014():
    assert execute_test("sema-014.tpp") == True

def test_015():
    assert execute_test("sema-015.tpp") == True

def test_016():
    assert execute_test("sema-016.tpp") == True

def test_017():
    assert execute_test("sema-017.tpp") == True

def test_018():
    assert execute_test("sema-018.tpp") == True

def test_019():
    assert execute_test("sema-019.tpp") == True

def test_020():
    assert execute_test("sema-020.tpp") == True
