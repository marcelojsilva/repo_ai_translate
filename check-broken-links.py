import os
import re
import requests
import glob

def check_broken_links(path):
    md_files = glob.glob(os.path.join(path, '**/*.md'), recursive=True)
    broken_links = []
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        links = re.findall(r'\((.*?)\)', content)
        for link in links:
            if link.startswith('http'):
                try:
                    response = requests.get(link, timeout=3)
                    if response.status_code != 200:
                        broken_links.append((md_file, link))
                except (requests.ConnectionError, requests.Timeout):
                    broken_links.append((md_file, link))
            else:
                local_file_path = os.path.join(os.path.dirname(md_file), link)
                if not os.path.exists(local_file_path):
                    broken_links.append((md_file, link))
    return broken_links

if __name__ == '__main__':
    path = os.getcwd()
    broken_links = check_broken_links(path)
    for file, link in broken_links:
        print(f'Broken link: {link} in file: {file}')
