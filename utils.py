import re 
from bs4 import BeautifulSoup

global_index = 0

def get_markdown_links(content):
    """Use regex to find markdown links: [link text](URL)"""
    doc_links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
    return doc_links

def get_html_links(content):
    doc_links = []
    soup = BeautifulSoup(content, 'html.parser')
    
    for a in soup.find_all('a'):
        href = a.get('href')
        link_text = a.get_text()
        if href and href.startswith('http'):
            doc_links.append((link_text, href))
    return doc_links

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


