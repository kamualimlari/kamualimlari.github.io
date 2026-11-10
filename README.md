# Kamu alımları: il il personel alımı haberleri

Haber sitelerinin RSS akışlarını ve Google Haberler aramalarını tarar, personel alımıyla ilgili haberleri süzer, hangi ili ilgilendirdiğini bulur ve bir web sayfasında il seçerek göstermenizi sağlar.

## Nasıl çalışır

```
scraper/scrape.py  →  data/ilanlar.json  →  index.html
 (her 30 dk)           (haber listesi)       (açık sekmede 5 dk'da bir kendini yeniler)
```

- `scraper/sources.json`: taranan haber siteleri ve arama sözcükleri. Kaynak ekleyip çıkarabilirsin.
- `scraper/scrape.py`: yalnızca Python 3 standart kütüphanesi, kurulum gerekmez. Her çalışmada yeni haberleri ekler, 90 günden eskileri siler, aynı haberi tekrar saymaz.
- `src/page.html` sayfanın kaynağıdır, `python3 build.py` bunu bağımsız `index.html` dosyasına çevirir. Sayfa tek dosyadır: İl seçimi (plaka kutusuna dokun), arama, alım türü ve zaman süzgeci. Seçtiğin il hatırlanır; adres çubuğundaki `#il-35` ile bağlantı paylaşılabilir.

## Kurulum A: GitHub ile ücretsiz ve tamamen otomatik (önerilen)

1. GitHub'da yeni bir depo aç, bu klasörün içindekileri yükle.
2. Depo ayarları → **Pages** → kaynak olarak `main` dalını ve kök klasörü seç. Sayfa `https://kullaniciadin.github.io/depoadi/` adresinde yayınlanır.
3. Depo → **Actions** sekmesi → "Haberleri güncelle" → **Run workflow** ile ilk taramayı elle başlat.
4. Bundan sonra `.github/workflows/guncelle.yml` her 30 dakikada bir taramayı çalıştırır, `data/ilanlar.json` dosyasını günceller. Açık sayfalar 5 dakikada bir yeni veriyi çeker.

Not: GitHub, zamanlanmış çalıştırmaları yoğun saatlerde geciktirebilir ve depoda 60 gün hiç etkinlik olmazsa zamanlamayı durdurur. Veri dosyası sürekli commit edildiği için bu pratikte olmaz.

### Telefona uygulama olarak kurma (PWA)

Sayfa kurulabilir uygulama olarak hazır (`manifest.webmanifest`, `sw.js`, `icons/`). Yayınladıktan sonra telefonda tarayıcıdan aç: Android Chrome'da "Ana ekrana ekle / Uygulamayı yükle", iPhone Safari'de Paylaş → "Ana Ekrana Ekle". HTTPS gerekir, GitHub Pages zaten HTTPS verir. Veri her zaman önce ağdan çekilir, internet yoksa son kopya gösterilir.

## Kurulum B: Kendi sunucun

```bash
crontab -e
# her 20 dakikada bir:
*/20 * * * * cd /yol/kamu-personel-takip && python3 scraper/scrape.py >> tara.log 2>&1
```

Sayfayı Nginx, Apache ya da herhangi bir statik barındırıcıyla yayınla.

## Yerelde deneme

```bash
python3 scraper/scrape.py     # gerçek haberleri çek (internet gerekir)
python3 serve.py              # http://localhost:8000
```

`index.html` dosyasına çift tıklayarak açma: tarayıcılar yerel dosyadan veri okumaya izin vermez, `serve.py` kullan.

Şu an `data/ilanlar.json` içinde, sayfalardan doğrulanmış 231 gerçek ilan var (61 il + ülke geneli). 20 ilde henüz kayıt yok; bu, ilan olmadığı anlamına gelmez, taramalar yarım kaldı. Kendi sunucunda `scrape.py` çalışınca yeni haberler bunlara eklenir. Boş bir örnek veri için: `python3 scraper/make_demo.py`.

## Bilmen gerekenler

- Sayfa **haber başlıklarını** derler, resmi ilan metni değildir. Başvuru koşulları için haberdeki bağlantıdan kurumun kendi duyurusuna gitmek gerekir.
- İl tespiti haber başlığındaki ve özetindeki il adına ve yaklaşık 700 ilçe adına bakar (ilçe, bağlı olduğu ile eşlenir; İBB gibi kısaltmalar da tanınır). Eksik bir ilçe için `scraper/districts.py` içindeki ilgili satıra adı eklemen yeterli. "Fatih", "Perşembe" gibi gündelik sözcüklerle karışabilen adlar yalnızca metinde "belediye" geçiyorsa sayılır. Ülke geneli ya da 4'ten fazla ili anan haberler "Ülke geneli" altında görünür.
- Bir haber sitesi RSS adresini değiştirirse betik o kaynağı atlar, diğerleriyle devam eder. Çıktı dosyasındaki `hatalar` alanında görürsün.
- Betik, siteleri yüksek sıklıkta yormaz; sıklığı 15 dakikanın altına indirmeni önermem.
- `scraper/sources.json` içindeki `html_listeler`, ilan.memurlar.net liste sayfalarını (bağlantı + gün/ay) okur; kendi sunucunda `scrape.py` bunlara da bakar. Yeni kategori eklemek için aynı biçimde satır ekle.
- `merge_sweep.py`, elle/ajanla hazırlanmış `part_*.json` dosyalarını veriye birleştirir.
- Testler: `python3 scraper/test_scrape.py`
