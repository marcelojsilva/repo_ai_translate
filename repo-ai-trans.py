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
            else:
                # If the link does not exist, return the original link
                return match.group(1) + url + match.group(3)
        # If the link is to a file in the repo, replace to relative path
        if f'{os.getenv("REPO_NAME")}/blob/main' in url: 
            return match.group(1) + url.replace(f'{os.getenv("REPO_NAME")}/blob/main', '.') + match.group(3)
        else:
            return match.group(1) + url + match.group(3)

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
        f.write("\n\n<!-- This file was translated using AI by repo_ai_translate. For more information, visit https://github.com/marcelojsilva/repo_ai_translate -->")

def copy_non_md_files(original_path, target_path):
    files = glob.glob(os.path.join(original_path, '**/*'), recursive=True)
    for file in files:
        if not file.endswith('.md') and not os.path.isdir(file):
            # Get the relative path difference
            rel_path = os.path.relpath(file, original_path)
            # Create the same directory structure in the target path
            target_file_path = os.path.join(target_path, rel_path)
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            shutil.copy(file, target_file_path)

def is_programming_file(filename):
    # List of common programming language extensions
    programming_extensions = ['.sol', '.py', '.js', '.java', '.c', '.cpp', '.cs', '.rb', '.go', '.php', '.swift', '.html', '.css', '.sql']

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # Check if the extension is in the list of programming extensions
    return extension in programming_extensions

def add_translation_link(md_file, target_path, target_language):
    target_file_path = os.path.join(target_path, md_file.replace('.md', '_' + target_language + '.md'))
    with open(target_file_path, 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:4]):
            if '](readme_' in line:
                language = line.split('](readme_')[1].split('.md')[0]
                new_line = line.replace(f'](readme_{language}.md', f'](readme_{target_language}.md')
                lines[i] = new_line
                break
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def translate_comments(file_path, target_language):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Regular expression to match comments in the original language
    comment_regex = re.compile(r'//.*|/\*.*\*/|<!--.*-->|#.*|\'\'\'.*\'\'\'|\"\"\".*\"\"\"')

    for i, line in enumerate(lines):
        match = comment_regex.search(line)
        if match:
            comment = match.group()
            translated_comment = translate_text(comment, target_language)
            lines[i] = line.replace(comment, translated_comment)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == '__main__':
    target_language = sys.argv[1]
    original_path = sys.argv[2]
    target_path = os.path.join(sys.argv[3], target_language)
    copy_non_md_files(original_path, target_path)
    md_files = glob.glob(os.path.join(original_path, '*.md'))
    for md_file in md_files:
        translate_file(md_file, target_path, target_language)
        if md_file.lower() == 'readme.md':
            add_translation_link(md_file, target_path, target_language)

    programming_files = [file for file in glob.glob(os.path.join(original_path, '**/*'), recursive=True) if is_programming_file(file)]
    for programming_file in programming_files:
        translate_comments(programming_file, target_language)
