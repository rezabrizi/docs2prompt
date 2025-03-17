# docs2prompt 📜→🤖
[![PyPI](https://img.shields.io/badge/pypi-v0.1.4-orange.svg)](https://pypi.org/project/docs2prompt/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/rezabrizi/docs2prompt/blob/main/LICENSE)

Fetch open-sourced documentation from Github or closed-sourced documentation from publisher website to put into a LLM-friendly format in one file for use with LLMs.

## Features

- **GitHub Integration:** Extracts documentation files (e.g., README.md, docs.md, files within a `docs/` folder) from a GitHub repository using heuristics.
- **External Documentation Heuristic:** Optionally, fetches and converts external documentation links found in the root README.
- **URL Crawling:** Supports crawling a top-level documentation URL for content.
- **Customizable Output:** Serialize documentation in various formats (default plain text, XML, or Markdown). 
- **CLI and API:** Use as an importable Python package or as a standalone command-line tool.

## Installation

You can install **docs2prompt** directly from PyPI:

    pip install docs2prompt

Alternatively, clone the repository and install locally:

    git clone https://github.com/rezabrizi/docs2prompt.git
    cd docs2prompt
    pip install .

## Usage

### Command-Line Interface

After installing, you can run the tool via the command line.

**Example using a GitHub repository:**

    docs2prompt --repo owner/repo --token YOUR_GITHUB_TOKEN --format markdown --full_repo --external_documentation --output docs.txt

- `--repo`: GitHub repository in the format `owner/repo` (required if not using `--url`).
- `--token`: Your GitHub authentication token (only used if `--repo` is provided) - HIGHLY RECOMMENDED as without a token you can make at most 60 requests  per hour which easily gets reached with 1 query. Refer to [How to create a Personal Access Token (PAT)](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- `--repo`: Documentation page url (required if not using `--repo`).
- `--format`: Output format (`default`, `xml`, or `markdown`).
- `--output`: File name to write the serialized documentation.
- `--full_repo`: Performs a full recursive search of the repository. Having this as True will cause the query to take longer to finish.
- `--external_documentation`: Enables external documentation heuristic to fetch linked external docs from the root README. Having this as True will cause the query to take longer to finish.

**Example using a documentation URL:**

    docs2prompt --url https://example.com/documentation --format xml --output output.xml

> **Note:** You must provide exactly one of `--repo` or `--url`.

### As a Python Package

You can also import **docs2prompt** as a module in your own Python code:
```Python
from docs2prompt import get_github_documentation


repo_id = "owner/repo"
token = "YOUR_GITHUB_TOKEN" # Although optional, Highly recommended
content = get_github_documentation(repo_id, token, full_repo=False, external_documentation=False, output_format="XML")
print(output_content)
```

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

For any questions or suggestions, please open an issue on the [GitHub repository](https://github.com/rezabrizi/docs2prompt).
