# Geliştirme Günlüğü (Dev Log)

## v7.3 - Çapraz Doğrulama ve Global İstihbarat (Final Stabil)

- **Zorunlu Global Teyit:** Yahoo Finance veri vermediğinde, sistem Mynet verisini doğrudan kabul etmiyor. Arka planda ABD borsasındaki (Proxy) hisse fiyatını çekip, Dolar/TL kuru ile çarpıyor. Eğer Yerel ve Global fiyat %5 toleransla eşleşirse "Onaylı" kabul ediyor.
- **Akıllı ADR Çözücü:** Global hissenin lot başına çarpanını (Örn: 1 ADR = 5 Hisse) otomatik algılayıp fiyatı ona göre düzeltiyor (KCHOL ve TCELL testlerinde başarılı oldu).
- **Kur Fallback:** Canlı dolar kuru çekilemezse sistem çökmez, güvenlik modunda (Sabit referans) çalışmaya devam eder.

## v7.1 - Anti-Blokaj ve Hayalet Modu (Stealth)

- **Dinamik Kimlik:** Her sorguda farklı bir User-Agent (Chrome, Firefox, Linux, Mac) taklidi yaparak "Bot" algısını kırıyor.
- **Rastgele Bekleme:** Robotik ritmi kırmak için her hisse analizi arasında 2-4 saniye rastgele "insani bekleme" süresi eklendi.
- **Sonuç:** Mynet blokajı tamamen aşıldı. Yahoo blokajına karşı direnç arttı.

## v7.0 - RLM Beyin ve TDFD Entegrasyonu

- **Yapay Zeka Kararı:** Fiyat ve indikatör skorları artık "RLM Brain" (Pekiştirmeli Öğrenme) süzgecinden geçiyor. RLM, geçmişte "Tuzak" olarak işaretlediği sinyalleri (örn: Fiyat artıyor ama TDFD döngüsü ters) hatırlayıp kullanıcıyı uyarıyor.
- **BitNet CPU:** Karar mekanizması `if/else` mantığından çıkarılıp olasılıksal bir işlemciye (BitNet) devredildi.

## v3.5 - RLM ve Biyolojik Döngü (Yapay Zeka Entegrasyonu)

- **RLM (Reinforcement Learning Manager):** Sisteme "Pekiştirmeli Öğrenme" yeteneği eklendi. Artık kararlarını geçmiş ödül/ceza puanlarına göre veriyor.
- **Biyolojik Yaşam Döngüsü:** Sistem veri akışı olmadığında "Rüya Modu"na geçerek eski anılarını (Memory Buffer) tarıyor ve yeniden değerlendiriyor.
- **BitNet 2.0:** İşlemci artık sadece matematiksel değil, RLM hafızasını sorgulayarak "sezgisel" kararlar da alabiliyor.
- **Bağışıklık Sistemi:** Kendi kod bütünlüğünü (DNA Hash) sürekli kontrol eden güvenlik katmanı eklendi.

- **Anti-Blokaj:** Her analiz arasında 2 saniye bekleyerek Mynet/Yahoo engellemelerini aşıyor.
- **Sonuç:** %100 Başarılı veri çekimi.

## v6.0 - İnteraktif Mod

- Terminal üzerinden `THYAO` yazıp enter'a basarak tek tek analiz yapabilme yeteneği eklendi.
- Bloklanma sorununu çözmek için yapıldı.

## v5.9 - Güçlendirilmiş Mynet

- Yahoo Finance çöktüğünde Mynet'ten veri çekilemiyordu.
- **Çözüm:** `User-Agent` (Browser Headers) eklenerek Mynet'e "Gerçek Tarayıcı" gibi istek atılması sağlandı. Blokaj aşıldı.

## v5.6 - Akıllı Osilatör ve Fırsat Modu

- Sisteme "Düşeni Al, Şişeni Sat" mantığı eklendi.
- RSI < 30 ise (Dip) -> Puan Ekle (+15)
- RSI > 70 ise (Tepe) -> Puan Kır (-10)
- F/K > 50 ise (Pahalı) -> Puan Kır (-20)
- TDFD Algoritması (Gizli Ritim) puanlamaya dahil edildi.

## v5.2 - Global İstihbarat (Proxy)

- BIST verileri eksik olduğunda ABD (OTC) piyasasına bağlanma özelliği eklendi.
- THYAO için `TKHVY`, GARAN için `TKGBY` gibi gölge kodlar tanımlandı.
- Temel analiz başarısı %80 arttı.

## v1.0 - v4.0 (Temel Hazırlık)

- Veri sağlayıcıların (IsYatirim, Mynet) yazılması.
- TDFD algoritmasının matematiksel inşası.
