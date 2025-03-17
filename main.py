import click
from utils import serialize_docs
from github import resolve_repo_identifier, get_documentation_files_from_github
from web_docs import fetch_top_level_documentation

@click.command()
@click.option('--repo', default=None, help='GitHub repository in the format owner/repo')
@click.option('--url', default=None, help='Documentation URL to crawl the top-level page')
@click.option('--token', default=None, help='GitHub auth token (only used if --repo is provided)')
@click.option('--format', 'output_format', type=click.Choice(['default', 'xml', 'markdown']), default='default', help='Output format: default, xml, markdown')
@click.option('--output', default=None, help='Output file name to write the serialized docs')
@click.option('--full_repo', is_flag=True, help='Perform a full recursive search of the repository', default=False)
@click.option('--external_documentation', is_flag=True, help='Enable external documentation heuristic (only valid with --repo)', default=False)
def main(repo, url, token, output_format, output, full_repo, external_documentation):
    """
    Doc-to-Prompt CLI: Extracts documentation either from a GitHub repository or from a documentation URL.
    
    Provide exactly one of the following options:
      --repo : A GitHub repository in the format owner/repo.
      --url  : A documentation URL to crawl the top-level page.
    """
    # Validate mutually exclusive options:
    if (repo is None and url is None) or (repo is not None and url is not None):
        click.echo("Error: You must provide exactly one of --repo or --url.", err=True)
        exit(1)
    
    docs = {}
    if repo:
        try:
            owner, repo_name = resolve_repo_identifier(repo, token)
        except Exception as e:
            click.echo(f"Error resolving repository: {e}", err=True)
            exit(1)
        try:
            docs = get_documentation_files_from_github(owner, repo_name, token, full_repo=full_repo, external_documentation=external_documentation)
            if not docs:
                click.echo("No documentation files found in the GitHub repository.", err=True)
                exit(1)
        except Exception as e:
            click.echo(f"Error fetching documentation from GitHub: {e}", err=True)
            exit(1)
    else:
        # For URL, we crawl the top-level documentation page.
        try:
            docs = fetch_top_level_documentation(url)
            if not docs:
                click.echo("No documentation found at the provided URL.", err=True)
                exit(1)
        except Exception as e:
            click.echo(f"Error fetching documentation from URL: {e}", err=True)
            exit(1)
    
    output_content = serialize_docs(docs, output_format=output_format)
    
    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(output_content)
            click.echo(f"Documentation written to {output}")
        except Exception as e:
            click.echo(f"Error writing output: {e}", err=True)
            exit(1)
    else:
        click.echo(output_content)

if __name__ == "__main__":
    main()