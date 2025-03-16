import requests
import sys
import click

# Global index used in XML serialization
global_index = 0


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

    def recurse(path=""):
        items = fetch_path(path)
        for item in items:
            if item["type"] == "dir":
                # In full recursion, traverse all directories
                recurse(item["path"])
            elif item["type"] == "file":
                filename = item["name"].lower()
                # Define qualified extensions
                qualified_extensions = [".md", ".mdx", ".txt", ".rst"]
                # Check if file name matches specific known documentation names
                is_explicit_doc = filename in ["readme.md", "readme.rst", "index.md", "docs.md", "readme.txt"]

                # Check heuristic: if any directory in the path is named 'docs'
                path_parts = item["path"].split("/")
                parent_dirs = path_parts[:-1]  # exclude the filename
                has_docs_dir = any(part.lower() == "docs" for part in parent_dirs)

                # Check if file has one of the qualified extensions
                has_qualified_extension = any(filename.endswith(ext) for ext in qualified_extensions)

                if is_explicit_doc or (has_docs_dir and has_qualified_extension):
                    file_url = item.get("download_url")
                    if file_url:
                        file_resp = requests.get(file_url, headers=headers)
                        if file_resp.status_code == 200:
                            # For root README, adjust the key
                            if item["path"].count("/") == 0 and filename.startswith("readme"):
                                key = f"{repo}/readme.md"
                            else:
                                key = item["path"]
                            docs[key] = file_resp.text
        return

    if full_repo:
        # Full recursive search of the entire repository
        try:
            recurse("")
        except Exception as e:
            raise e
    else:
        # Non-full search: only inspect root and the 'docs' directory at root if it exists
        try:
            root_items = fetch_path("")
        except Exception as e:
            raise e

        # Process files in root
        for item in root_items:
            if item["type"] == "file":
                filename = item["name"].lower()
                if filename in ["readme.md", "readme.rst", "index.md", "docs.md", "readme.txt"]:
                    file_url = item.get("download_url")
                    if file_url:
                        file_resp = requests.get(file_url, headers=headers)
                        if file_resp.status_code == 200:
                            # For root README, adjust the key
                            if item["path"].count("/") == 0 and filename.startswith("readme"):
                                key = f"{repo}/readme.md"
                            else:
                                key = item["path"]
                            docs[key] = file_resp.text
            elif item["type"] == "dir" and item["name"].lower() == "docs":
                # Recursively search within the 'docs' directory
                try:
                    recurse(item["path"])
                except Exception as e:
                    raise e
    return docs


@click.command()
@click.argument('repo')
@click.option('--token', default=None, help='GitHub auth token')
@click.option('--format', 'output_format', type=click.Choice(['default', 'xml', 'markdown']), default='default', help='Output format: default, xml, markdown')
@click.option('--output', default=None, help='Output file name to write the serialized docs')
@click.option('--full_repo', is_flag=True, help='Perform a full recursive search of the repository')
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
