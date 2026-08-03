
import datetime
import json
import urllib.parse
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
  headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K)'}

  for key, provider in config["providers"].items():
    print(f"🔍 فحص المصدر: {provider['name']} ({key})...")
    current_url = provider["base_url"]

    try:
      # 1️⃣ الكشف عن تغير الدومين تلقائياً (Domain Hop Detection)
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

      # 2️⃣ اختبار الكشط العملي المباشر من الكتالوج (بدون IMDb)
      catalog_url = f"{current_url}/movies"
      c_res = requests.get(catalog_url, headers=headers, timeout=10)
      soup = BeautifulSoup(c_res.text, "html.parser")

      # جلب أول فيلم من القائمة المباشرة
      link = soup.select_one(provider["selectors"]["link"])

      if link and link.get("href"):
        target_page = link["href"]
        if not target_page.startswith("http"):
          target_page = f"{current_url}{target_page}"

        # دخول صفحة الفيلم
        p_res = requests.get(target_page, headers=headers, timeout=10)
        p_soup = BeautifulSoup(p_res.text, "html.parser")
        dl_btn = p_soup.select_one(provider["selectors"]["download_btn"])

        if dl_btn and dl_btn.get("href"):
          dl_url = dl_btn["href"]
          if not dl_url.startswith("http"):
            dl_url = f"{current_url}{dl_url}"

          # دخول صفحة التنزيل والاستخراج
          dl_res = requests.get(dl_url, headers=headers, timeout=10)
          dl_soup = BeautifulSoup(dl_res.text, "html.parser")
          mp4_link = dl_soup.select_one('a[href*=".mp4"]')

          if mp4_link:
            print(
                "   ✅ اختبار الكشط المباشر نجح 100%! تم الوصول لرابط"
                " MP4."
            )
            provider["is_active"] = True
          else:
            print("   ❌ فشل العثور على زر MP4 المباشر.")
            provider["is_active"] = False
        else:
          print("   ❌ فشل الوصول لزر التحميل.")
          provider["is_active"] = False
      else:
        print("   ❌ لم يظهر أي محتوى في كتالوج الأفلام.")
        provider["is_active"] = False

    except Exception as e:
      print(f"   ❌ خطأ في فحص المصدر: {e}")
      provider["is_active"] = False

  # 3️⃣ حفظ الملف بعد التحديث
  config["last_updated"] = datetime.date.today().strftime("%Y-%m-%d")
  save_config(config)
  print("\n💾 تم حفظ التحديثات في ملف config.json بنجاح!")


if __name__ == "__main__":
  run_health_check()
