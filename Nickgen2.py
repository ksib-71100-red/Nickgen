import requests
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# === AYARLAR ===
MAX_WORKERS = 8             # Thread sayısı (çok yükseltme)
DELAY = 0.12                # İstekler arası bekleme (saniye)
CHARS = string.ascii_lowercase + string.digits

lock = threading.Lock()
checked = 0
found_count = 0

def is_valid_format(nick: str) -> bool:
    if len(nick) != 4:
        return False
    if nick.startswith("_") or nick.endswith("_"):
        return False
    if nick.count("_") > 1 or "__" in nick:
        return False
    return all(c in CHARS + "_" for c in nick)

def generate_nick() -> str:
    while True:
        if random.random() < 0.45:  # %45 ihtimalle _ koy
            pos = random.randint(1, 2)
            chars = [random.choice(CHARS) for _ in range(3)]
            chars.insert(pos, "_")
            nick = "".join(chars)
        else:
            nick = "".join(random.choice(CHARS) for _ in range(4))
        
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
        r = requests.get(url, timeout=8)
        data = r.json()
        return data.get("code") == 0  # 0 = Available
    except Exception:
        time.sleep(1)
        return False

def worker():
    global checked, found_count
    while True:
        nick = generate_nick()
        is_available = check_username(nick)

        with lock:
            checked += 1
            if checked % 25 == 0:
                print(f"Kontrol: {checked} | Bulunan: {found_count}")

            if is_available:
                found_count += 1
                print(f"✅ AVAILABLE → {nick}   (Toplam: {found_count})")
                
                # Anında dosyaya kaydet
                with open("available_nicks.txt", "a", encoding="utf-8") as f:
                    f.write(nick + "\n")

        time.sleep(DELAY)

if __name__ == "__main__":
    print("4 harfli available nick avı başladı...")
    print("Bulduğu her nick'i anında kaydedecek, hiç durmayacak.")
    print("Durdurmak için Ctrl + C yap.\n")

    # Dosyayı temiz başlat
    open("available_nicks.txt", "w").close()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for _ in range(MAX_WORKERS):
            executor.submit(worker)

        # Sonsuz döngü (Ctrl+C ile çıkılır)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\nDurduruldu.")
            print(f"Toplam kontrol: {checked}")
            print(f"Bulunan available: {found_count}")
            print("Kayıtlar → available_nicks.txt")
