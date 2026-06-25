
# BBC v6 Sistem ve TDFD Algoritması

## (BIST Business Cycles - Time Dependent Force Dynamics)

Bu doküman, BBC v6 sisteminin çalışma mantığını ve kullandığı özel matematiksel algoritmaları açıklar.

### 1. Sistemin Amacı

BBC Sistemi, Borsa İstanbul (BIST) hisselerini analiz ederken klasik "fiyat ortalamalarına" dayalı analistlerin ötesine geçmeyi hedefler. Amacı, **Global Piyasa İstihbaratı** ile **Gizli Algoritmik Ritimleri** birleştirerek hibrit bir karar mekanizması oluşturmaktır.

---

### 2. TDFD Algoritması (Gizli Ritim)

Sistemde kullanılan `run_tdfd_analysis` fonksiyonu, **Time-Dependent Force Dynamics** (Zamana Bağlı Kuvvet Dinamiği) teorisine dayanır.

#### Klasik Matematikten Farkı Nedir?

* **Klasik:** RSI, MACD gibi indikatörler fiyatın "Ortalamasını" (Yumuşatılmış halini) alırlar. Bu yüzden sinyaller hep gecikmelidir (Lagging).
* **TDFD Algoritması:** Ortalama almaz. Zamanı büker.
  * Algoritma, `Fiyat(t)` anındaki hareket vektörü ile `Fiyat(t + n)` anındaki hareket vektörünün (gelecekteki veya geçmişteki döngünün) **Faz Uyumuna (Resonance)** bakar.
  * Eğer bir hisse senedi her 12 barda bir yukarı ivmeleniyorsa (T12 Döngüsü), TDFD bunu yakalar. Fiyat düşüyor olsa bile, "Zamanı Geldi" diyerek AL sinyali üretebilir.

> **Örnek:** THY hissesinde sistem "T12 Döngüsü" tespit etmiştir. Bu, fiyat grafiğinde gizli bir kalp atışı gibi, her 12 birimde bir piyasa yapıcı robotların devreye girdiğini gösterir.

---

### 3. Hibrit Zeka (Global Proxy)

Sistem sadece Borsa İstanbul verilerine güvenmez (çünkü yerel veriler manipüle edilebilir veya eksik olabilir).

* **Global Gölge Takibi:** THYAO analiz edilirken, sistem otomatik olarak ABD Borsasındaki (OTC) karşılığı olan `TKHVY` koduna bağlanır.
* **Arbitraj:** Eğer İstanbul'da bilanço açıklanmamışsa bile, Global piyasadaki yatırımcıların fiyatladığı F/K oranını temel alır.
* **Yedekleme Zinciri:** Global veri yoksa -> İş Yatırım Bilançosu -> O da yoksa -> Mynet Scraping devreye girer.

---

### 4. Akıllı Osilatör (Opportunist Mod)

Sistem v6 ile birlikte "Fırsatçı" bir kimliğe bürünmüştür:

* **Aşırı Satım Fırsatı:** Eğer bir hisse çok düşmüşse (RSI < 30), sistem trende karşı gelerek "Burada tepki alımı var" der ve puan ekler.
* **Aşırı Alım Tuzağı:** Eğer bir hisse çok şişmişse (RSI > 70), sistem trend yukarı olsa bile "Dikkat, düzeltme gelebilir" diyerek puan kırar.

**Özetle:** BBC v6, matematiksel bir "Kahin" prototipidir.
