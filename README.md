# docs2prompt

**docs2prompt** is a command-line tool and Python package that converts software documentation into a prompt-friendly format for LLMs. It extracts documentation from GitHub repositories or crawls a documentation website URL, then serializes the content into formats such as plain text, XML, or Markdown. This makes it easy to provide context to LLMs when working with large codebases or external documentation.

## Features

- **GitHub Integration:** Extracts documentation files (e.g., README.md, files within a `docs/` folder) from a GitHub repository.
- **External Documentation Heuristic:** Optionally, fetches and converts external documentation links found in the root README.
- **URL Crawling:** Supports crawling a top-level documentation URL for content.
- **Customizable Output:** Serialize documentation in various formats (default plain text, XML, or Markdown).
- **CLI and API:** Use as an importable Python package or as a standalone command-line tool.

## Installation

You can install **docs2prompt** directly from PyPI:

    pip install docs2prompt

Alternatively, clone the repository and install locally:

    git clone https://github.com/yourusername/docs2prompt.git
    cd docs2prompt
    pip install .

## Usage

### Command-Line Interface

After installing, you can run the tool via the command line.

**Example using a GitHub repository:**

    docs2prompt --repo owner/repo --token YOUR_GITHUB_TOKEN --format markdown --full_repo --external_documentation --output docs.txt

- `--repo`: GitHub repository in the format `owner/repo` (required if not using `--url`).
- `--token`: GitHub authentication token (only used if `--repo` is provided).
- `--format`: Output format (`default`, `xml`, or `markdown`).
- `--output`: File name to write the serialized documentation.
- `--full_repo`: Performs a full recursive search of the repository.
- `--external_documentation`: Enables external documentation heuristic to fetch linked external docs from the root README.

**Example using a documentation URL:**

    docs2prompt --url https://example.com/documentation --format xml --output output.xml

> **Note:** You must provide exactly one of `--repo` or `--url`.

### As a Python Package

You can also import **docs2prompt** as a module in your own Python code:

    from docs2prompt.github import get_documentation_files_from_github
    from docs2prompt.utils import serialize_docs

    owner = "owner"
    repo = "repo"
    token = "YOUR_GITHUB_TOKEN"
    docs = get_documentation_files_from_github(owner, repo, token, full_repo=True, external_documentation=True)
    output_content = serialize_docs(docs, output_format="markdown")
    print(output_content)

## Contributing

Contributions are welcome! If you'd like to contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Create a new Pull Request.

Please ensure that your changes include appropriate tests and documentation.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or suggestions, please open an issue on the [GitHub repository](https://github.com/yourusername/docs2prompt).