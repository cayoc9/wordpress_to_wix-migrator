
import requests
import os
import json
import argparse

def get_wix_auth_token():
    """
    Reads the Wix auth token from the migration_config.json file.

    Returns:
        str: The Wix auth token.
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'migration_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        return config.get('wix', {}).get('access_token')

def get_wix_post_content(post_id, auth_token, save_file=False):
    """
    Fetches the content of a Wix post and optionally saves it to a file.

    Args:
        post_id (str): The ID of the post to fetch.
        auth_token (str): Your Wix authorization token.
        save_file (bool): If True, saves the post content to a JSON file. 
                          Otherwise, prints to stdout.
    """
    headers = {
        "Authorization": auth_token
    }

    try:
        # First, get the post metadata
        meta_url = f"https://www.wixapis.com/blog/v3/posts/{post_id}?fieldsets=URL,SEO"
        response_meta = requests.get(meta_url, headers=headers)
        response_meta.raise_for_status()
        post_object = response_meta.json().get("post")

        if not post_object:
            print("Could not fetch post metadata.")
            return

        # Second, get the rich content
        content_url = f"https://www.wixapis.com/blog/v3/posts/{post_id}?fieldsets=RICH_CONTENT"
        response_content = requests.get(content_url, headers=headers)
        response_content.raise_for_status()
        rich_content = response_content.json().get("post", {}).get("richContent")

        if rich_content:
            post_object['richContent'] = rich_content
        else:
            print(f"Warning: Could not retrieve richContent for post {post_id}.")

        if save_file:
            # Create the directory if it doesn't exist
            output_dir = "data/posts"
            os.makedirs(output_dir, exist_ok=True)

            # Save the combined post object to a file
            output_path = os.path.join(output_dir, f"{post_id}.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(post_object, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved post content to {output_path}")
        else:
            # Print the JSON to stdout
            print(json.dumps(post_object, ensure_ascii=False, indent=4))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")

def main():
    """Main function to parse arguments and fetch post content."""
    parser = argparse.ArgumentParser(description="Fetch a Wix post by its ID.")
    parser.add_argument("post_id", help="The ID of the Wix post to fetch.")
    parser.add_argument(
        "--save-file",
        action="store_true",
        help="Save the post content to a JSON file in data/posts/."
    )
    args = parser.parse_args()

    auth_token = get_wix_auth_token()
    if auth_token:
        get_wix_post_content(args.post_id, auth_token, args.save_file)
    else:
        print("Could not find Wix auth token in config/migration_config.json")

if __name__ == "__main__":
    main()
