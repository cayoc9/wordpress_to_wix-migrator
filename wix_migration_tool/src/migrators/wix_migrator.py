import requests
import json
import os

def upload_image(wix_config, image_url):
    """
    Downloads an image from a URL and uploads it to the Wix Media Platform.

    Args:
        wix_config (dict): Wix API configuration.
        image_url (str): The URL of the image to download.

    Returns:
        str: The new URL of the image hosted on Wix, or None if it fails.
    """
    if not image_url:
        return None

    try:
        # 1. Download the image from the source URL
        print(f"Downloading image from: {image_url}")
        image_response = requests.get(image_url, stream=True, timeout=10)
        image_response.raise_for_status()
        image_bytes = image_response.content
        
        # Extract a file name from the URL
        file_name = os.path.basename(image_url.split('?')[0])

        # 2. Upload the image to Wix Media Platform
        api_url = f"{wix_config['base_url']}/media/v1/files/upload"
        headers = {
            'Authorization': wix_config['api_key']
            # Content-Type for multipart/form-data is set automatically by requests
        }
        files = {
            'file': (file_name, image_bytes)
        }
        
        print(f"Uploading {file_name} to Wix...")
        upload_response = requests.post(api_url, headers=headers, files=files, timeout=30)
        upload_response.raise_for_status()
        
        wix_file_data = upload_response.json()
        new_url = wix_file_data.get('file', {}).get('url')
        
        if new_url:
            print(f"Image uploaded successfully. New Wix URL: {new_url}")
            return new_url
        else:
            print("Upload response from Wix did not contain a file URL.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Failed to process image from {image_url}. Error: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")
        return None


def _get_or_create_taxonomy_ids(wix_config, term_names: list, taxonomy_type: str) -> list:
    """
    Gets the IDs of existing taxonomy terms (tags/categories) or creates them if they don't exist.

    Args:
        wix_config: Wix API configuration.
        term_names (list): A list of tag or category names from WordPress.
        taxonomy_type (str): Either 'tags' or 'categories'.

    Returns:
        list: A list of Wix term IDs.
    """
    if not term_names:
        return []

    api_url_base = f"{wix_config['base_url']}/blog/v3/{taxonomy_type}"
    headers = {'Authorization': wix_config['api_key']}
    
    # 1. Get all existing terms from Wix to avoid creating duplicates
    try:
        response = requests.get(api_url_base, headers=headers)
        response.raise_for_status()
        existing_terms = response.json().get(taxonomy_type, [])
        # Create a map of {name: id} for quick lookup
        term_map = {term['label'].lower(): term['id'] for term in existing_terms}
    except requests.exceptions.RequestException as e:
        print(f"Error listing {taxonomy_type}: {e}")
        return []

    term_ids = []
    for name in term_names:
        if name.lower() in term_map:
            term_ids.append(term_map[name.lower()])
        else:
            # 2. Create the term if it doesn't exist
            print(f"Creating new {taxonomy_type[:-1]}: {name}")
            try:
                create_payload = {"label": name}
                create_response = requests.post(api_url_base, headers=headers, json={"tag": create_payload} if taxonomy_type == 'tags' else {"category": create_payload})
                create_response.raise_for_status()
                new_term = create_response.json().get(taxonomy_type[:-1], {})
                new_id = new_term.get('id')
                if new_id:
                    term_ids.append(new_id)
                    # Add to our map to avoid re-creating in the same run
                    term_map[name.lower()] = new_id
            except requests.exceptions.RequestException as e:
                print(f"Error creating {taxonomy_type[:-1]} '{name}': {e}")

    return term_ids


def create_draft_post(wix_config, post_data, rich_content_nodes):
    """
    Creates a draft post in Wix.

    Args:
        wix_config (dict): A dictionary containing the Wix API configuration 
                           (site_id, api_key, base_url).
        post_data (dict): A dictionary containing the post data to be migrated.
        rich_content_nodes (dict): The pre-converted Rich Content JSON object.

    Returns:
        dict: The JSON response from the Wix API.
    """
    api_url = f"{wix_config['base_url']}/blog/v3/draft-posts"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': wix_config['api_key']
    }

    # Get or create IDs for categories and tags
    category_ids = _get_or_create_taxonomy_ids(wix_config, post_data.get('Categories', []), 'categories')
    tag_ids = _get_or_create_taxonomy_ids(wix_config, post_data.get('Tags', []), 'tags')

    payload = {
        "draftPost": {
            "title": post_data.get('Title'),
            "richContent": rich_content_nodes,
            "slug": post_data.get('Slug'),
            "categoryIds": category_ids,
            "tagIds": tag_ids
        },
        "fieldsets": ["URL", "RICH_CONTENT"]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the Wix API: {e}")
        if e.response:
            print(f"Response content: {e.response.text}")
        return None
