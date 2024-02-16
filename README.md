# Repo AI Translate

Repo AI Translate is a Python script that uses OpenAI to translate markdown files and comments in programming files from one language to another. It also copies non-translated files and checks for broken links in the translated markdown files.

## Folder Structure

Before running the script, your project might look like this:

```
project/
├── file1.md
├── file2.py
└── img/
    └── image1.png
```

After running the script with 'pt-br', for example, as the target language, your project will look like this:

```
project/
├── file1.md
├── file2.py
├── img/
│   └── image1.png
└── languages/
│   └── pt-br
        ├── file1.md
        ├── file2.py
        └── img/
            └── image1.png
```

## Setup

1. Clone the repository.
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install the requirements: `pip install -r requirements.txt`
5. Copy the `.env_example` file to `.env` and fill in your OpenAI API key and the URL of repository to translate.

## Execution

To execute the script, run: `python repo-ai-trans.py <original_language> <target_language> <original_path> <target_path>`

For example: `python repo-ai-trans.py zh pt-br ./project ./project/languages`

This will translate all markdown files and comments in programming files from Chinese to Brazilian Portuguese, and place the translated files in the 'languages' folder inside the 'project' folder.

To re-translate an updated original file, simply delete the corresponding file in the destination translated folder and run the script again.

## Notes

Please note that the size of markdown files and the versions of the models used can significantly impact the results of the translation. Large markdown files may require more time to translate and may result in incomplete translations if the file size exceeds the model's maximum token limit. Similarly, different versions of the models may produce different translation results. It is recommended to keep markdown files to a reasonable size and to use the latest version of the models for optimal results.
