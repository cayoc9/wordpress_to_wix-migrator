# WordPress to Wix Migration Tool
# Professional blog migration with SEO preservation

import requests
import json
import csv
import os
from datetime import datetime
from urllib.parse import urlparse, urljoin
import hashlib
import time

class WordPressMigrationTool:
    def __init__(self):
        """
        Inicializa a ferramenta de migração.
        As configurações são carregadas diretamente das variáveis de ambiente.
        """
        self.config = self.load_config_from_env()
        self.session = requests.Session()
        self.migration_data = {
            'posts': [],
            'url_mappings': {},
            'seo_metrics': {},
            'images': [],
            'errors': []
        }
    
    def load_config_from_env(self):
        """Carrega a configuração a partir das variáveis de ambiente."""
        return {
            "wix": {
                "site_id": os.getenv("WIX_SITE_ID"),
                "api_key": os.getenv("WIX_API_KEY"),
                "base_url": "https://www.wixapis.com"
            },
            "migration": {
                "batch_size": 10,
                "delay_between_requests": 1,
                "preserve_urls": True,
                "download_images": True,
                "validate_seo": True
            },
            "seo": {
                "check_meta_titles": True,
                "check_meta_descriptions": True,
                "check_headings": True,
                "check_images_alt": True,
                "check_internal_links": True
            }
        }
    
    def log_message(self, message, level='INFO'):
        """Log migration messages"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        # Save to log file
        os.makedirs('reports/migration', exist_ok=True)
        with open('reports/migration/migration.log', 'a') as f:
            f.write(log_entry + '\\n')
