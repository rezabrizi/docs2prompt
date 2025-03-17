import requests

from utils import get_html_links, get_markdown_links
from web_docs import fetch_top_level_documentation

DOCS_FILE_NAMES = set(["readme.md", "readme.rst", "index.md", "docs.md", "readme.txt", "document.md"])
QUALIFIED_EXTENSIONS = set([".md", ".mdx", ".txt", ".rst"])
DOC_FOLDERS = set(["docs", "doc"])
DOC_KW = set(["docs", "documentation", "guide", "doc"])

def resolve_repo_identifier(repo_identifier, token=None):
    """
    Accept only repository identifiers in the format 'owner/repo'.
    Raise an Exception if the identifier is not in that format.
    """
    if "/" not in repo_identifier:
        raise Exception("Repository identifier must be in the format owner/repo")
    owner, repo = repo_identifier.split("/", 1)
    return owner, repo

def get_documentation_files_from_github(owner, repo, token=None, full_repo=False, external_documentation=False):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    docs = {}
    base_url = f"https://api.github.com/repos/{owner}/{repo}/contents"

    def fetch_path(path=""):
        url = base_url if path == "" else f"{base_url}/{path}"
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise Exception("Repository or path not found.")
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.text}")
        return response.json()

    def process_file_item(item):
        filename = item["name"].lower()
        # Check if file name matches specific known documentation names
        is_explicit_doc = filename in DOCS_FILE_NAMES

        # Check heuristic: if any directory in the path is named 'docs'
        path_parts = item["path"].split("/")
        parent_dirs = path_parts[:-1]  # exclude the filename
        has_docs_dir = any(part.lower() in DOC_FOLDERS for part in parent_dirs)

        # Check if file has one of the qualified extensions
        has_qualified_extension = any(filename.endswith(ext) for ext in QUALIFIED_EXTENSIONS)

        if is_explicit_doc or (has_docs_dir and has_qualified_extension):
            file_url = item.get("download_url")
            if file_url:
                file_resp = requests.get(file_url, headers=headers)
                if file_resp.status_code == 200:
                    # For root README, adjust the key
                    key = f"{repo}/{(item["path"]).lower()}"
                    docs[key] = file_resp.text

    def recursive_search(path="", is_in_docs_folder=False):
        items = fetch_path(path)
        for item in items:
            item_name_lower = item["name"].lower()
            if item["type"] == "dir":
                if full_repo or is_in_docs_folder:       
                    recursive_search(item["path"], is_in_docs_folder)
                if item_name_lower in DOC_FOLDERS: 
                    recursive_search(item["path"], True)
            elif item["type"] == "file":    
                    process_file_item(item)

    def check_for_linked_external_documentation_links():
        # New heuristic: Check root README for external documentation links with specific link text
        readme_key = f"{repo}/readme.md"
        if readme_key not in docs: return
        readme_content = docs[readme_key]
        seen_links = set()

        links = get_html_links(readme_content) + get_markdown_links(readme_content)
        for link_text, url in links:
            # Check if the link or text contains any of the keywords
            doc_kw_in_link = any(kw in url.lower() for kw in DOC_KW)
            doc_kw_in_text = any(kw in link_text.lower() for kw in DOC_KW)
            if doc_kw_in_link or doc_kw_in_text:
                web_docs = fetch_top_level_documentation(url, seen_links)
                docs.update(web_docs)


                
    recursive_search()
    if external_documentation:
        check_for_linked_external_documentation_links()
    return docs