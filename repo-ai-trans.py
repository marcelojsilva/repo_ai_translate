import os
import requests
import shutil
import sys
import glob
from openai import OpenAI
import re

original_language = os.getenv('ORIGINAL_LANGUAGE')
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

def replace_links(text, target_language):
    def replacer(match):
        url = match.group(2)
        # Check if the link is in the original language
        if f'/{original_language}/' in url:
            new_url = url.replace(f'/{original_language}/', f'/{target_language}/')
            # If the new link exists, return it
            if requests.get(new_url).status_code == 200:
                return match.group(1) + new_url + match.group(3)
            new_url = url.replace(f'/{original_language}/', '/en/')
            # If the 'en' link exists, return it
            if requests.get(new_url).status_code == 200:
                return match.group(1) + new_url + match.group(3)
            new_url = url.replace(f'/{original_language}/', '/')
            # If the link without language exists, return it
            if requests.get(new_url).status_code == 200:
                return match.group(1) + new_url + match.group(3)
        # If the link is not in the original language, replace the repo name with '.'
        return match.group(1) + url.replace(f'{os.getenv("REPO_NAME")}/blob/main', '.') + match.group(3)

    # Replace all links in the text
    return re.sub(r'(\[.*?\]\()(.*?)(\))', replacer, text)

def copy_images(text, original_path, target_path):
    matches = re.findall(r'!\[.*?\]\((.*?)\)', text)
    for match in matches:
        original_image_path = os.path.join(os.path.dirname(original_path), match)
        target_image_path = os.path.join(os.path.dirname(target_path), match)
        os.makedirs(os.path.dirname(target_image_path), exist_ok=True)
        shutil.copyfile(original_image_path, target_image_path)

def translate_file(md_file, original_path, target_path):
    original_file_path = os.path.join(original_path, md_file)
    target_file_path = os.path.join(target_path, md_file.replace('.md', '_' + target_language + '.md'))
    with open(original_file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    translated_text = translate_text(text, target_language)
    translated_text = replace_links(translated_text, target_language)
    copy_images(translated_text, original_file_path, target_file_path)
    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
    with open(target_file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

def copy_non_md_files(original_path, target_path):
    files = glob.glob(os.path.join(original_path, '**/*'), recursive=True)
    for file in files:
        if not file.endswith('.md') and not os.path.isdir(file):
            shutil.copy(file, target_path)

if __name__ == '__main__':
    target_language = sys.argv[1]
    original_path = sys.argv[2]
    target_path = os.path.join(sys.argv[3], target_language)
    copy_non_md_files(original_path, target_path)
    md_files = glob.glob(os.path.join(original_path, '*.md'))
    for md_file in md_files:
        translate_file(md_file, target_path, target_language)
