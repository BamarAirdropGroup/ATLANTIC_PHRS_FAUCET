import requests
import json
import time
from colorama import init, Fore, Style
from eth_account import Account
import os

class FaucetClaimer:
    def __init__(self):
        init(autoreset=True)  
        self.capmonster_api_key = self._read_api_key()
        self.capmonster_url = "https://api.capmonster.cloud"
        self.site_key = "6LcFofArAAAAAMUs2mWr4nxx0OMk6VygxXYeYKuO"
        self.site_url = "https://faroswap.xyz"
        self.faucet_url = "https://api.dodoex.io/gas-faucet-server/faucet/claim"
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://faroswap.xyz',
            'priority': 'u=1, i',
            'referer': 'https://faroswap.xyz/',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        }
        self.wallets = []

    def _read_api_key(self):
        try:
            with open('key.txt', 'r') as f:
                api_key = f.read().strip()
            if not api_key:
                print(Fore.RED + "Error: API key is empty in key.txt")
                exit(1)
            return api_key
        except FileNotFoundError:
            print(Fore.RED + "Error: key.txt not found")
            exit(1)
        except Exception as e:
            print(Fore.RED + f"Error reading API key: {e}")
            exit(1)

    def _generate_wallets(self, num_wallets):
        for _ in range(num_wallets):
            account = Account.create()
            self.wallets.append({
                'address': account.address,
                'private_key': account.key.hex()
            })
            print(Fore.CYAN + f"Generated wallet address: {account.address}")

    def _solve_captcha(self):
        payload = {
            "clientKey": self.capmonster_api_key,
            "task": {
                "type": "RecaptchaV2TaskProxyless",
                "websiteURL": self.site_url,
                "websiteKey": self.site_key
            }
        }
        try:
            response = requests.post(f"{self.capmonster_url}/createTask", json=payload)
            response.raise_for_status()
            result = response.json()
            task_id = result.get("taskId")
            if not task_id:
                print(Fore.RED + f"Error: Failed to create CAPTCHA task: {result}")
                return None

            print(Fore.YELLOW + "Solving CAPTCHA...")
            for _ in range(30):
                time.sleep(5)
                result = requests.post(f"{self.capmonster_url}/getTaskResult", json={"clientKey": self.capmonster_api_key, "taskId": task_id})
                result.raise_for_status()
                result_data = result.json()
                if result_data.get("status") == "ready":
                    token = result_data.get("solution", {}).get("gRecaptchaResponse")
                    print(Fore.GREEN + "CAPTCHA solved successfully")
                    return token
                elif result_data.get("errorId") != 0:
                    print(Fore.RED + f"CAPTCHA error: {result_data.get('errorDescription')}")
                    return None
            print(Fore.RED + "CAPTCHA solving timeout")
            return None
        except requests.RequestException as e:
            print(Fore.RED + f"Error solving CAPTCHA: {e} - Response: {e.response.text if e.response else 'No response'}")
            return None
        except Exception as e:
            print(Fore.RED + f"Unexpected error solving CAPTCHA: {e}")
            return None

    def _claim_faucet(self, wallet, captcha_token):
        payload = {
            
            "address": wallet['address'],
            "chainId": 688689,
            "recaptchaToken": captcha_token
        }
        try:
            response = requests.post(self.faucet_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            print(Fore.YELLOW + f"Faucet response: {json.dumps(result, indent=2)}")
            
            # Treat code 0 as success
            if result.get("code") == 0:
                tx_hash = result.get("data", {}).get("txHash")
                if tx_hash:
                    print(Fore.GREEN + f"Faucet request successful!!")
                    print(Fore.CYAN + f"TX Hash: {tx_hash}")
                    print(Fore.CYAN + f"Explorer link: https://atlantic.pharosscan.xyz/tx/{tx_hash}")
                else:
                    print(Fore.GREEN + "Faucet request successful, but TX hash not found.")
                return True
            else:
                print(Fore.RED + f"Faucet claim failed for address {wallet['address']}: {result.get('msg', 'Unknown error')}")
                return False
        except requests.RequestException as e:
            print(Fore.RED + f"Error claiming faucet for address {wallet['address']}: {e} - Response: {e.response.text if e.response else 'No response'}")
            return False
        except Exception as e:
            print(Fore.RED + f"Unexpected error claiming faucet for address {wallet['address']}: {e}")
            return False

    def _save_private_key(self, wallet):
        try:
            with open('pkey.txt', 'a') as f:
                f.write(f"{wallet['address']}:{wallet['private_key']}\n")
            print(Fore.GREEN + f"Private key for {wallet['address']} saved to pkey.txt")
        except Exception as e:
            print(Fore.RED + f"Error saving private key for {wallet['address']}: {e}")

    def run(self):
        try:
            num_wallets = int(input(Fore.CYAN + "Enter the number of wallets to generate: "))
            if num_wallets <= 0:
                print(Fore.RED + "Error: Number of wallets must be positive")
                return
        except ValueError:
            print(Fore.RED + "Error: Please enter a valid number")
            return

        self._generate_wallets(num_wallets)
        
        for wallet in self.wallets:
            print(Fore.CYAN + f"\nProcessing wallet: {wallet['address']}")
            captcha_token = self._solve_captcha()
            if not captcha_token:
                print(Fore.RED + f"Failed to solve CAPTCHA for {wallet['address']}. Skipping.")
                continue
            if self._claim_faucet(wallet, captcha_token):
                self._save_private_key(wallet)
            else:
                print(Fore.RED + f"Faucet claim failed for {wallet['address']}. Private key not saved.")

if __name__ == "__main__":
    claimer = FaucetClaimer()
    claimer.run()
