import csv
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

def extract_posts_from_csv(file_path):
    """
    Extracts and normalizes posts from a WordPress CSV export file.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a post
              with a normalized structure.
    """
    posts = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                post = {
                    'ID': row.get('ID'),
                    'Title': row.get('Title'),
                    'ContentHTML': row.get('Content'),
                    'Excerpt': row.get('Excerpt'),
                    'Date': row.get('Date'),
                    'Post Type': row.get('Post Type'),
                    'Permalink': row.get('Permalink'),
                    'FeaturedImageUrl': row.get('Image URL', '').split('|')[0],
                    'Categories': [cat.strip() for cat in row.get('Categorias', '').split(',') if cat.strip()],
                    'Tags': [tag.strip() for tag in row.get('Tags', '').split(',') if tag.strip()],
                    'Status': row.get('Status'),
                    'Author ID': row.get('Author ID'),
                    'Author Username': row.get('Author Username'),
                    'Author Email': row.get('Author Email'),
                    'Author First Name': row.get('Author First Name'),
                    'Author Last Name': row.get('Author Last Name'),
                    'Slug': row.get('Slug'),
                    'Format': row.get('Format'),
                    'Template': row.get('Template'),
                    'Parent': row.get('Parent'),
                    'Parent Slug': row.get('Parent Slug'),
                    'Order': row.get('Order'),
                    'Comment Status': row.get('Comment Status'),
                    'Ping Status': row.get('Ping Status'),
                    'Post Modified Date': row.get('Post Modified Date')
                }
                posts.append(post)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return posts

def extract_posts_from_xml(file_path):
    """
    Extracts posts from a WordPress XML export file.

    Args:
        file_path (str): The path to the XML file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a post.
    """
    posts = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for item in root.findall('.//item'):
            post_id_element = item.find('{http://wordpress.org/export/1.2/}post_id')
            title_element = item.find('title')
            content_element = item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            date_element = item.find('pubDate')
            permalink_element = item.find('link')
            status_element = item.find('{http://wordpress.org/export/1.2/}status')

            permalink = permalink_element.text if permalink_element is not None else ''
            slug = None
            if permalink:
                # Extrai a última parte do caminho da URL, que é o slug.
                path = urlparse(permalink).path
                if path:
                    slug = path.strip('/').split('/')[-1]

            categories = [
                cat.text for cat in item.findall('category[@domain="category"]')
            ]
            tags = [
                tag.text for tag in item.findall('category[@domain="post_tag"]')
            ]

            post = {
                'ID': post_id_element.text if post_id_element is not None else None,
                'Title': title_element.text if title_element is not None else None,
                'Content': content_element.text if content_element is not None else None,
                'Date': date_element.text if date_element is not None else None,
                'Permalink': permalink,
                'Slug': slug, # Adiciona o slug ao dicionário do post
                'Status': status_element.text if status_element is not None else None,
                'Categories': categories,
                'Tags': tags,
            }
            posts.append(post)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return posts
