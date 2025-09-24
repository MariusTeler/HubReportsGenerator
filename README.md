# Unified Hub Report Generator

Un script Python unificat care generează automat rapoartele de hub pornind de la un fișier master, înlocuind cele 2 scripturi separate anterioare.

## 🔧 Funcționalități

- **Un singur fișier master**: În loc să încarci 2 fișiere separate pentru fiecare script, folosești un singur fișier master
- **Filtrare automată**: Scriptul detectează automat datele necesare pe baza criteriilor specificate
- **Generare dublă**: Creează atât raportul "Statie-Hub" cât și "Hub-Statie" dintr-o singură rulare
- **Gestionare automată a intervalelor de timp**: Calculează automat intervalele corecte pe baza datei raportului
- **Sortare automată**: Sheet-ul "Detaliat" este sortat după coloana "User"
- **Formatare Excel**: Coloanele de procente în sheet-ul "Sumar" sunt formatate ca procente (0.00%)
- **Suport multi-hub**: Generează rapoarte pentru multiple hub-uri (Brașov, Sibiu) cu configurări independente

## 📋 Cerințe

```bash
pip install pandas openpyxl
```

## 🚀 Utilizare

### Rulare interactivă:

```bash
python unified_hub_report_generator.py
```

Scriptul va afișa un meniu pentru a selecta hub-ul:
1. Generează rapoarte pentru Brașov
2. Generează rapoarte pentru Sibiu  
3. Generează rapoarte pentru toate hub-urile

### Utilizare programatică:

```python
from unified_hub_report_generator import generate_brasov_reports, generate_sibiu_reports, generate_all_hub_reports

# Pentru Brașov
generate_brasov_reports("2025-07-23")

# Pentru Sibiu
generate_sibiu_reports("2025-07-23")

# Pentru toate hub-urile
generate_all_hub_reports("2025-07-23")
```

### Utilizare avansată cu configurări custom:

```python
from unified_hub_report_generator import UnifiedHubReportGenerator

# Configurație personalizată
custom_config = {
    'nume': 'CLUJ',
    'prescurtare': 'CLJ',
    'intrare_start_hour': 10,
    'intrare_start_minute': 0,
    'intrare_end_hour': 18,
    'intrare_end_minute': 0,
    'iesire_start_hour': 10,
    'iesire_start_minute': 0,
    'iesire_end_hour': 18,
    'iesire_end_minute': 0
}

generator = UnifiedHubReportGenerator(fisier_master, data_raport, base_url, custom_config)
generator.genereaza_rapoarte()
```

## 📁 Structura fișierelor

### Fișierele necesare:

1. **Fișier Master** (`master_data.csv`): Conține toate datele de scanare cu coloanele:
   - `CodBare`, `Tip Scanare`, `Centru`, `Ruta`, `Centru exp`, `Centru dest`
   - `Expeditor`, `Destinatar`, `bucati`, `Greutate`, `Categorie`, `Scanare`, `User`
   
   **Valori importante în `Tip Scanare`**:
   - `"Iesire Centru"` (nu "Ieșire centru" - fără diacritice, fără spațiu în mijloc)
   - `"Intrare Centru"` (nu "Intrare centru" - fără diacritice, fără spațiu în mijloc)

2. **Fișiere statice** (în directorul `Utile/`):
   - `ruteBRASOV.csv` / `ruteSIBIU.csv` - rutele pentru fiecare hub
   - `ruteBrasov_echivalenta.xlsx` / `ruteSibiu_echivalenta.xlsx` - echivalențele rutelor
   - `FirmeFaraScanIesire.xlsx` - firme fără scan ieșire (comun pentru toate hub-urile)

## 🕐 Logica de filtrare automată

### 📅 Logica Specială pentru Weekend (VINERI)

Când `data_raport` este **vineri**, script-ul aplică o logică specială pentru a gestiona weekendul:

#### Intervalele pentru Vineri:
- **Ieșire Centru**: Doar vineri 00:00-23:59
- **Intrare Hub**: Vineri-Sâmbătă (conform orarului configurat)
- **Ieșire Hub**: Vineri-Sâmbătă (conform orarului configurat) 
- **Intrare Centru**: Sâmbătă 00:00 - Luni 16:59

#### Pentru celelalte zile:
- Toate intervalele folosesc logica standard (+1 zi)

### Pentru Raportul Statie-Hub:

**Fișier ieșire centru**:
- `Tip Scanare` = "Ieșire centru"
- `Scanare` între:
  - **Vineri**: `{vineri} 00:00` și `{vineri} 23:59` (doar vineri)
  - **Alte zile**: `{data_raport} 00:00` și `{data_raport} 23:59`

**Fișier intrare hub**:
- `Tip Scanare` = "Intrare centru"
- `Centru` = "BRASOV" / "SIBIU"
- `Scanare` între:
  - **Vineri - Brașov**: `{vineri} 15:30` și `{sâmbătă} 15:30`
  - **Vineri - Sibiu**: `{vineri} 21:00` și `{sâmbătă} 06:00`
  - **Alte zile - Brașov**: `{data_raport} 15:30` și `{data_raport+1} 15:30`
  - **Alte zile - Sibiu**: `{data_raport} 21:00` și `{data_raport+1} 06:00`

### Pentru Raportul Hub-Statie:

**Fișier ieșire hub**:
- `Tip Scanare` = "Ieșire centru"
- `Centru` = "BRASOV" / "SIBIU"
- `Scanare` între:
  - **Vineri - Brașov**: `{vineri} 15:30` și `{sâmbătă} 23:59`
  - **Vineri - Sibiu**: `{vineri} 21:00` și `{sâmbătă} 06:00`
  - **Alte zile - Brașov**: `{data_raport} 15:30` și `{data_raport+1} 23:59`
  - **Alte zile - Sibiu**: `{data_raport} 21:00` și `{data_raport+1} 06:00`

**Fișier intrare centru**:
- `Tip Scanare` = "Intrare centru"
- `Scanare` între:
  - **Vineri**: `{sâmbătă} 00:00` și `{luni} 16:59`
  - **Alte zile**: `{data_raport+1} 00:00` și `{data_raport+1} 16:59`

## 📊 Output

Scriptul generează 2 fișiere Excel pentru fiecare hub:
- `Raport Statie-Hub {Hub} {DD.MM}-{DD.MM}.xlsx`
- `Raport HUB-Statie {Hub} {DD.MM}-{DD.MM}.xlsx`

Exemple:
- `Raport Statie-Hub Brasov 23.07-24.07.xlsx`
- `Raport HUB-Statie Sibiu 23.07-24.07.xlsx`

Fiecare fișier conține 2 sheet-uri:
- **Detaliat**: Datele complete sortate după coloana "User"
- **Sumar**: Agregarea pe rute cu statistici și procente formatate

## 🧪 Testare

Pentru a testa scriptul cu date simulate:

```bash
python test_unified_generator.py
```

Testul va:
1. Crea date de test automat
2. Rula scriptul unificat
3. Verifica output-ul generat
4. Curăța fișierele temporare

## ⚠️ Note importante

1. **Format dată**: Folosește formatul `YYYY-MM-DD` pentru data raportului
2. **Fișiere temporare**: Scriptul creează și șterge automat fișiere temporare
3. **Verificare existență**: Scriptul verifică existența fișierului master înainte de rulare
4. **Backup**: Recomand să faci backup la fișierele originale înainte de prima utilizare

## 🔍 Exemple de utilizare

### Exemplu cu data específica:
```python
# Pentru raportul din 23 iulie 2025 (actualizează anul conform datelor tale)
generator = UnifiedHubReportGenerator(
    fisier_master="path/to/master_data.csv",
    data_raport="2025-07-23",
    base_url="/path/to/output/"
)
generator.genereaza_rapoarte()
```

### Exemplu cu mai multe date:
```python
# Pentru mai multe rapoarte (actualizează anul conform datelor tale)
date_rapoarte = ["2025-07-23", "2025-07-24", "2025-07-25"]

for data in date_rapoarte:
    print(f"Generez raportul pentru {data}...")
    generator = UnifiedHubReportGenerator(fisier_master, data, base_url)
    generator.genereaza_rapoarte()
```

## 🚨 Troubleshooting

### Erori comune:

1. **"Fișierul master nu există"**: Verifică calea către fișierul master
2. **"Date insuficiente"**: Verifică că fișierul master conține date pentru intervalul specificat
3. **"Fișiere utile lipsă"**: Verifică că toate fișierele din directorul `Utile/` există
4. **"Rapoarte goale deși se generează înregistrări"**: Verifică că fișierul `ruteBRASOV.csv` conține rutele corecte care trec prin hub-ul Brașov (rute cu 'BVH' în nume)

### Pentru debugging:
```python
# Activează afișarea detaliilor
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Migrare de la scripturile anterioare

Dacă ai folosit anterior `TRKReportGenerator1_v2.py` și `TRKRaportGenerator2_v2.py`:

1. **Combină datele**: Unifică toate datele într-un singur fișier master
2. **Actualizează căile**: Modifică `base_url` în script
3. **Testează**: Rulează `test_unified_generator.py` pentru verificare
4. **Compară**: Verifică că output-ul este identic cu cel anterior

---

📝 **Autor**: Generat cu Claude Code
🗓️ **Data**: Iulie 2024