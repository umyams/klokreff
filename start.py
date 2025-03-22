import json
from web3.auto import w3
from eth_account import Account
from eth_account.messages import encode_defunct
import secrets
import time
import requests
import random
import sys
from datetime import datetime
from colorama import init, Fore, Style
import uuid
from datetime import timezone

init()

# Initialize Web3
w3 = w3

MODELS = [
    "llama-3.3-70b-instruct",
    "deepseek-r1",
    "gpt-4o-mini"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Edge/133.0.2623.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Brave/133.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

def print_banner():
    print(rf"""
{Fore.CYAN}                           
Kelliark | Klok.ai Auto Referral and Chat Bot{Style.RESET_ALL}
""")

def log_message(wallet_count, address, ref_code, status="info", message=""):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    color_map = {
        "success": Fore.GREEN + Style.BRIGHT,
        "error": Fore.RED + Style.BRIGHT,
        "warning": Fore.YELLOW + Style.BRIGHT,
        "info": Fore.CYAN + Style.BRIGHT,
        "process": Fore.MAGENTA + Style.BRIGHT,
        "address": Fore.WHITE + Style.BRIGHT,
        "referral": Fore.YELLOW + Style.NORMAL,
        "chat": Fore.GREEN + Style.NORMAL
    }
    
    if status == "process":
        print(f"\n{color_map['process']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Generating Wallet #{wallet_count}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    else:
        print(f"{color_map[status]}━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if status == "success":
            print(f"Wallet #{wallet_count} Successfully Generated!")
        elif status == "error":
            print(f"Wallet #{wallet_count} Failed!")
        print(f"{color_map['address']}Address: {address}")
        print(f"{color_map['referral']}Referred By: {ref_code}")
        if message:
            print(f"{color_map[status]}{message}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")

def load_list(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_wallet(ref_code, private_key, address):
    # Extract the referral code from the URL if present
    if "referral_code=" in ref_code:
        ref_code = ref_code.split("referral_code=")[-1].split('&')[0]  # Extract code after "referral_code="
    filename = f"klok_{ref_code}.txt"
    with open(filename, 'a') as f:
        f.write(f"{private_key}:{address}\n")

def generate_uuid():
    return str(uuid.uuid4())

def get_current_time():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def load_chat_messages():
    try:
        with open('chats.txt', 'r') as f:
            lines = f.readlines()
        messages = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        return messages
    except FileNotFoundError:
        print(f"{Fore.RED}chats.txt not found, using default messages{Style.RESET_ALL}")
        return [
            "What's your opinion on blockchain technology?",
            "How do you see AI evolving in the next decade?",
            "What makes a successful startup?",
            "Share an interesting science fact",
            "What's your favorite tech innovation?"
        ]

def generate_random_chat():
    messages = load_chat_messages()
    return random.choice(messages)

def sign_message(private_key, address, nonce):
    try:
        current_time = get_current_time()
        message = f"""klokapp.ai wants you to sign in with your Ethereum account:
{address}


URI: https://klokapp.ai/
Version: 1
Chain ID: 1
Nonce: {nonce}
Issued At: {current_time}"""
        
        message_hash = encode_defunct(text=message)
        signed_message = w3.eth.account.sign_message(message_hash, private_key=private_key)
        return signed_message.signature.hex(), message
    except Exception as e:
        print(f"{Fore.RED}Error signing message: {str(e)}{Style.RESET_ALL}")
        return None, None

def send_chat(session, chat_headers, chat_data):
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts:
        try:
            response = session.post(
                'https://api1-pp.klokapp.ai/v1/chat',
                headers=chat_headers,
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response
            elif response.status_code == 500 and "rate_limit_exceeded" in response.text:
                print(f"{Fore.YELLOW}Rate limit hit, waiting 30 seconds...{Style.RESET_ALL}")
                time.sleep(30)
            else:
                print(f"{Fore.RED}Failed with status code: {response.status_code}{Style.RESET_ALL}")
                if response.text:
                    print(f"{Fore.RED}Error: {response.text}{Style.RESET_ALL}")
                
        except requests.exceptions.ReadTimeout:
            print(f"{Fore.YELLOW}Request timed out, retrying...{Style.RESET_ALL}")
        except requests.exceptions.ChunkedEncodingError:
            print(f"{Fore.YELLOW}Connection broken, retrying...{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            
        attempt += 1
        if attempt < max_attempts:
            time.sleep(2)
            
    return None

def perform_chats(session, headers):
    max_retries = 3
    retry_count = 0
    num_chats = 10  # Previously changed to 10
    successful_chats = 0
    chat_headers = get_chat_headers(headers.get('x-session-token', ''))
    
    while retry_count < max_retries and successful_chats < num_chats:
        try:
            for i in range(successful_chats, num_chats):
                chat_message = generate_random_chat()
                chat_id = generate_uuid()
                current_time = get_current_time()
                
                chat_data = {
                    "id": chat_id,
                    "title": "",
                    "messages": [
                        {
                            "role": "user",
                            "content": chat_message
                        }
                    ],
                    "sources": [],
                    "model": random.choice(MODELS),
                    "created_at": current_time,
                    "language": "english"
                }
                
                print(f"{Fore.CYAN}Creating new chat with ID: {chat_id} using model: {chat_data['model']}{Style.RESET_ALL}")
                response = send_chat(session, chat_headers, chat_data)
                
                if response:
                    print(f"{Fore.GREEN}Chat {i+1}/{num_chats}: {chat_message}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}Response received successfully{Style.RESET_ALL}")
                    successful_chats += 1
                    
                    if i < num_chats - 1:
                        delay = random.uniform(5, 6)
                        print(f"{Fore.YELLOW}Waiting {delay:.1f} seconds before next chat...{Style.RESET_ALL}")
                        time.sleep(delay)
                else:
                    raise Exception("Failed to send chat after multiple attempts")
            
            if successful_chats == num_chats:
                print(f"{Fore.GREEN}Successfully completed all {num_chats} chats!{Style.RESET_ALL}")
                return True
                
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"{Fore.YELLOW}Chat sequence failed at {successful_chats}/{num_chats}, retrying...{Style.RESET_ALL}")
                time.sleep(2)
            else:
                print(f"{Fore.RED}Failed to complete chat sequence after {max_retries} attempts. Got {successful_chats}/{num_chats} chats.{Style.RESET_ALL}")
                return False
                
    return False

def get_headers():
    return {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://klokapp.ai',
        'referer': 'https://klokapp.ai/',
        'authority': 'api1-pp.klokapp.ai',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="133", "Not(A:Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site'
    }

def get_chat_headers(session_token):
    return {
        'Host': 'api1-pp.klokapp.ai',
        'X-Session-Token': session_token,
        'Sec-Ch-Ua-Platform': random.choice(['"Windows"', '"macOS"', '"Linux"']),
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Ch-Ua': '"Chromium";v="133", "Not(A:Brand";v="99"',
        'User-Agent': random.choice(USER_AGENTS),
        'Sec-Ch-Ua-Mobile': '?0',
        'Accept': '*/*',
        'Origin': 'https://klokapp.ai',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://klokapp.ai/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Priority': 'u=1, i'
    }

def get_nonce(address):
    try:
        url = f'https://api1-pp.klokapp.ai/v1/verify'
        headers = {
            'accept': '*/*',
            'access-control-request-method': 'POST',
            'access-control-request-headers': 'content-type',
            'origin': 'https://klokapp.ai',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-fetch-dest': 'empty',
            'referer': 'https://klokapp.ai/',
            'accept-language': 'en-US,en;q=0.9'
        }
        
        print(f"{Fore.YELLOW}Sending OPTIONS request to: {url}{Style.RESET_ALL}")
        response = requests.options(url, headers=headers)
        print(f"{Fore.CYAN}OPTIONS response status: {response.status_code}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Allowed methods: {response.headers.get('Allow', 'Not provided')}{Style.RESET_ALL}")
        
        nonce = secrets.token_hex(48)
        print(f"{Fore.GREEN}Generated nonce: {nonce}{Style.RESET_ALL}")
        return nonce
    except Exception as e:
        print(f"{Fore.RED}Error getting nonce: {str(e)}{Style.RESET_ALL}")
        return None

def login(address, signature, message, ref_code):
    try:
        session = requests.Session()
        response = session.post(
            'https://api1-pp.klokapp.ai/v1/verify',
            headers=get_headers(),
            json={
                'signedMessage': signature,
                'message': message,
                'referral_code': ref_code
            }
        )
        if response.status_code == 200:
            data = response.json()
            session_token = data.get('session_token', '')
            session.headers.update(get_chat_headers(session_token))
            return session
        print(f"{Fore.RED}Failed to login: {response.status_code} - {response.text}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}Error during login: {str(e)}{Style.RESET_ALL}")
        return None

def get_user_input(ref_count):
    max_accounts = ref_count * 100
    
    print(f"\n{Fore.CYAN}Available Resources:{Style.RESET_ALL}")
    print(f"Referral Codes: {ref_count}")
    print(f"Maximum Possible Accounts: {max_accounts}")
    
    while True:
        try:
            num_accounts = int(input(f"\n{Fore.YELLOW}Enter number of accounts to generate (max {max_accounts}): {Style.RESET_ALL}"))
            if 1 <= num_accounts <= max_accounts:
                return num_accounts
            print(f"{Fore.RED}Please enter a number between 1 and {max_accounts}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number{Style.RESET_ALL}")

def create_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    acct = Account.from_key(private_key)
    return private_key, acct.address

def process_account(wallet_count, ref_code):
    log_message(wallet_count, "", ref_code, "process")
    
    try:
        private_key, address = create_wallet()
        log_message(wallet_count, address, ref_code, "info", "Wallet created, getting nonce...")
        
        nonce = get_nonce(address)
        if not nonce:
            log_message(wallet_count, address, ref_code, "error", "Failed to get nonce")
            return False
            
        signature, message = sign_message(private_key, address, nonce)
        if not signature:
            log_message(wallet_count, address, ref_code, "error", "Failed to sign message")
            return False
            
        session = login(address, signature, message, ref_code)
        if not session:
            log_message(wallet_count, address, ref_code, "error", "Failed to login")
            return False
        
        # Save wallet immediately after successful login
        save_wallet(ref_code, private_key, address)
        log_message(wallet_count, address, ref_code, "success", "Login successful, wallet saved, starting chat sequence...")
        
        if perform_chats(session, session.headers):
            log_message(wallet_count, address, ref_code, "success", "All chats completed successfully!")
            return True
        else:
            log_message(wallet_count, address, ref_code, "error", "Failed during chat sequence")
            return False
            
    except Exception as e:
        log_message(wallet_count, address, ref_code, "error", f"Error: {str(e)}")
        return False

def main():
    print_banner()
    
    refs = load_list('refs.txt')
    
    if not refs:
        print(f"{Fore.RED}Error: No referral codes found in refs.txt{Style.RESET_ALL}")
        return
    
    successful_accounts = 0
    num_accounts = get_user_input(len(refs))
    wallet_count = 0
    
    while wallet_count < num_accounts:
        wallet_count += 1
        ref_code = random.choice(refs)
        
        if process_account(wallet_count, ref_code):
            successful_accounts += 1
        
        if wallet_count < num_accounts:
            time.sleep(random.uniform(1, 2))

    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"Accounts created: {successful_accounts}")

if __name__ == "__main__":
    main()
