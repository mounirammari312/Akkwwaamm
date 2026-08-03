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
  print("🚀 بدء الفحص الآلي لمصادر البث (Auto Health Check)")
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
      new_domain = "/".join(res.url.split("/")[:3])  # استخراج Domain الأصلي

      if new_domain != current_url:
        print(f"   ⚠️ تم اكتشاف تغير الدومين: {current_url} ──► {new_domain}")
        provider["base_url"] = new_domain
        provider["referer_header"] = f"{new_domain}/"
        current_url = new_domain
      else:
        print(f"   ✅ الدومين مستقر: {current_url}")

      # 2️⃣ اختبار الكشط العملي على IMDb ID افتراضي
      imdb_id = provider["test_imdb_id"]
      imdb_res = requests.get(
          f"https://v2.sg.media-imdb.com/suggestion/t/{imdb_id}.json",
          headers=headers,
          timeout=8,
      )
      title = imdb_res.json()["d"][0]["l"]

      # البحث في الموقع
      search_url = f"{current_url}{provider['search_endpoint']}{urllib.parse.quote(title)}"
      s_res = requests.get(search_url, headers=headers, timeout=10)
      soup = BeautifulSoup(s_res.text, "html.parser")

      link = soup.select_one(provider["selectors"]["content_link"])

      if link:
        # دخول صفحة العرض والتحميل
        target_page = link["href"]
        p_res = requests.get(target_page, headers=headers, timeout=10)
        p_soup = BeautifulSoup(p_res.text, "html.parser")
        dl_btn = p_soup.select_one(provider["selectors"]["download_btn"])

        if dl_btn:
          dl_res = requests.get(dl_btn["href"], headers=headers, timeout=10)
          dl_soup = BeautifulSoup(dl_res.text, "html.parser")
          mp4_link = dl_soup.select_one('a[href*=".mp4"]')

          if mp4_link:
            print("   ✅ اختبار الكشط نجح 100%! تم الوصول لرابط MP4.")
            provider["is_active"] = True
          else:
            print("   ❌ فشل العثور على زر MP4 المباشر.")
            provider["is_active"] = False
        else:
          print("   ❌ فشل الوصول لزر التحميل.")
          provider["is_active"] = False
      else:
        print("   ❌ لم يظهر أي محتوى في نتيجة البحث.")
        provider["is_active"] = False

    except Exception as e:
      print(f"   ❌ خطأ في فحص المصدر: {e}")
      provider["is_active"] = False

  # 3️⃣ حفظ الملف بعد التحديث
  import datetime

  config["last_updated"] = datetime.date.today().strftime("%Y-%m-%d")
  save_config(config)
  print("\n💾 تم حفظ التحديثات في ملف config.json بنجاح!")


if __name__ == "__main__":
  run_health_check()

