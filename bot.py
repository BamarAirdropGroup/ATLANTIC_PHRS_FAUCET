import requests
import json
import time
from colorama import init, Fore, Style
from eth_account import Account

init(autoreset=True)

class FaroSwapFaucet:
    def __init__(self):
        self.api_key = self.load_key()
        self.sitekey = "0x4AAAAAACAb9Tup9M-ewXTN"
        self.url = "https://api.dodoex.io/gas-faucet-server/faucet/claim"
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://faroswap.xyz",
            "referer": "https://faroswap.xyz/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

    def load_key(self):
        try:
            with open("key.txt", "r") as f:
                key = f.read().strip()
            if not key:
                print(Fore.RED + "[!] key.txt is empty")
                exit()
            return key
        except FileNotFoundError:
            print(Fore.RED + "[!] key.txt not found")
            exit()

    def solve_turnstile(self):
        task = {
            "clientKey": self.api_key,
            "task": {
                "type": "TurnstileTaskProxyless",
                "websiteURL": "https://faroswap.xyz",
                "websiteKey": self.sitekey
            }
        }
        try:
            r = requests.post("https://api.capmonster.cloud/createTask", json=task)
            task_id = r.json().get("taskId")
            if not task_id:
                return None

            for _ in range(40):
                time.sleep(4)
                res = requests.post("https://api.capmonster.cloud/getTaskResult",
                                   json={"clientKey": self.api_key, "taskId": task_id})
                data = res.json()
                if data.get("status") == "ready":
                    return data["solution"]["token"]
            return None
        except:
            return None

    def claim(self, address, token):
        payload = {
            "chainId": 688689,
            "address": address,
            "turnstileToken": token
        }
        try:
            r = requests.post(self.url, headers=self.headers, json=payload, timeout=20)
            result = r.json()

            print(Fore.CYAN + json.dumps(result, indent=2, ensure_ascii=False))

            # Only this exact response = real success
            if (result.get("code") == 0 and 
                result.get("msg") == "Faucet service is successful"):
                return True
            return False
        except:
            return False

    def save_key(self, address, private_key):
        with open("pkey.txt", "a") as f:
            f.write(f"{address}:{private_key}\n")
        print(Fore.GREEN + f"[+] Saved → {address[:10]}...{address[-8:]}")

    def run(self):
        print(Fore.CYAN + Style.BRIGHT + "\nFaroSwap Faucet Claimer — Turnstile (Nov 2025)\n")

        try:
            n = int(input(Fore.CYAN + "How many wallets? → "))
            if n < 1 or n > 20000:
                print(Fore.RED + "[!] 1–20000 only")
                return
        except:
            return

        print(Fore.YELLOW + f"\nStarting {n} wallets...\n")

        for i in range(n):
            acc = Account.create()
            addr = acc.address
            pk = acc.key.hex()

            print(Fore.MAGENTA + f"[{i+1}/{n}] {addr}")

            token = self.solve_turnstile()
            if not token:
                print(Fore.RED + "[-] Turnstile failed → skip\n")
                time.sleep(5)
                continue

            if self.claim(addr, token):
                self.save_key(addr, pk)
            else:
                print(Fore.YELLOW + "[-] Not success → not saved\n")

            time.sleep(8)

        print(Fore.CYAN + Style.BRIGHT + "\nDone! Check pkey.txt")

if __name__ == "__main__":
    FaroSwapFaucet().run()
