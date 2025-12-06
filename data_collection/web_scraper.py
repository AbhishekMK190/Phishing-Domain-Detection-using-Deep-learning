import os
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import concurrent.futures
from datetime import datetime
import json
import tldextract
import socket
import whois
from fake_useragent import UserAgent
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection/scraper.log'),
        logging.StreamHandler()
    ]
)

class DomainScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = self._create_session()
        self.processed_domains = set()
        self.load_existing_domains()
        
    def _create_session(self):
        """Create a requests session with retry logic"""
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429]
        )
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session
    
    def get_random_headers(self):
        """Generate random headers to avoid bot detection"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def load_existing_domains(self):
        """Load already processed domains to avoid duplicates"""
        try:
            if os.path.exists('data_collection/processed_domains.json'):
                with open('data_collection/processed_domains.json', 'r') as f:
                    self.processed_domains = set(json.load(f))
                logging.info(f"Loaded {len(self.processed_domains)} processed domains")
        except Exception as e:
            logging.error(f"Error loading processed domains: {e}")
    
    def save_processed_domains(self):
        """Save the list of processed domains"""
        try:
            with open('data_collection/processed_domains.json', 'w') as f:
                json.dump(list(self.processed_domains), f)
        except Exception as e:
            logging.error(f"Error saving processed domains: {e}")
    
    def is_valid_domain(self, domain):
        """Check if a domain is valid and not already processed"""
        if not domain or domain in self.processed_domains:
            return False
        
        # Basic domain validation
        try:
            extracted = tldextract.extract(domain)
            if not extracted.domain or not extracted.suffix:
                return False
            return True
        except:
            return False
    
    def get_domain_info(self, domain):
        """Get WHOIS and other domain information"""
        try:
            domain_info = whois.whois(domain)
            return {
                'domain': domain,
                'creation_date': domain_info.creation_date,
                'expiration_date': domain_info.expiration_date,
                'registrar': domain_info.registrar,
                'name_servers': domain_info.name_servers,
                'status': domain_info.status,
                'emails': domain_info.emails,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logging.warning(f"Could not get WHOIS info for {domain}: {e}")
            return {
                'domain': domain,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
    
    def save_domains(self, domains, domain_type):
        """Save domains to appropriate file"""
        if not domains:
            return
        
        filename = f"data_collection/{domain_type}/domains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(domains, f, indent=2, default=str)
            logging.info(f"Saved {len(domains)} {domain_type} domains to {filename}")
        except Exception as e:
            logging.error(f"Error saving {domain_type} domains: {e}")
    
    def scrape_phishstats(self, max_pages=50):
        """Scrape phishing domains from PhishStats"""
        logging.info("Starting to scrape PhishStats...")
        base_url = "https://phishstats.info/phish_score.json?date=all&page={}"
        domains = []
        
        for page in range(1, max_pages + 1):
            try:
                url = base_url.format(page)
                response = self.session.get(
                    url,
                    headers=self.get_random_headers(),
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                if not data:
                    break
                    
                for entry in data:
                    domain = entry.get('url', '')
                    if self.is_valid_domain(domain):
                        domain_info = self.get_domain_info(domain)
                        domains.append(domain_info)
                        self.processed_domains.add(domain)
                
                logging.info(f"Processed page {page} - Found {len(domains)} domains so far")
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logging.error(f"Error scraping PhishStats page {page}: {e}")
                time.sleep(5)
        
        return domains
    
    def scrape_urlhaus(self):
        """Scrape phishing domains from URLhaus"""
        logging.info("Starting to scrape URLhaus...")
        url = "https://urlhaus.abuse.ch/downloads/text/"
        domains = []
        
        try:
            response = self.session.get(
                url,
                headers=self.get_random_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            for line in response.text.split('\n'):
                if line and not line.startswith('#'):
                    url_parts = line.strip().split('/')
                    if len(url_parts) > 2:
                        domain = url_parts[2]
                        if self.is_valid_domain(domain):
                            domain_info = self.get_domain_info(domain)
                            domains.append(domain_info)
                            self.processed_domains.add(domain)
                
            logging.info(f"Found {len(domains)} phishing domains from URLhaus")
            
        except Exception as e:
            logging.error(f"Error scraping URLhaus: {e}")
        
        return domains
    
    def scrape_openphish(self):
        """Scrape phishing domains from OpenPhish"""
        logging.info("Starting to scrape OpenPhish...")
        url = "https://openphish.com/feed.txt"
        domains = []
        
        try:
            response = self.session.get(
                url,
                headers=self.get_random_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            for line in response.text.split('\n'):
                if line and not line.startswith('#'):
                    domain = urlparse(line.strip()).netloc
                    if self.is_valid_domain(domain):
                        domain_info = self.get_domain_info(domain)
                        domains.append(domain_info)
                        self.processed_domains.add(domain)
            
            logging.info(f"Found {len(domains)} phishing domains from OpenPhish")
            
        except Exception as e:
            logging.error(f"Error scraping OpenPhish: {e}")
        
        return domains
    
    def scrape_legitimate_domains(self, count=25000):
        """Scrape legitimate domains from various sources"""
        logging.info("Starting to scrape legitimate domains...")
        sources = [
            self._scrape_majestic_million,
            self._scrape_tranco_list,
            self._scrape_cisco_umbrella
        ]
        
        all_domains = []
        for source in sources:
            try:
                domains = source(count // len(sources))
                all_domains.extend(domains)
                logging.info(f"Collected {len(domains)} domains from {source.__name__}")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Error in {source.__name__}: {e}")
        
        return all_domains
    
    def _scrape_majestic_million(self, count=10000):
        """Scrape from Majestic Million"""
        url = "https://downloads.majestic.com/majestic_million.csv"
        domains = []
        
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            for i, line in enumerate(response.iter_lines()):
                if i == 0 or not line:  # Skip header and empty lines
                    continue
                    
                domain = line.decode('utf-8').split(',')[2]  # Domain is the 3rd column
                if self.is_valid_domain(domain):
                    domain_info = self.get_domain_info(domain)
                    domains.append(domain_info)
                    self.processed_domains.add(domain)
                    
                    if len(domains) >= count:
                        break
            
        except Exception as e:
            logging.error(f"Error scraping Majestic Million: {e}")
        
        return domains
    
    def _scrape_tranco_list(self, count=10000):
        """Scrape from Tranco list"""
        url = "https://tranco-list.eu/download_daily/1000000"
        domains = []
        
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            for i, line in enumerate(response.iter_lines()):
                if not line:
                    continue
                    
                parts = line.decode('utf-8').split(',')
                if len(parts) >= 2:
                    domain = parts[1].strip()
                    if self.is_valid_domain(domain):
                        domain_info = self.get_domain_info(domain)
                        domains.append(domain_info)
                        self.processed_domains.add(domain)
                        
                        if len(domains) >= count:
                            break
            
        except Exception as e:
            logging.error(f"Error scraping Tranco list: {e}")
        
        return domains
    
    def _scrape_cisco_umbrella(self, count=5000):
        """Scrape from Cisco Umbrella Top 1M"""
        url = "http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
        domains = []
        
        try:
            # Download and extract the zip file
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Save the zip file
            zip_path = 'top-1m.csv.zip'
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract and process the CSV
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                csv_file = zip_ref.namelist()[0]
                with zip_ref.open(csv_file) as f:
                    for i, line in enumerate(f):
                        if not line:
                            continue
                            
                        parts = line.decode('utf-8').strip().split(',')
                        if len(parts) >= 2:
                            domain = parts[1].strip()
                            if self.is_valid_domain(domain):
                                domain_info = self.get_domain_info(domain)
                                domains.append(domain_info)
                                self.processed_domains.add(domain)
                                
                                if len(domains) >= count:
                                    break
            
            # Clean up
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
        except Exception as e:
            logging.error(f"Error scraping Cisco Umbrella list: {e}")
            # Clean up in case of error
            if os.path.exists('top-1m.csv.zip'):
                os.remove('top-1m.csv.zip')
        
        return domains

def main():
    # Create data directories if they don't exist
    os.makedirs('data_collection/legitimate', exist_ok=True)
    os.makedirs('data_collection/phishing', exist_ok=True)
    
    # Initialize scraper
    scraper = DomainScraper()
    
    try:
        # Scrape phishing domains
        logging.info("Starting phishing domain collection...")
        phish_domains = []
        phish_domains.extend(scraper.scrape_phishstats(max_pages=50))
        phish_domains.extend(scraper.scrape_urlhaus())
        phish_domains.extend(scraper.scrape_openphish())
        
        # Save phishing domains
        if phish_domains:
            scraper.save_domains(phish_domains, 'phishing')
        
        # Scrape legitimate domains
        logging.info("Starting legitimate domain collection...")
        legit_domains = scraper.scrape_legitimate_domains(count=25000)
        
        # Save legitimate domains
        if legit_domains:
            scraper.save_domains(legit_domains, 'legitimate')
        
        # Save processed domains
        scraper.save_processed_domains()
        
        logging.info("Data collection completed successfully!")
        logging.info(f"Total domains collected: {len(phish_domains) + len(legit_domains)}")
        logging.info(f"- Phishing domains: {len(phish_domains)}")
        logging.info(f"- Legitimate domains: {len(legit_domains)}")
        
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Saving progress...")
        scraper.save_processed_domains()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        scraper.save_processed_domains()
    finally:
        logging.info("Script execution completed.")

if __name__ == "__main__":
    main()
