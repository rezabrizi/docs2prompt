import requests
import sys
import click
import re

from bs4 import BeautifulSoup
import html2text

# Global index used in XML serialization
global_index = 0
DOCS_FILE_NAMES = set(["readme.md", "readme.rst", "index.md", "docs.md", "readme.txt", "document.md"])
QUALIFIED_EXTENSIONS = set([".md", ".mdx", ".txt", ".rst"])
DOC_FOLDERS = set(["docs", "doc"])
DOC_KW = set(["docs", "documentation", "guide", "doc"])

def resolve_repo_identifier(repo_identifier, token=None):
    """
    If the repo_identifier is in the format 'owner/repo', return (owner, repo).
    Otherwise, use the GitHub search API to find a repository with the given name in its title.
    If a single match is found, return (owner, repo). If no matches or multiple matches are found,
    raise an Exception with a meaningful message.
    """
    if "/" in repo_identifier:
        owner, repo = repo_identifier.split("/", 1)
        return owner, repo
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    search_url = f"https://api.github.com/search/repositories?q={repo_identifier}+in:name"
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error searching for repository: {response.status_code} {response.text}")
    results = response.json()
    items = results.get("items", [])
    if not items:
        raise Exception(f"No repository found with name '{repo_identifier}'. Please specify the owner, e.g., owner/repo.")
    elif len(items) > 1:
        # More than one match found, prompt user to be more specific
        matches = [f"{item['full_name']}" for item in items[:5]]  # show up to 5 matches
        match_list = ", ".join(matches)
        raise Exception(f"Multiple repositories found for name '{repo_identifier}': {match_list}. Please specify the repository in the format owner/repo.")
    else:
        full_name = items[0]['full_name']
        owner, repo = full_name.split("/", 1)
        print(f"Auto-selected repository: {full_name}")
        return owner, repo


def print_default(writer, path, content):
    writer(path)
    writer("---")
    writer(content)
    writer("")
    writer("---")


def print_as_xml(writer, path, content):
    global global_index
    writer(f'<document index="{global_index}">')
    writer(f"<source>{path}</source>")
    writer("<document_content>")
    writer(content)
    writer("</document_content>")
    writer("</document>")
    global_index += 1


def print_path(writer, path, content, output_format):
    if output_format == "xml":
        print_as_xml(writer, path, content)
    elif output_format == "markdown":
        writer(f"## {path}")
        writer("---")
        writer(content)
        writer("---")
    else:
        print_default(writer, path, content)


def serialize_docs(doc_dict, output_format="default"):
    output_lines = []
    writer = lambda s: output_lines.append(s)
    global global_index
    global_index = 0
    for path, content in doc_dict.items():
        print_path(writer, path, content, output_format)
    return "\n".join(output_lines)



def get_documentation_files(owner, repo, token=None, full_repo=False):
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
                    print(item["path"])
                    recursive_search(item["path"], True)
            elif item["type"] == "file":
                    process_file_item(item)

    
    def try_get_external_doc_link(url):
        try:
            ext_resp = requests.get(url)
            if ext_resp.status_code == 200:
                # Use BeautifulSoup to parse the external HTML content
                ext_soup = BeautifulSoup(ext_resp.text, 'html.parser')
                # Remove unwanted tags like script and style
                for tag in ext_soup(['script', 'style']):
                    tag.decompose()
                # Convert the HTML to markdown/plain text using html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                text = h.handle(ext_soup.prettify())
                docs[f"external:{url}"] = text
        except Exception as e:
            # Skip link if error occurs
            pass

    def get_markdown_links():
        readme_key = f"{repo}/readme.md"
        doc_links = []
        if readme_key in docs:
            readme_content = docs[readme_key]
            # Use regex to find markdown links: [link text](URL)
            doc_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', readme_content)
        return doc_links
    
    def get_html_links():
        readme_key = f"{repo}/readme.md"
        doc_links = []
        if readme_key in docs:
            readme_content = docs[readme_key]
            soup = BeautifulSoup(readme_content, 'html.parser')
            
            for a in soup.find_all('a'):
                href = a.get('href')
                link_text = a.get_text()
                if href and href.startswith('http'):
                    doc_links.append((link_text, href))
        return doc_links
        

    def check_for_linked_external_documentation_links():
        # New heuristic: Check root README for external documentation links with specific link text
            links = get_html_links() + get_markdown_links()
            for link_text, url in links:
                # Check if the link text contains any of the keywords
                doc_kw_in_link = any(kw in url.lower() for kw in DOC_KW)
                doc_kw_in_text = any(kw in link_text.lower() for kw in DOC_KW)
                if doc_kw_in_link or doc_kw_in_text:
                    try_get_external_doc_link(url)
                    
    recursive_search()
    check_for_linked_external_documentation_links()
    return docs


@click.command()
@click.argument('repo')
@click.option('--token', default=None, help='GitHub auth token')
@click.option('--format', 'output_format', type=click.Choice(['default', 'xml', 'markdown']), default='default', help='Output format: default, xml, markdown')
@click.option('--output', default=None, help='Output file name to write the serialized docs')
@click.option('--full_repo', is_flag=True, help='Perform a full recursive search of the repository', default=False)
def main(repo, token, output_format, output, full_repo):
    """
    Doc-to-Prompt CLI: Extracts documentation from a GitHub repository and serializes it in a specified format.
    
    REPO should be provided in the format owner/repo or just repo name if unique.
    """
    try:
        owner, repo_name = resolve_repo_identifier(repo, token)
    except Exception as e:
        click.echo(f"Error resolving repository: {e}", err=True)
        exit(1)

    try:
        docs = get_documentation_files(owner, repo_name, token, full_repo=full_repo)
        if not docs:
            click.echo("No documentation files found.", err=True)
            exit(1)
        output_content = serialize_docs(docs, output_format=output_format)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_content)
            click.echo(f"Documentation written to {output}")
        else:
            click.echo(output_content)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        exit(1)


if __name__ == "__main__":
    main()
