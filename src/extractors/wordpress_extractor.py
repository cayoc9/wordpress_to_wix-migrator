import csv
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

def _parse_taxonomy_field(field_value):
    """Analisa um campo de taxonomia (Categorias ou Tags) de uma fonte CSV ou XML.

    Esta função processa uma string contendo itens de taxonomia separados por vírgulas ou pipes,
    limpando espaços em branco e decodificando entidades HTML.

    Args:
        field_value (str): O valor bruto do campo contendo itens de taxonomia separados por vírgula ou pipe.

    Returns:
        list: Uma lista de itens de taxonomia limpos e com entidades HTML decodificadas.
    """
    if not field_value:
        return []
    # Split by comma or pipe, then strip whitespace and decode HTML entities
    items = [html.unescape(item.strip()) for item in re.split(r'[,|]', field_value) if item.strip()]
    return items

def extract_posts_from_csv(file_path):
    """Extrai e normaliza posts a partir de um arquivo de exportação CSV do WordPress.

    Esta função lê um arquivo CSV exportado do WordPress e converte seus dados em um
    formato padronizado para migração. Trata corretamente campos de taxonomia, URLs de
    imagens e outros metadados necessários para a migração.

    Args:
        file_path (str): O caminho para o arquivo CSV.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um post
              com uma estrutura normalizada.

    Raises:
        FileNotFoundError: Se o arquivo CSV especificado não for encontrado.
        ValueError: Se ocorrer um erro durante o processamento de uma linha do CSV,
                    incluindo problemas de formatação ou codificação.
    """
    posts = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
            try:
                # Handle potential missing 'Image URL' key gracefully
                featured_image_url = row.get('Image URL', '')
                # Safely extract the first image URL, handling potential empty strings
                if featured_image_url:
                    featured_image_url = featured_image_url.split('|')[0]
                else:
                    featured_image_url = ''
                
                post = {
                    'ID': row.get('ID'),
                    'Title': row.get('Title'),
                    'ContentHTML': row.get('Content'),
                    'Excerpt': row.get('Excerpt'),
                    'Date': row.get('Date'),
                    'FeaturedImageUrl': featured_image_url,
                    'Categories': _parse_taxonomy_field(row.get('Categorias', '')),
                    'Tags': _parse_taxonomy_field(row.get('Tags', '')),
                    'Author ID': row.get('Author ID'),
                    'Author Email': row.get('Author Email'),
                    'Slug': row.get('Slug')
                }
                posts.append(post)
            except Exception as e:
                raise ValueError(f"Error processing row {row_num} in {file_path}: {e}") from e
    return posts

def extract_posts_from_xml(file_path):
    """Extrai posts a partir de um arquivo de exportação XML do WordPress.

    Esta função analisa um arquivo XML exportado do WordPress e extrai informações
    de posts, incluindo conteúdo, metadados e taxonomias (categorias e tags).
    Processa URLs de permalinks para derivar slugs.

    Args:
        file_path (str): O caminho para o arquivo XML.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um post.

    Raises:
        FileNotFoundError: Se o arquivo XML especificado não for encontrado.
        ET.ParseError: Se ocorrer um erro durante a análise do XML.
        ValueError: Se ocorrer um erro durante o processamento de um item do XML,
                    incluindo problemas de formatação ou campos ausentes.
    """
    posts = []
    tree = ET.parse(file_path)
    root = tree.getroot()
    for item in root.findall('.//item'):
        post_id_element = item.find('{http://wordpress.org/export/1.2/}post_id')
        title_element = item.find('title')
        content_element = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        date_element = item.find('pubDate')
        permalink_element = item.find('link')
        status_element = item.find('{http://wordpress.org/export/1.2/}status')

        try:
            permalink = permalink_element.text if permalink_element is not None else ''
            slug = None
            if permalink:
                # Extrai a última parte do caminho da URL, que é o slug.
                path = urlparse(permalink).path
                if path:
                    slug = path.strip('/').split('/')[-1]

            categories = []
            for cat_element in item.findall('category[@domain="category"]'):
                if cat_element.text:
                    categories.extend(_parse_taxonomy_field(cat_element.text))
            tags = [
                tag.text for tag in item.findall('category[@domain="post_tag"]') if tag.text
            ]

            post = {
                'ID': post_id_element.text if post_id_element is not None else None,
                'Title': title_element.text if title_element is not None else None,
                'ContentHTML': content_element.text if content_element is not None else None,
                'Date': date_element.text if date_element is not None else None,
                'Slug': slug,
                'Categories': categories,
                'Tags': tags,
            }
            posts.append(post)
        except Exception as e:
            # Assuming we can get the item's ID or title for context if available
            item_id = post_id_element.text if post_id_element is not None else 'unknown'
            raise ValueError(f"Error processing item with ID {item_id} in {file_path}: {e}") from e
    return posts
