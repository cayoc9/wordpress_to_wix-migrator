import sys
import os
import html

# Adiciona o diretório raiz do projeto ao sys.path para permitir a importação de módulos
# O script está em 'testes/', então subimos um nível para a raiz do projeto.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.extractors.wordpress_extractor import _parse_taxonomy_field

def run_tests():
    """Executa os testes da função _parse_taxonomy_field."""
    
    # Definição dos casos de teste
    test_cases = [
        {
            'name': 'Separação por vírgula',
            'input': 'Geral, Notícias',
            'expected': ['Geral', 'Notícias']
        },
        {
            'name': 'Separação por pipe',
            'input': 'Tecnologia|Inovação',
            'expected': ['Tecnologia', 'Inovação']
        },
        {
            'name': 'Mistura de delimitadores',
            'input': 'Geral, Análises|Opinião',
            'expected': ['Geral', 'Análises', 'Opinião']
        },
        {
            'name': 'Validação Crítica (não separar por &)',
            'input': 'Tecnologia & Inovação',
            'expected': ['Tecnologia & Inovação']
        },
        {
            'name': 'Entidades HTML',
            'input': 'Dicas & Truques',
            'expected': ['Dicas & Truques']
        },
        {
            'name': 'Espaços extras',
            'input': '  Geral ,   Notícias  ',
            'expected': ['Geral', 'Notícias']
        },
        {
            'name': 'Itens vazios',
            'input': 'Geral,,Notícias| |Opinião',
            'expected': ['Geral', 'Notícias', 'Opinião']
        },
        {
            'name': 'String vazia',
            'input': '',
            'expected': []
        },
        {
            'name': 'Valor None simulado',
            'input': None,
            'expected': []
        }
    ]
    
    print("Iniciando testes da função _parse_taxonomy_field...\n")
    
    # Itera sobre os casos de teste
    for i, test_case in enumerate(test_cases, 1):
        input_value = test_case['input']
        expected = test_case['expected']
        name = test_case['name']
        
        # Chama a função com o valor de entrada
        try:
            if input_value is None:
                # Simula o comportamento da função com None
                result = _parse_taxonomy_field(input_value)
            else:
                result = _parse_taxonomy_field(input_value)
        except Exception as e:
            print(f"Teste {i}: {name}")
            print(f"  Entrada: {input_value}")
            print(f"  Erro na execução: {e}")
            print(f"  Resultado Obtido: ERRO")
            print(f"  Resultado Esperado: {expected}")
            print(f"  Status: FAIL\n")
            continue
            
        # Compara o resultado com o esperado
        status = "PASS" if result == expected else "FAIL"
        
        print(f"Teste {i}: {name}")
        print(f"  Entrada: {input_value}")
        print(f"  Resultado Esperado: {expected}")
        print(f"  Resultado Obtido: {result}")
        print(f"  Status: {status}\n")

if __name__ == "__main__":
    run_tests()