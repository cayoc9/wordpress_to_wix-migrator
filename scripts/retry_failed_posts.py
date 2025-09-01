#!/usr/bin/env python3
"""
Script to retry failed posts from migration error log.

This script reads posts that failed during migration from the error CSV
and attempts to migrate them again, optionally with different parameters
or after manual fixes.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.migration_tool import WordPressMigrationTool
from src.utils.error_logger import ErrorLogger


def retry_failed_posts(config_file: str = "config/migration_config.json", 
                      error_types: List[str] = None,
                      max_retries: int = 3,
                      dry_run: bool = False):
    """
    Retry posts that failed during migration.
    
    Args:
        config_file: Path to migration configuration file
        error_types: List of error types to retry (None = retry all)
        max_retries: Maximum retry count for posts
        dry_run: If True, only show what would be retried
    """
    
    # Initialize error logger and migration tool
    error_logger = ErrorLogger()
    migration_tool = WordPressMigrationTool(config_file=config_file)
    
    # Get failed posts
    failed_posts = error_logger.get_failed_posts()
    
    if not failed_posts:
        print("No failed posts found in error log.")
        return
    
    # Filter by error types if specified
    if error_types:
        failed_posts = [p for p in failed_posts if p['error_type'] in error_types]
    
    # Filter by retry count
    retry_posts = [p for p in failed_posts if p['retry_count'] < max_retries]
    
    print(f"Found {len(failed_posts)} failed posts")
    print(f"Posts eligible for retry (< {max_retries} attempts): {len(retry_posts)}")
    
    if not retry_posts:
        print("No posts eligible for retry.")
        return
    
    # Show error statistics
    error_stats = {}
    for post in retry_posts:
        error_type = post['error_type']
        error_stats[error_type] = error_stats.get(error_type, 0) + 1
    
    print("\nError type breakdown:")
    for error_type, count in error_stats.items():
        print(f"  {error_type}: {count} posts")
    
    if dry_run:
        print(f"\nDRY RUN: Would retry {len(retry_posts)} posts")
        for post in retry_posts[:10]:  # Show first 10
            print(f"  - {post['slug']}: {post['error_type']}")
        if len(retry_posts) > 10:
            print(f"  ... and {len(retry_posts) - 10} more")
        return
    
    # Ask for confirmation
    response = input(f"\nRetry {len(retry_posts)} failed posts? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Retry cancelled.")
        return
    
    print(f"\nStarting retry process for {len(retry_posts)} posts...")
    
    success_count = 0
    still_failing = []
    
    for i, failed_post in enumerate(retry_posts, 1):
        slug = failed_post['slug']
        retry_count = failed_post['retry_count']
        
        print(f"[{i}/{len(retry_posts)}] Retrying '{slug}' (attempt #{retry_count + 1})")
        
        try:
            # Create a temporary list with just this post
            posts_to_migrate = [failed_post['post_data']]
            
            # Temporarily override limit to process just this post
            original_limit = migration_tool.config.get('migration', {}).get('limit')
            migration_tool.config['migration']['limit'] = 1
            
            # Attempt migration
            migration_tool.migrate_posts(posts_to_migrate)
            
            # Restore original limit
            migration_tool.config['migration']['limit'] = original_limit
            
            print(f"  ✅ SUCCESS: {slug}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ STILL FAILING: {slug} - {str(e)}")
            
            # Log the retry attempt
            error_logger.log_error(
                post=failed_post['post_data'],
                error_type=failed_post['error_type'],
                error_message=f"Retry failed: {str(e)}",
                error_details=str(e),
                retry_count=retry_count + 1
            )
            
            still_failing.append(failed_post)
    
    print(f"\nRetry Summary:")
    print(f"  ✅ Successfully migrated: {success_count}")
    print(f"  ❌ Still failing: {len(still_failing)}")
    
    if still_failing:
        print(f"\nStill failing posts:")
        for post in still_failing:
            print(f"  - {post['slug']}: {post['error_type']}")


def show_error_stats():
    """Show statistics about failed posts."""
    error_logger = ErrorLogger()
    failed_posts = error_logger.get_failed_posts()
    
    if not failed_posts:
        print("No failed posts found.")
        return
    
    stats = error_logger.get_error_stats()
    
    print(f"Total failed posts: {len(failed_posts)}")
    print(f"\nError breakdown:")
    for error_type, count in sorted(stats.items()):
        print(f"  {error_type}: {count}")
    
    # Show recent failures
    print(f"\nMost recent failures:")
    recent = sorted(failed_posts, key=lambda x: x['timestamp'], reverse=True)[:10]
    for post in recent:
        print(f"  {post['timestamp'][:19]} - {post['slug']}: {post['error_type']}")


def main():
    parser = argparse.ArgumentParser(description="Retry failed WordPress to Wix migrations")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Retry command
    retry_parser = subparsers.add_parser('retry', help='Retry failed posts')
    retry_parser.add_argument('--config', '-c', default='config/migration_config.json',
                             help='Migration config file path')
    retry_parser.add_argument('--error-types', nargs='*', 
                             help='Specific error types to retry')
    retry_parser.add_argument('--max-retries', type=int, default=3,
                             help='Maximum retry attempts per post')
    retry_parser.add_argument('--dry-run', action='store_true',
                             help='Show what would be retried without doing it')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show error statistics')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear error log')
    
    args = parser.parse_args()
    
    if args.command == 'retry':
        retry_failed_posts(
            config_file=args.config,
            error_types=args.error_types,
            max_retries=args.max_retries,
            dry_run=args.dry_run
        )
    elif args.command == 'stats':
        show_error_stats()
    elif args.command == 'clear':
        error_logger = ErrorLogger()
        response = input("Clear all logged errors? This cannot be undone. (y/N): ")
        if response.lower() in ['y', 'yes']:
            error_logger.clear_errors()
            print("Error log cleared.")
        else:
            print("Clear cancelled.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()