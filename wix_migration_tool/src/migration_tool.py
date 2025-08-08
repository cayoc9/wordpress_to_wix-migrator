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
    def __init__(self, config_file='config/migration_config.json'):
        """
        Inicializa a ferramenta de migração.
        As configurações são carregadas a partir de um arquivo JSON.
        """
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.migration_data = {
            'posts': [],
            'url_mappings': {},
            'seo_metrics': {},
            'images': [],
            'errors': []
        }
    
    def load_config(self, config_file):
        """Carrega a configuração a partir de um arquivo JSON."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_default_config(config_file)
    
    def create_default_config(self, config_file):
        """Cria um arquivo de configuração padrão."""
        default_config = {
            "wordpress": {
                "site_url": "",
                "api_endpoint": "/wp-json/wp/v2/",
                "username": "",
                "password": ""
            },
            "wix": {
                "site_id": "",
                "api_key": "",
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
        
        # Garante que o diretório exista antes de tentar criar o arquivo
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def log_message(self, message, level='INFO'):
        """Log migration messages"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        # Save to log file
        os.makedirs('reports/migration', exist_ok=True)
        with open('reports/migration/migration.log', 'a') as f:
            f.write(log_entry + '\\n')
