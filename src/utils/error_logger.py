"""
Error logging system for WordPress to Wix migration failures.

This module provides functionality to log failed posts with their error details
to CSV files for later analysis and retry processing.
"""

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class ErrorLogger:
    """Logs migration errors to CSV for later processing."""
    
    def __init__(self, error_file: str = "reports/migration_errors.csv"):
        self.error_file = error_file
        self.error_dir = os.path.dirname(error_file)
        
        # Create directory if it doesn't exist
        if self.error_dir and not os.path.exists(self.error_dir):
            os.makedirs(self.error_dir)
        
        # CSV headers
        self.headers = [
            "timestamp",
            "slug", 
            "title",
            "error_type",
            "error_message",
            "error_details",
            "post_data_json",
            "retry_count"
        ]
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(error_file):
            self._write_headers()
    
    def _write_headers(self):
        """Write CSV headers to the error file."""
        with open(self.error_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)
    
    def log_error(self, 
                  post: Dict[str, Any], 
                  error_type: str, 
                  error_message: str, 
                  error_details: Optional[str] = None,
                  retry_count: int = 0):
        """
        Log a migration error to CSV.
        
        Args:
            post: The post data that failed to migrate
            error_type: Type of error (e.g., 'API_ERROR', 'VALIDATION_ERROR')
            error_message: Human-readable error message
            error_details: Detailed error information (JSON response, stack trace, etc.)
            retry_count: Number of times this post has been retried
        """
        timestamp = datetime.now().isoformat()
        slug = post.get("Slug", "unknown")
        title = post.get("Title", "")
        
        # Convert post data to JSON for storage
        post_data_json = json.dumps(post, ensure_ascii=False)
        
        error_row = [
            timestamp,
            slug,
            title,
            error_type,
            error_message,
            error_details or "",
            post_data_json,
            retry_count
        ]
        
        # Append to CSV file
        with open(self.error_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(error_row)
        
        print(f"ERROR LOGGED: {error_type} for post '{slug}' - {error_message}")
    
    def get_failed_posts(self) -> List[Dict[str, Any]]:
        """
        Read all failed posts from the error log.
        
        Returns:
            List of error records with post data
        """
        if not os.path.exists(self.error_file):
            return []
        
        failed_posts = []
        with open(self.error_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse post data from JSON
                    post_data = json.loads(row['post_data_json'])
                    
                    failed_posts.append({
                        'timestamp': row['timestamp'],
                        'slug': row['slug'],
                        'title': row['title'],
                        'error_type': row['error_type'],
                        'error_message': row['error_message'],
                        'error_details': row['error_details'],
                        'retry_count': int(row['retry_count']),
                        'post_data': post_data
                    })
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"WARNING: Could not parse error row: {e}")
                    continue
        
        return failed_posts
    
    def clear_errors(self):
        """Clear all logged errors by recreating the CSV with headers only."""
        self._write_headers()
        print(f"Cleared all errors from {self.error_file}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Get statistics about logged errors.
        
        Returns:
            Dictionary with error type counts
        """
        failed_posts = self.get_failed_posts()
        
        stats = {}
        for post in failed_posts:
            error_type = post['error_type']
            stats[error_type] = stats.get(error_type, 0) + 1
        
        return stats