from typing import Optional

from docs2prompt.github import get_documentation_files_from_github, resolve_repo_identifier
from docs2prompt.utils import serialize_docs
from docs2prompt.web_docs import fetch_top_level_documentation


def get_github_documentation(
    repo_identification: str,
    token: Optional[str] = None,
    full_repo: bool = False,
    external_documentation: bool = False,
    output_format: str = "default",
):
    """
    Retrieve documentation from a GitHub repository.

    This function takes a GitHub repository identifier in the format "owner/repo" along with a GitHub
    authentication token and optional flags to perform a full recursive search of the repository and/or
    fetch external documentation linked in the root README. The retrieved documentation files are then
    serialized into a string using the specified output format ("default", "xml", or "markdown").

    Parameters:
        repo_identification (str): The GitHub repository identifier in the format "owner/repo".
        token (str): The GitHub authentication token.
        full_repo (bool, optional): If True, perform a full recursive search of the repository. Keep as False for faster documentation retrieval. Defaults to False.
        external_documentation (bool, optional): If True, fetch external documentation linked in the root README. Defaults to False.
        output_format (str, optional): The output format for serialization. Valid values are "default", "xml", and "markdown". Defaults to "default".

    Returns:
        str: The serialized documentation content. Returns an empty string if no documentation is found.

    Raises:
        Exception: If there is an error resolving the repository or fetching the documentation from GitHub.
    """
    try:
        owner, repo_name = resolve_repo_identifier(repo_identification, token)
    except Exception as e:
        raise Exception(f"Error resolving repository: {e}")

    try:
        docs = get_documentation_files_from_github(
            owner,
            repo_name,
            token,
            full_repo=full_repo,
            external_documentation=external_documentation,
        )
        if not docs:
            return ""
    except Exception as e:
        raise Exception(f"Error fetching documentation from GitHub: {e}")
    if output_format not in ["default", "xml", "markdown"]:
        output_format = "default"
    output_content = serialize_docs(docs, output_format=output_format)
    return output_content


def get_url_documentation(url: str, output_format: str = "default"):
    """
    Retrieve documentation by crawling a top-level documentation URL.

    This function fetches documentation by crawling the provided URL (assumed to be a documentation website)
    and serializes the retrieved content using the specified output format ("default", "xml", or "markdown").

    Parameters:
        url (str): The URL of the documentation website.
        output_format (str, optional): The output format for serialization. Valid values are "default", "xml", and "markdown". Defaults to "default".

    Returns:
        str: The serialized documentation content. Returns an empty string if no documentation is found.

    Raises:
        Exception: If there is an error fetching documentation from the provided URL.
    """
    try:
        docs = fetch_top_level_documentation(url)
        if not docs:
            return ""
    except Exception as e:
        raise Exception(f"Error fetching documentation from URL: {e}")
    if output_format not in ["default", "xml", "markdown"]:
        output_format = "default"
    output_content = serialize_docs(docs, output_format=output_format)
    return output_content
