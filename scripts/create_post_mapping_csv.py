
import os
import json
import csv

def create_post_mapping_csv():
    """
    Creates a CSV file mapping post data from JSON files.
    """
    posts_dir = "data/posts"
    output_csv_path = "data/posts_mapping.csv"

    if not os.path.exists(posts_dir):
        print(f"Directory not found: {posts_dir}")
        return

    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["post_name", "post_id", "content"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for filename in os.listdir(posts_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(posts_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        post_data = json.load(f)
                        post_id = post_data.get("id")
                        post_name = post_data.get("title")
                        content = post_data.get("richContent", {}).get("nodes")

                        if post_id and post_name and content:
                            writer.writerow({
                                "post_name": post_name,
                                "post_id": post_id,
                                "content": json.dumps(content)  # Store content as a JSON string
                            })
                        else:
                            print(f"Skipping {filename}: missing data.")
                    except json.JSONDecodeError:
                        print(f"Skipping {filename}: not a valid JSON file.")

    print(f"Successfully created mapping file at {output_csv_path}")

if __name__ == "__main__":
    create_post_mapping_csv()
