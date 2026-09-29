import requests
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# === AYARLAR ===
TARGET = 5                  # Kaç tane available bulunca dursun
MAX_WORKERS = 8             # Thread sayısı (çok yüksek yapma, 429 yersin)
DELAY = 0.15                # Her istek arası bekleme (saniye)
CHARS = string.ascii_lowercase + string.digits

lock = threading.Lock()
found = []
checked = 0
stop_flag = False

def is_valid_format(nick: str) -> bool:
    """Roblox username kurallarına uygun mu?"""
    if len(nick) != 4:
        return False
    if nick.startswith("_") or nick.endswith("_"):
        return False
    if nick.count("_") > 1:
        return False
    if "__" in nick:
        return False
    return all(c in CHARS + "_" for c in nick)

def generate_nick() -> str:
    """Geçerli formatta 4 harfli nick üretir (_ dahil olabilir)"""
    while True:
        # %40 ihtimalle _ koy
        if random.random() < 0.4:
            pos = random.randint(1, 2)  # 1 veya 2. pozisyona koy (başa/sona koyma)
            chars = [random.choice(CHARS) for _ in range(3)]
            chars.insert(pos, "_")
            nick = "".join(chars)
        else:
            nick = "".join(random.choice(CHARS) for _ in range(4))
        
        if is_valid_format(nick):
            return nick

def check_username(username: str) -> bool:
    """True = Available, False = Taken / Invalid"""
    global checked
    url = (
        f"https://auth.roblox.com/v1/usernames/validate"
        f"?username={username}"
        f"&birthday=2000-01-01T00:00:00.000Z"
        f"&context=Signup"
    )
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        
        with lock:
            checked += 1
            if checked % 20 == 0:
                print(f"Kontrol edildi: {checked} | Bulunan: {len(found)}")

        # code 0 = Username is valid (available)
        if data.get("code") == 0:
            return True
        return False
    except Exception:
        time.sleep(1)
        return False

def worker():
    global stop_flag
    while not stop_flag and len(found) < TARGET:
        nick = generate_nick()
        if check_username(nick):
            with lock:
                if nick not in found and len(found) < TARGET:
                    found.append(nick)
                    print(f"✅ AVAILABLE BULUNDU → {nick}")
                    # Anında dosyaya yaz
                    with open("available_nicks.txt", "a", encoding="utf-8") as f:
                        f.write(nick + "\n")
                    
                    if len(found) >= TARGET:
                        stop_flag = True
                        break
        time.sleep(DELAY)

if __name__ == "__main__":
    print("4 harfli available nick aranıyor...")
    print("Uyarı: 4 harfli nick'ler neredeyse tamamen dolu. Uzun sürebilir.\n")

    # Dosyayı temizle
    open("available_nicks.txt", "w").close()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(worker) for _ in range(MAX_WORKERS)]
        for f in as_completed(futures):
            if stop_flag:
                break

    print("\n" + "="*40)
    if found:
        print(f"{len(found)} available nick bulundu:")
        for n in found:
            print(f"  → {n}")
        print(f"\nKaydedildi → available_nicks.txt")
    else:
        print("Hiç available nick bulunamadı.")
    print("="*40)
