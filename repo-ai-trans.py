import os
import requests
from bs4 import BeautifulSoup

import openai

def translate_text(text, target_language):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"{text}\n\nTranslate the above text to {target_language}:",
        temperature=0.5,
        max_tokens=200
    )
    return response.choices[0].text.strip()

def replace_links(text, target_language):
    soup = BeautifulSoup(text, 'html.parser')
    for a in soup.find_all('a', href=True):
        if '/zh/' in a['href']:
            new_href = a['href'].replace('/zh/', '/' + target_language + '/')
            if requests.get(new_href).status_code == 200:
                a['href'] = new_href
            else:
                new_href = a['href'].replace('/zh/', '/en/')
                if requests.get(new_href).status_code == 200:
                    a['href'] = new_href
                else:
                    a['href'] = a['href'].replace('/zh/', '/')
    return str(soup)

def translate_file(original_path, target_path, target_language):
    with open(original_path, 'r', encoding='utf-8') as f:
        text = f.read()
    translated_text = translate_text(text, target_language)
    translated_text = replace_links(translated_text, target_language)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

if __name__ == '__main__':
    original_path = '../WTF-Solidity/01_HelloWeb3/readme.md'
    target_path = './WTF-Solidity/Languages/pt-br/01_HelloWeb3_pt-br/readme.md'
    target_language = 'pt-br'
    translate_file(original_path, target_path, target_language)
