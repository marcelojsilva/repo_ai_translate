import os
import requests
from bs4 import BeautifulSoup

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
