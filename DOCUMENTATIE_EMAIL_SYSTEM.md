# HUB Reporting cu Email System

Sistem extins pentru generarea rapoartelor HUB cu funcționalitate de trimitere automată pe email, organizate pe centre.

## 🚀 Funcționalități Noi

### 1. Coloana "Centru" în Fișierele de Rute
- Adăugată coloana "Centru" în `ruteBrasov.csv` și `ruteSIBIU.csv`
- Mapare automată pe baza codurilor din numele rutelor
- Suport pentru toate centrele din rețea

### 2. Sistem de Email Automat
- Trimitere automată de rapoarte pe centre
- Template-uri HTML profesionale pentru email-uri
- Configurație flexibilă SMTP (Gmail, Outlook, etc.)
- Adrese email configurabile per centru

### 3. Istoric Rapoarte (SQLite)
- Salvare automată a istoricului pe ultimele 30 de zile
- Calcul medii pentru procente pe centru
- Baza de date optimizată pentru performanță
- Rapoarte agregat pe centre și rute

### 4. Raport Email cu Sumar 30 Zile
Tabelul din email conține:
- **Centru**: Numele centrului
- **Ruta**: Numele rutei
- **Nr Colete**: Numărul total de colete
- **Greutate**: Greutatea totală (kg)
- **Procent Iesire Centru**: Media procentului de ieșire
- **Procent Intrare Centru**: Media procentului de intrare

## 📁 Structura Fișierelor

```
HUBReporting/
├── unified_hub_report_generator.py      # Generator original (NESCHIMBAT)
├── email_reporting_system.py            # Sistem email și istoric
├── enhanced_hub_generator.py             # Generator extins cu email
├── update_rute_with_centres.py          # Script actualizare rute
├── setup_email_system.py                # Configurare inițială
├── demo_email_system.py                 # Demonstrație sistem
├── test_excel_format.py                 # Demo format Excel
├── migrate_config_to_utile.py           # Migrare fișiere în Utile
└── DOCUMENTATIE_EMAIL_SYSTEM.md         # Această documentație

Fișiere generate în directorul de lucru (folder Utile/):
├── Utile/email_config.json              # Credențiale SMTP
├── Utile/email_addresses_centre.xlsx    # Adrese email pe centre (Excel)
├── Utile/rapoarte_istoric.db            # Baza de date SQLite
└── Utile/email_reporting.log            # Log-uri sistem
```

## 🛠️ Instalare și Configurare

### 1. Migrare Fișiere în Utile (dacă sunt în locația veche)
```bash
python migrate_config_to_utile.py
```

### 2. Actualizare Fișiere Rute
```bash
python update_rute_with_centres.py
```

### 3. Configurare Email
```bash
python setup_email_system.py
```

Apoi editați (în folderul Utile/):
- `Utile/email_config.json` - credențiale SMTP
- `Utile/email_addresses_centre.xlsx` - adrese email per centru (Excel)

### 4. Test Sistem
```bash
python demo_email_system.py                # Test complet sistem
python test_excel_format.py                # Test și demo format Excel
```

## 🎯 Utilizare

### Generator Clasic (NESCHIMBAT)
```bash
python unified_hub_report_generator.py
```

### Generator cu Email
```bash
python enhanced_hub_generator.py
```

Opțiuni disponibile:
1. **Generează rapoarte cu email (complet)** - Generează rapoarte + trimite email-uri
2. **Generează doar rapoarte** - Doar generarea clasică + salvare istoric
3. **Trimite doar email-uri** - Din istoric existent
4. **Configurează email** - Creează template-urile
5. **Email de test** - Testare pentru un centru
6. **Vezi centre disponibile** - Lista centrelor cu date

### Script Programatic
```python
from enhanced_hub_generator import EnhancedHubGenerator

generator = EnhancedHubGenerator()

# Generare cu email
generator.generate_reports_with_email("2025-08-29", send_emails=True)

# Doar generare (fără email)
generator.generate_reports_with_email("2025-08-29", send_emails=False)

# Trimite email pentru un centru specific
generator.send_test_email("BUCUREȘTI", "2025-08-29")
```

## 📊 Configurare Adrese Email (Excel)

Fișierul `email_addresses_centre.xlsx` conține o foaie Excel cu următoarele coloane:

| Centru | Adrese_Email | Activ | Observatii |
|--------|-------------|-------|------------|
| BUCUREȘTI | manager.bucuresti@company.com; supervisor.bucuresti@company.com | DA | Adresele separate cu ; |
| ALBA IULIA | manager.alba@company.com | DA | Un singur email |
| ARAD | - | NU | Centru inactiv |

### Instrucțiuni editare:
- **Centru**: Numele centrului (nu modificați)
- **Adrese_Email**: Email-urile separate cu `;` (punct și virgulă)
- **Activ**: `DA` pentru centre active, `NU` pentru inactive
- **Observatii**: Note opționale

### Exemple adrese multiple:
```
manager@company.com; supervisor@company.com; director@company.com
```

## ⚙️ Configurare Email

### Gmail
```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "your_email@gmail.com",
    "password": "your_app_password",
    "sender_name": "HUB Reporting System"
}
```

**Important**: Pentru Gmail folosiți App Password, nu parola normală:
1. Activați 2-Factor Authentication
2. Generați App Password din Google Account Settings
3. Folosiți App Password în configurație

### Outlook/Hotmail
```json
{
    "smtp_server": "smtp.live.com",
    "smtp_port": 587,
    "email": "your_email@hotmail.com",
    "password": "your_password",
    "sender_name": "HUB Reporting System"
}
```

### Configurație Corporativă
```json
{
    "smtp_server": "mail.company.com",
    "smtp_port": 587,
    "email": "reports@company.com",
    "password": "company_password",
    "sender_name": "HUB Reporting System"
}
```

## 📧 Format Email

Fiecare email conține:
- **Subiect**: "Raport Centru [NUME_CENTRU] - [DATA]"
- **Tabel HTML** cu datele din ultimele 30 zile
- **Totalizare automată** pentru centru
- **Design profesional** cu stilizare CSS

Exemplu tabel:

| Centru | Ruta | Nr Colete | Greutate | Procent Iesire | Procent Intrare |
|--------|------|-----------|----------|----------------|-----------------|
| BUCUREȘTI | BVH-ROM | 1,250 | 2,750.50 | 95.20% | 92.80% |
| BUCUREȘTI | ROM-BVH | 1,100 | 2,450.75 | 93.60% | 94.10% |
| **TOTAL** | - | **2,350** | **5,201.25** | **94.40%** | **93.45%** |

## 🗄️ Baza de Date

Schema SQLite:
```sql
CREATE TABLE rapoarte_istoric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_raport DATE NOT NULL,
    hub VARCHAR(50) NOT NULL,
    tip_raport VARCHAR(50) NOT NULL,
    centru VARCHAR(100) NOT NULL,
    ruta VARCHAR(100) NOT NULL,
    nr_colete INTEGER NOT NULL,
    greutate REAL NOT NULL,
    procent_iesire_centru REAL NOT NULL,
    procent_intrare_centru REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📊 Centre Mapate

Sistemul include mapping pentru toate centrele din rețea:
- ALBA IULIA, ARAD, BACĂU, BISTRIȚA, BĂRĂGAN
- BRĂILA, BESTFACTOR, BUZĂU, CLUJ, CĂLĂRAȘI
- CÂMPINA, CRAIOVA, CONSTANȚA, DROBETA, DEVA
- FOCȘANI, FĂGĂRAȘ, GALAȚI, IAȘI, LUGOJ
- MEDIAȘ, ONEȘTÎ, ORADEA, OTOPENI, PITEȘTI
- PLOIEȘTI, POPEȘTI, REȘIȚA, BUCUREȘTI, RÂMNICU VÂLCEA
- SFÂNTU GHEORGHE, SIBIU, SĂLAJ, SLATINA, SATU MARE
- TIMIȘOARA, TARGU JIU, TÂRGU MUREȘ, TÂRGOVIȘTE
- TULCEA, TURNUL NOVAC, URZICENI, ZALĂU, NUGAT

## 🔧 Mentenanță

### Log-uri Îmbunătățite
Toate operațiunile sunt înregistrate în:
- `Utile/email_reporting.log` - log-uri detaliate sistem
- Console output pentru feedback real-time

**Log-urile includ:**
- 📧 Adresele email către care se trimit rapoartele
- 🔗 Serverul SMTP și portul folosit (ex: mail.company.com:587)
- 👤 Utilizatorul pentru autentificare SMTP
- 📄 Subiectul email-ului și mărimea conținutului HTML
- ✅ Confirmarea trimiterii cu succes către fiecare destinatar
- ⚠️ Erorile detaliate cu stack trace în caz de probleme

**Exemplu log:**
```
2025-08-29 15:59:52,968 - INFO - Pregătesc email pentru centrul ALBA IULIA → destinatari: manager.alba@company.com, supervisor.alba@company.com
2025-08-29 15:59:52,968 - INFO - Email configurat: 'Raport Centru ALBA IULIA - 28.08.2025' de la Marius Teler (2,352 caractere HTML)
2025-08-29 15:59:52,968 - INFO - Conectare la SMTP: mail.curierdragonstar.ro:587
2025-08-29 15:59:53,109 - INFO - Autentificare reușită pentru marius.teler@curierdragonstar.ro
2025-08-29 15:59:53,189 - INFO - Email trimis cu succes pentru centrul ALBA IULIA → manager.alba@company.com, supervisor.alba@company.com
```

### Backup
Recomandări backup (toate în folderul Utile/):
- `Utile/rapoarte_istoric.db` - baza de date
- `Utile/email_config.json` - configurația email
- `Utile/email_addresses_centre.xlsx` - adresele email (Excel)

### Performanță
- Index-uri optimizate în SQLite
- Batch processing pentru email-uri
- Cache pentru mapări centre
- Limitare memorie pentru fișiere mari

## 🆘 Depanare

### Email-uri nu se trimit
1. Verificați credențialele în `email_config.json`
2. Pentru Gmail, folosiți App Password
3. Verificați conexiunea internet
4. Consultați `email_reporting.log`

### Lipsesc centre
1. Rulați `update_rute_with_centres.py`
2. Verificați mapping-ul în scriptul de actualizare
3. Adăugați centre noi manual dacă este necesar

### Performanță lentă
1. Verificați mărimea bazei de date
2. Rulați VACUUM pe SQLite periodic
3. Limitați intervalul de date pentru rapoarte mari

## 📝 Note Importante

- **Sistemul original rămâne NESCHIMBAT** - `unified_hub_report_generator.py`
- **Compatibilitate completă** cu workflow-ul existent
- **Extensibilitate** - ușor de extins cu noi funcționalități
- **Securitate** - credențialele email sunt stocate local
- **Logging complet** pentru monitorizare și depanare

## 🎖️ Caracteristici Tehnice

- **Python 3.7+** compatibil
- **SQLite** pentru persistență
- **Pandas** pentru procesare date
- **SMTP** pentru email (SSL/TLS)
- **HTML/CSS** pentru formatare email
- **Error handling** robust
- **Logging** structurat
- **Memory efficient** pentru fișiere mari