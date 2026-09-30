import requests
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# === GÜVENLİ AYARLAR ===
MAX_WORKERS = 4
DELAY = 0.35
CHARS = string.ascii_lowercase + string.digits

lock = threading.Lock()
checked = 0
found_count = 0

def is_valid_format(nick: str) -> bool:
    length = len(nick)
    if length not in (4, 5):
        return False
    if nick.startswith("_") or nick.endswith("_"):
        return False
    if nick.count("_") > 1 or "__" in nick:
        return False
    return all(c in CHARS + "_" for c in nick)

def generate_nick() -> str:
    length = random.choice([4, 5])  # %50 4 harf, %50 5 harf
    while True:
        if random.random() < 0.40:  # _ koyma ihtimali
            if length == 4:
                pos = random.randint(1, 2)
            else:  # 5 harf
                pos = random.randint(1, 3)
            chars = [random.choice(CHARS) for _ in range(length - 1)]
            chars.insert(pos, "_")
            nick = "".join(chars)
        else:
            nick = "".join(random.choice(CHARS) for _ in range(length))
        
        if is_valid_format(nick):
            return nick

def check_username(username: str) -> bool:
    url = (
        f"https://auth.roblox.com/v1/usernames/validate"
        f"?username={username}"
        f"&birthday=2000-01-01T00:00:00.000Z"
        f"&context=Signup"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("code") == 0
    except Exception:
        time.sleep(1.5)
        return False

def worker():
    global checked, found_count
    while True:
        nick = generate_nick()
        is_available = check_username(nick)

        with lock:
            checked += 1
            if checked % 20 == 0:
                print(f"Kontrol: {checked} | Bulunan: {found_count}")

            if is_available:
                found_count += 1
                print(f"✅ AVAILABLE → {nick}   ({len(nick)} harf)   (Toplam: {found_count})")
                
                with open("available_nicks.txt", "a", encoding="utf-8") as f:
                    f.write(f"{nick}\n")

        time.sleep(DELAY)

if __name__ == "__main__":
    print("4 + 5 harfli available nick avı başladı (Güvenli Mod)")
    print("Bulduğu her nick anında kaydedilecek.")
    print("Durdurmak için Ctrl + C yap.\n")

    open("available_nicks.txt", "w").close()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for _ in range(MAX_WORKERS):
            executor.submit(worker)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\nDurduruldu.")
            print(f"Toplam kontrol: {checked}")
            print(f"Bulunan available: {found_count}")
            print("Kayıtlar → available_nicks.txt")
