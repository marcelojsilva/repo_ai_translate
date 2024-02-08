import os
import requests
import shutil
import sys
import glob
from openai import OpenAI

def translate_text(text, target_language):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"{text}\n\nTranslate the above text to {target_language}:",
            }
        ],
        model="gpt-3.5-turbo",
    )
    
    return chat_completion.choices[0].message.content.strip()
    # return '---\ntitle: 4. Funções de Retorno\ntags:\n  - solidity\n  - básico\n  - wtfacademy\n  - return\n---\n\n# WTF Solidity Básico: 4. Funções de Retorno\n\nEu tenho estudado Solidity recentemente para reforçar os detalhes e escrever um tutorial "WTF Solidity Básico" para iniciantes (desenvolvedores experientes podem procurar outro tutorial). Serão lançadas de 1 a 3 aulas por semana.\n\nTwitter: [@0xAA_Science](https://twitter.com/0xAA_Science)\n\nComunidade: [Discord](https://discord.gg/5akcruXrsk)｜[Grupo do WhatsApp](https://docs.google.com/forms/d/e/1FAIpQLSe4KGT8Sh6sJ7hedQRuIYirOoZK_85miz3dw7vA1-YjodgJ-A/viewform?usp=sf_link)｜[Site wtf.academy](https://wtf.academy)\n\nTodo o código e tutoriais são de código aberto no GitHub: [github.com/AmazingAng/WTFSolidity](https://github.com/AmazingAng/WTFSolidity)\n\n-----\n\nNesta aula, vamos falar sobre funções de retorno no Solidity, incluindo: retornar múltiplos valores, retornar com nomes e utilizar atribuição destrutiva para ler todos ou alguns dos valores de retorno.\n\n## Valores de Retorno: return e returns\n\nNo Solidity, existem duas palavras-chave relacionadas às funções de retorno: `return` e `returns`. Elas têm as seguintes diferenças:\n\n- `returns`: é adicionado ao final da declaração da função para declarar o tipo e o nome das variáveis de retorno.\n- `return`: utilizado no corpo da função para retornar os valores especificados.\n\n```solidity\n// Retorna múltiplos valores\nfunction returnMultiple() public pure returns(uint256, bool, uint256[3] memory){\n    return(1, true, [uint256(1),2,5]);\n}\n```\n\nNo código acima, utilizamos a palavra-chave `returns` para declarar a função `returnMultiple()` que retorna múltiplos valores. Em seguida, no corpo da função, utilizamos o `return(1, true, [uint256(1),2,5])` para retornar esses valores.\n\nO tipo de `uint256[3]` declara um array com comprimento 3 e do tipo `uint256` como retorno. Como `[1,2,3]` seria considerado como `uint8(3)` por padrão, precisamos fazer um cast para `uint256` no primeiro elemento do array para declarar que todos os elementos desse array são do tipo `uint256`. Os valores do retorno do tipo array devem ser sempre declarados como `memory`. Falaremos mais sobre o armazenamento de variáveis e escopos na próxima aula [5. Armazenamento de Dados](../05_DataStorage/readme.md).\n\n## Retorno com Nomes\n\nPodemos declarar o nome das variáveis de retorno utilizando a palavra-chave `returns`. O Solidity irá inicializar essas variáveis e automaticamente retornar seus valores, sem a necessidade de utilizar `return`.\n\n```solidity\n// Retorno com nomes\nfunction returnNamed() public pure returns(uint256 _number, bool _bool, uint256[3] memory _array){\n    _number = 2;\n    _bool = false;\n    _array = [uint256(3),2,1];\n}\n```\n\nNo código acima, utilizamos `returns(uint256 _number, bool _bool, uint256[3] memory _array)` para declarar os tipos e nomes das variáveis de retorno. Dessa forma, no corpo da função, só precisamos atribuir valores para `_number`, `_bool` e `_array` e eles serão automaticamente retornados.\n\nÉ possível também utilizar o `return` para retornar os valores:\n\n```solidity\n// Retorno com nomes, retorna utilizando return\nfunction returnNamed2() public pure returns(uint256 _number, bool _bool, uint256[3] memory _array){\n    return(1, true, [uint256(1),2,5]);\n}\n```\n\n## Atribuição Destrutiva\n\nO Solidity suporta atribuição destrutiva para ler todos ou alguns dos valores de retorno de uma função.\n\n- Para ler todos os valores de retorno: declare as variáveis e separe-as por vírgulas, na mesma ordem que são retornados.\n\n    ```solidity\n    uint256 _number;\n    bool _bool;\n    uint256[3] memory _array;\n    (_number, _bool, _array) = returnNamed();\n    ```\n\n- Para ler apenas alguns valores de retorno: declare apenas as variáveis correspondentes aos valores que deseja ler e deixe as outras variáveis vazias. No exemplo abaixo, só estamos interessados em `_bool`, portanto, não declaramos as variáveis correspondentes a `_number` e `_array`:\n\n    ```solidity\n    (, _bool2, ) = returnNamed();\n    ```\n\n## Executando no Remix\n\n- Deploy o contrato e verifique os resultados das três formas de retorno\n\n    ![4-1.png](./img/4-1.png)\n\n## Conclusão\n\nNesta aula, falamos sobre funções de retorno no Solidity, incluindo: retornar múltiplos valores, retornar com nomes e utilizar atribuição destrutiva para ler todos ou alguns dos valores de retorno. Esses conhecimentos nos ajudam a lidar de forma mais flexível com os valores de retorno ao escrever contratos inteligentes.'
import re

def replace_links(text, target_language):
    def replacer(match):
        url = match.group(2)
        if '/zh/' in url:
            new_url = url.replace('/zh/', '/' + target_language + '/')
            if requests.get(new_url).status_code == 200:
                return match.group(1) + new_url + match.group(3)
            else:
                new_url = url.replace('/zh/', '/en/')
                if requests.get(new_url).status_code == 200:
                    return match.group(1) + new_url + match.group(3)
                else:
                    return match.group(1) + url.replace('/zh/', '/') + match.group(3)
        return match.group(0)

    return re.sub(r'(\[.*?\]\()(/zh/.*?)(\))', replacer, text)

def copy_images(text, original_path, target_path):
    matches = re.findall(r'!\[.*?\]\((.*?)\)', text)
    for match in matches:
        original_image_path = os.path.join(os.path.dirname(original_path), match)
        target_image_path = os.path.join(os.path.dirname(target_path), match)
        os.makedirs(os.path.dirname(target_image_path), exist_ok=True)
        shutil.copyfile(original_image_path, target_image_path)

def translate_file(original_path, target_path):
    with open(original_path, 'r', encoding='utf-8') as f:
        text = f.read()
    translated_text = translate_text(text, target_language)
    translated_text = replace_links(translated_text, target_language)
    copy_images(translated_text, original_path, target_path)
    target_path = os.path.join(target_path, os.path.basename(original_path).replace('.md', '_' + target_language + '.md'))
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

def copy_non_md_files(original_path, target_path):
    files = glob.glob(os.path.join(original_path, '*'))
    for file in files:
        if not file.endswith('.md'):
            shutil.copy(file, target_path)

if __name__ == '__main__':
    original_path = sys.argv[1]
    target_path = os.path.join(sys.argv[2], 'pt-br')
    target_language = sys.argv[3]
    copy_non_md_files(original_path, target_path)
    md_files = glob.glob(os.path.join(original_path, '*.md'))
    for md_file in md_files:
        translate_file(md_file, target_path, target_language)
