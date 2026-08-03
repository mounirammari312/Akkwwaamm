import datetime
import json
import requests
from bs4 import BeautifulSoup

CONFIG_FILE = "config.json"


def load_config():
  with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    return json.load(f)


def save_config(config_data):
  with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump(config_data, f, ensure_ascii=False, indent=2)


def run_health_check():
  print("==================================================")
  print("🚀 بدء الفحص الآلي لمصادر البث (Direct Health Check)")
  print("==================================================\n")

  config = load_config()

  # 💡 إضافة الهيدرز الكاملة لمنع حظر السكربت أثناء الفحص
  headers = {
      'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
      'Referer': 'https://akwam.it/',
  }

  for key, provider in config["providers"].items():
    print(f"🔍 فحص المصدر: {provider['name']} ({key})...")
    current_url = provider["base_url"]

    try:
      # 1️⃣ الكشف عن تغير الدومين تلقائياً
      res = requests.get(
          current_url, headers=headers, timeout=10, allow_redirects=True
      )
      new_domain = "/".join(res.url.split("/")[:3])

      if new_domain != current_url:
        print(f"   ⚠️ تم اكتشاف تغير الدومين: {current_url} ──► {new_domain}")
        provider["base_url"] = new_domain
        provider["referer_header"] = f"{new_domain}/"
        current_url = new_domain
      else:
        print(f"   ✅ الدومين مستقر: {current_url}")

      # 2️⃣ اختبار الكشط المباشر بطلب محمي وهيدرز كاملة
      catalog_url = f"{current_url}/movies"
      c_res = requests.get(catalog_url, headers=headers, timeout=10)
      soup = BeautifulSoup(c_res.text, "html.parser")

      link = soup.select_one(provider["selectors"]["link"])

      if link and link.get("href"):
        target_page = link["href"]
        if not target_page.startswith("http"):
          target_page = f"{current_url}{target_page}"

        p_res = requests.get(target_page, headers=headers, timeout=10)
        p_soup = BeautifulSoup(p_res.text, "html.parser")
        dl_btn = p_soup.select_one(provider["selectors"]["download_btn"])

        if dl_btn and dl_btn.get("href"):
          dl_url = dl_btn["href"]
          if not dl_url.startswith("http"):
            dl_url = f"{current_url}{dl_url}"

          dl_res = requests.get(dl_url, headers=headers, timeout=10)
          dl_soup = BeautifulSoup(dl_res.text, "html.parser")
          mp4_link = dl_soup.select_one('a[href*=".mp4"]')

          if mp4_link:
            print("   ✅ الفحص نجح 100%! تم التأكد من عمل السيرفر.")
            provider["is_active"] = True
          else:
            print("   ⚠️ لم يتم العثور على زر MP4 المباشر في الاختبار.")
        else:
          print("   ⚠️ لم يتم الوصول لزر التحميل في الاختبار.")
      else:
        print("   ⚠️ لم يظهر محتوى في القائمة.")

    except Exception as e:
      print(f"   ❌ خطأ أثناء الفحص: {e}")

  # 3️⃣ حفظ التاريخ فقط دون تعطيل is_active بشكل عشوائي
  config["last_updated"] = datetime.date.today().strftime("%Y-%m-%d")
  save_config(config)
  print("\n💾 تم حفظ التحديثات في ملف config.json بنجاح!")


if __name__ == "__main__":
  run_health_check()

