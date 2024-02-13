import os
import requests
import shutil
import sys
import glob
from openai import OpenAI
import re

def translate_text(text, prompt):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"{prompt}",
            },
            {
                "role": "user",
                "content": f"{text}",
            }
        ],
        model="gpt-3.5-turbo-16k",
        max_tokens=4096,
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return chat_completion.choices[0].message.content.strip()

def replace_links(text, target_language, original_language):
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
            return match.group(1) + url.replace(f'{os.getenv("REPO_NAME")}/blob/main', '..').replace('.md', f'_{target_language}.md') + match.group(3)
        else:
            return match.group(1) + url + match.group(3)

    # Replace all links in the text
    return re.sub(r'(\[.*?\]\()(.*?)(\))', replacer, text)

def translate_file(original_file_path, target_file_path, target_language):
    with open(original_file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    prompt = f'Translate text to {target_language}'
    translated_text = translate_text(text, prompt)
    translated_text = replace_links(translated_text, target_language, original_language)
    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
    with open(target_file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)
        f.write("\n\n<!-- This file was translated using AI by repo_ai_translate. For more information, visit https://github.com/marcelojsilva/repo_ai_translate -->")

def copy_non_translated_files(original_path, target_path):
    files = glob.glob(os.path.join(original_path, '**/*'), recursive=True)
    files = [f for f in files if not f.startswith(os.path.join(original_path, 'Languages'))]
    for file in files:
        if not file.endswith('.md') and not os.path.isdir(file) and not is_programming_file(file) and not file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico')):
            # Get the relative path difference
            rel_path = os.path.relpath(file, original_path)
            # Create the same directory structure in the target path
            target_file_path = os.path.join(target_path, rel_path)
            if os.path.exists(target_file_path):
                continue
            os.makedirs(os.path.dirname(file), exist_ok=True)
            shutil.copy(file, target_file_path)

def is_programming_file(filename):
    # List of common programming language extensions
    programming_extensions = ['.sol', '.py', '.js', '.java', '.c', '.cpp', '.cs', '.rb', '.go', '.php', '.swift', '.html', '.css', '.sql']

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # Check if the extension is in the list of programming extensions
    return extension in programming_extensions

def add_translation_link(target_file_path, target_language):
    with open(target_file_path, 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:4]):
            if '](readme_' in line:
                language = line.split('](readme_')[1].split('.md')[0]
                new_line = line.replace(f'](readme_{language}.md', f'](readme_{target_language}.md')
                lines[i] = new_line
                break
        else:
            # If no link to a translated readme is found, generate one using OpenAI
            link_text = translate_text(f"Read this document in {target_language}:", f'Translate text to {target_language}')
            new_line = f"[{link_text}](readme_{target_language}.md)\n"
            lines.insert(0, new_line)
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def translate_comments(original_file, target_file, original_language, target_language):
    with open(original_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Regular expression to match comments and common log commands in the original language
    comment_regex = re.compile(r'//.*|/\*.*?\*/|<!--.*?-->|#.*|\'\'\'.*?\'\'\'|\"\"\".*?\"\"\"|console\.log\(.*\)|print\(.*\)|System\.out\.println\(.*\)', re.DOTALL)
    i = 0
    while i < len(lines):
        comment = ""
        end_line = i
        # If the comment is a multiline comment, get all lines
        if lines[i].lstrip().startswith(('/*', '"""', "'''", '<!--')):
            comment += lines[end_line]
            while not comment.rstrip().endswith(('*/', '"""', "'''", '-->')):
                end_line += 1
                comment += lines[end_line]
        match = comment_regex.search(lines[i])
        if match and 'SPDX-License-Identifier:' not in lines[i]:
            comment = match.group()
        if comment:
            prompt = f'Translate the text if the text has any part in \'{original_language}\', if so, translate the entire text to \'{target_language}\', else keep the original text. (DO NOT INCLUDE ANYTHING OTHER THAN THE TRANSLATED TEXT. LEAVE COMMENTS CHARACTERS, ESCAPE CHARACTERS AND SPACES. DO NOT INCLUDE ANY PART OF THE ROLE SYSTEM CONTENT).'
            translated_comment = translate_text(comment, prompt)
            # Fix start and end of translated comments
            if not translated_comment.startswith(('#', '/*', '*/', '//', '"""', "'''", '<!--', '-->')) and not translated_comment.startswith(('console.log(', 'print(', 'System.out.println(')):
                translated_comment = f'{comment[:2]} {translated_comment}'
            translated_comment_lines = translated_comment.split('\n')
            if not translated_comment.endswith('\n'):
                translated_comment += '\n'
            for j in range(i, len(translated_comment_lines) + i):
                lines[j] = ' ' * (len(lines[j]) - len(lines[j].lstrip())) + translated_comment_lines[j - i].lstrip() + '\n'
            i = end_line
        i += 1

    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)


if __name__ == '__main__':
    original_language = sys.argv[1]
    target_language = sys.argv[2]
    original_path = sys.argv[3]
    target_path = os.path.join(sys.argv[4], target_language)
    md_files = glob.glob(os.path.join(original_path, '**/*.md'))
    for md_file in md_files:
        relative_path = os.path.relpath(md_file, original_path)
        target_file_path = os.path.join(target_path, relative_path.replace('.md', f'_{target_language}.md'))
        # Check if the file exists in the target language
        if os.path.exists(target_file_path):
            continue
        translate_file(md_file, target_file_path, target_language)

    copy_non_translated_files(original_path, target_path)

    programming_files = [file for file in glob.glob(os.path.join(original_path, '**/*'), recursive=True) if is_programming_file(file)]
    programming_files = [f for f in programming_files if not f.startswith(os.path.join(original_path, 'Languages'))]

    for programming_file in programming_files:
        relative_path = os.path.relpath(programming_file, original_path)
        target_file_path = os.path.join(target_path, relative_path)
        if os.path.exists(target_file_path):
            continue
        translate_comments(programming_file, target_file_path, original_language, target_language)
