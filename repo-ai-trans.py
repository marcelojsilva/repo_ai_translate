import os
import requests
import shutil
import sys
import glob
from openai import OpenAI
import re

MAX_TOKENS = 4096

def translate_text(text, prompt):
    messages = [
        {
            "role": "system",
            "content": f"{prompt}",
        },
        {
            "role": "user",
            "content": f"{text}.",
        }
    ]
    count = 0
    history = ""
    while True:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-16k",
            max_tokens=MAX_TOKENS,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        count += 1
        content = chat_completion.choices[0].message.content.strip()
        if chat_completion.usage.completion_tokens < MAX_TOKENS or count == 2:
            history += content
            break

        last_sentence = content.splitlines()[-1:]
        content_without_last_sentence, _, _ = content.rpartition(last_sentence[0])
        history += content_without_last_sentence
        messages.append({
                "role": "assistant",
                "content": f"{content}",
            })
        messages.append({
                "role": "user",
                "content": f"Continue replace from {last_sentence}"
            })
    return history 

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
            return match.group(1) + url.replace(f'{os.getenv("REPO_NAME")}/blob/main', '..') + match.group(3)
        elif f'{os.getenv("REPO_NAME")}/tree/main' in url: 
            return match.group(1) + url.replace(f'{os.getenv("REPO_NAME")}/tree/main', '..') + match.group(3)
        else:
            return match.group(1) + url + match.group(3)

    # Replace all links in the text
    return re.sub(r'(\[.*?\]\()(.*?)(\))', replacer, text)

def translate_file(original_file_path, target_file_path, original_language, target_language):
    with open(original_file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    prompt = f'Translate the text above to \'{target_language}\'. Don\'t keep anything in \'{original_language}\'.'
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
        if not file.endswith('.md') and not os.path.isdir(file) and not is_programming_file(file):
            # Get the relative path difference
            rel_path = os.path.relpath(file, original_path)
            # Create the same directory structure in the target path
            target_file_path = os.path.join(target_path, rel_path)
            if os.path.exists(target_file_path):
                continue
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            shutil.copy(file, target_file_path)

def is_programming_file(filename):
    # List of common programming language extensions
    programming_extensions = ['.sol', '.py', '.js', '.java', '.c', '.cpp', '.cs', '.rb', '.go', '.php', '.swift', '.html', '.css', '.sql']

    # Get the file extension
    _, extension = os.path.splitext(filename)

    # Check if the extension is in the list of programming extensions
    return extension in programming_extensions

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

def check_broken_links(path):
    md_files = glob.glob(os.path.join(path, '**/*.md'), recursive=True)
    broken_links = []
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        links = re.findall(r'\[(.*?)\]\((.*?)\)', content)
        exclude = ['https://twitter.com', 'https://x.com']
        for link_text, link in links:
            # check if the link start with exclude list
            if any(link.startswith(e) for e in exclude):
                continue
            
            if link.startswith('http'):
                try:
                    response = requests.get(link, timeout=10)
                    if response.status_code not in (200, 401, 402, 403):
                        broken_links.append((md_file, link_text, link, response.status_code))
                except (requests.ConnectionError, requests.Timeout):
                    broken_links.append((md_file, link_text, link, 'Connection error'))
            # Check the link is a valid local file
            elif link.startswith(('/', '.')):
                local_file_path = os.path.join(os.path.dirname(md_file), link)
                if not os.path.exists(local_file_path):
                    broken_links.append((md_file, link_text, link))
    return broken_links

def get_file_size(file_path):
    return os.path.getsize(file_path) / 1024

if __name__ == '__main__':
    original_language = sys.argv[1]
    target_language = sys.argv[2]
    original_path = sys.argv[3]
    target_path = os.path.join(sys.argv[4], target_language)

    print(f'Starting translation from {original_language} to {target_language} on {target_path}...')
    md_files = glob.glob(os.path.join(original_path, '**/*.md'))
    md_files.append(os.path.join(original_path, 'README.md'))
    
    md_count = 0
    print('Translating markdown files...')
    for md_file in md_files:
        relative_path = os.path.relpath(md_file, original_path)
        target_file_path = os.path.join(target_path, relative_path)
        # Check if the file exists in the target language
        if os.path.exists(target_file_path):
            continue
        translate_file(md_file, target_file_path, original_language, target_language)
        md_count += 1

    print('Copying non-translated files...')
    copy_non_translated_files(original_path, target_path)

    program_count = 0
    print('Translating comments on programming files...')
    programming_files = [file for file in glob.glob(os.path.join(original_path, '**/*'), recursive=True) if is_programming_file(file)]
    programming_files = [f for f in programming_files if not f.startswith(os.path.join(original_path, 'Languages'))]

    for programming_file in programming_files:
        relative_path = os.path.relpath(programming_file, original_path)
        target_file_path = os.path.join(target_path, relative_path)
        if os.path.exists(target_file_path):
            continue
        translate_comments(programming_file, target_file_path, original_language, target_language)
        program_count += 1
    
    broken_links = check_broken_links(os.path.join(target_path, target_language))
    print('Validating broken links...')
    for file, link, status in broken_links:
        print(f'Broken link: {link} in file: {file}, retruned status: {status}')

    print('Checking size difference of original and translated Markdown files...')
    for md_file in md_files:
        relative_path = os.path.relpath(md_file, original_path)
        target_file_path = os.path.join(target_path, relative_path)
        original_size = get_file_size(md_file)
        target_size = get_file_size(target_file_path)
        size_difference = abs(original_size - target_size) / original_size * 100
        if size_difference > 10:
            print(f'Size difference more than 10%: {md_file} (original: {original_size}KB, translated: {target_size}KB, difference: {size_difference}%)')

    print(f'\nTranslation finished. {md_count} markdown files and {program_count} programming files translated.\nTotal broken links: {len(broken_links)}\n\n')
