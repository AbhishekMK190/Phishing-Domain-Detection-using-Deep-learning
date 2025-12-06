import web_scarping.feature_init_ff1 as fe
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from bs4 import BeautifulSoup
import time
import functools

protocols = ["https", "http"]

def get_url_from_domain(domain, protocol):
    return f"{protocol}://{domain}"

def _probe_url(url: str, timeout: float = 4.0):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        start_time = time.time()
        resp = requests.get(url, timeout=timeout, headers=headers)
        elapsed = time.time() - start_time
        return url if resp.status_code == 200 else None
    except Exception:
        return None

def process_urls(domain_name, protocols):
    list_200 = []
    urls = [get_url_from_domain(domain_name, p) for p in protocols]

    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        futures = {executor.submit(_probe_url, u): u for u in urls}
        for fut in as_completed(futures, timeout=6.0):  # Add timeout to prevent hanging
            try:
                ok_url = fut.result(timeout=2.0)  # Individual future timeout
                if ok_url:
                    list_200.append(ok_url)
            except TimeoutError:
                continue  # Skip timed out URLs
            except Exception:
                continue  # Skip failed URLs

    return list_200

#main
def data_set_list_creation(domain):
    soup = None
    url = None
    response = None

    # Add overall timeout for the entire function
    start_time = time.time()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Check if we've been running too long (prevent infinite loading)
        if time.time() - start_time > 15:  # 15 second overall timeout
            print(f"Feature extraction timeout for {domain}, using domain-only features")
            return _get_domain_only_features(domain)

        lis_success = process_urls(domain, protocols)
        if len(lis_success) != 0:
            url = lis_success[0]
            url = str(url)
            response = requests.get(url, timeout=10, headers=headers)
            print(f"{url} --> Response = {response.status_code}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"HTTP {response.status_code} for {url}, using domain-only features")
        else:
            print(f"No accessible URLs for {domain}, using domain-only features")
    except Exception as e:
        print(f"Error accessing {domain}: {e}, using domain-only features")

    # Check timeout again before feature extraction
    if time.time() - start_time > 15:
        return _get_domain_only_features(domain)

    try:
        # If we have soup (website accessible), use full feature extraction
        if soup != None:
            domain = fe._url_domain(url)
            features_list_ml = [
                        fe.url_length(domain),
                        fe.number_of_special_charectors(domain),
                        fe._has_ssl(domain),
                        fe.number_of_name_servers(domain),
                        fe.number_of_href_links(soup),
                        fe.has_pop_up(soup),
                        fe.has_input(soup),
                        fe.has_password(soup),
                        fe.domain_age(domain),
                        fe.number_of_subdomains(url),
                        fe.has_favicon(soup, domain),
                        #fe.NonStdPort(domain),
                        fe.LinksInScriptTags(domain, soup),
                        fe.has_title(soup),
                        fe.has_submit(soup),
                        fe.has_button(soup),
                        fe.has_link(soup),
                        fe.has_email_input(soup),
                        fe.has_hidden_element(soup),
                        fe.has_audio(soup),
                        fe.has_video(soup),
                        fe.number_of_inputs(soup),
                        fe.number_of_images(soup),
                        fe.number_of_option(soup),
                        fe.number_of_list(soup),
                        fe.number_of_TR(soup),
                        fe.number_of_TH(soup),
                        fe.number_of_paragraph(soup),
                        fe.number_of_script(soup),
                        fe.length_of_title(soup),
                        fe.has_h1(soup),
                        fe.has_h2(soup),
                        fe.has_h3(soup),
                        fe.length_of_text(soup),
                        fe.number_of_clickable_button(soup),
                        fe.number_of_a(soup),
                        fe.number_of_div(soup),
                        fe.number_of_figure(soup),
                        fe.has_footer(soup),
                        fe.has_form(soup),
                        fe.has_text_area(soup),
                        fe.has_iframe(soup),
                        fe.has_text_input(soup),
                        fe.number_of_meta(soup),
                        fe.has_nav(soup),
                        fe.has_object(soup),
                        fe.has_picture(soup),
                        fe.number_of_sources(soup),
                        fe.number_of_span(soup),
                        fe.number_of_table(soup),
                        fe.number_link(soup),
                        fe.has_abnormalURL(response, domain),
                        fe.has_dns_recording(domain),
                        #fe.GoogleIndex(url),
                        #fe.double_slash_redirecting(domain),
                        fe.domain_registration_length(domain),
                        fe.statistical_report(url, domain),
                        fe.submitting_to_email(soup),
                        #fe.https_token(domain),
                        fe.count_redirects(domain),
                        fe.has_executable_files(soup),
                        fe.count_javascript_files(soup),
                        fe.number_of_emails(domain),
                        fe.get_ssl_update_age(domain),
                        fe.get_ip_count(domain),
                        fe.get_ssl_expiry_duration(domain),
                        fe.number_of_smtp_servers(domain),
                        fe.number_of_txt_records(domain),
                        fe.shortening_service(url),

            ]
            return features_list_ml
        else:
            # Website not accessible, use domain-only features with defaults
            print(f"Using domain-only features for {domain}")
            return _get_domain_only_features(domain)
    except Exception as e:
        print(f"Feature extraction error for {domain}: {e}")
        # Return a default feature vector if everything fails
        return _get_domain_only_features(domain)

def _get_domain_only_features(domain):
    """Get domain-only features when website is not accessible or timeout occurs"""
    try:
        features_list_ml = [
            fe.url_length(domain),                    # Domain-based
            fe.number_of_special_charectors(domain), # Domain-based
            fe._has_ssl(domain),                      # Domain-based
            fe.number_of_name_servers(domain),       # Domain-based
            0,  # number_of_href_links (default)
            0,  # has_pop_up (default)
            0,  # has_input (default)
            0,  # has_password (default)
            fe.domain_age(domain),                    # Domain-based
            fe.number_of_subdomains(f"https://{domain}"), # Domain-based
            0,  # has_favicon (default)
            0,  # LinksInScriptTags (default)
            0,  # has_title (default)
            0,  # has_submit (default)
            0,  # has_button (default)
            0,  # has_link (default)
            0,  # has_email_input (default)
            0,  # has_hidden_element (default)
            0,  # has_audio (default)
            0,  # has_video (default)
            0,  # number_of_inputs (default)
            0,  # number_of_images (default)
            0,  # number_of_option (default)
            0,  # number_of_list (default)
            0,  # number_of_TR (default)
            0,  # number_of_TH (default)
            0,  # number_of_paragraph (default)
            0,  # number_of_script (default)
            0,  # length_of_title (default)
            0,  # has_h1 (default)
            0,  # has_h2 (default)
            0,  # has_h3 (default)
            0,  # length_of_text (default)
            0,  # number_of_clickable_button (default)
            0,  # number_of_a (default)
            0,  # number_of_div (default)
            0,  # number_of_figure (default)
            0,  # has_footer (default)
            0,  # has_form (default)
            0,  # has_text_area (default)
            0,  # has_iframe (default)
            0,  # has_text_input (default)
            0,  # number_of_meta (default)
            0,  # has_nav (default)
            0,  # has_object (default)
            0,  # has_picture (default)
            0,  # number_of_sources (default)
            0,  # number_of_span (default)
            0,  # number_of_table (default)
            0,  # number_link (default)
            0,  # has_abnormalURL (default - can't check without response)
            fe.has_dns_recording(domain),             # Domain-based
            fe.domain_registration_length(domain),   # Domain-based
            0,  # statistical_report (default - can't check without URL)
            0,  # submitting_to_email (default)
            fe.count_redirects(domain),               # Domain-based
            0,  # has_executable_files (default)
            0,  # count_javascript_files (default)
            fe.number_of_emails(domain),              # Domain-based
            fe.get_ssl_update_age(domain),            # Domain-based
            fe.get_ip_count(domain),                  # Domain-based
            fe.get_ssl_expiry_duration(domain),       # Domain-based
            fe.number_of_smtp_servers(domain),        # Domain-based
            fe.number_of_txt_records(domain),         # Domain-based
            fe.shortening_service(f"https://{domain}"), # Domain-based
        ]
        return features_list_ml
    except Exception as e:
        print(f"Error in domain-only features for {domain}: {e}")
        # Return a default feature vector if everything fails
        return [0] * 65  # Assuming 65 features based on your model