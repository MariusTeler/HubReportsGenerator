#!/usr/bin/env python3
"""
Sistem de raportare email pentru HUB Reporting
- Salvează istoricul rapoartelor în SQLite
- Trimite rapoarte pe email organizate pe centre
- Calculează media pe ultimele 30 de zile
"""

import pandas as pd
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
from unified_hub_report_generator import UnifiedHubReportGenerator, BRASOV_CONFIG, SIBIU_CONFIG

class EmailReportingSystem:
    def __init__(self, base_path=None):
        if base_path is None:
            base_path = '/Users/telermarius/Library/CloudStorage/Dropbox/DSC/Rapoarte/HUB Brasov/'
        
        self.base_path = base_path
        self.utile_path = os.path.join(base_path, 'Utile')
        
        # Asigură că folderul Utile există
        os.makedirs(self.utile_path, exist_ok=True)
        
        # Toate fișierele de configurare în folderul Utile
        self.db_path = os.path.join(self.utile_path, 'rapoarte_istoric.db')
        self.config_path = os.path.join(self.utile_path, 'email_config.json')
        self.email_addresses_path = os.path.join(self.utile_path, 'email_addresses_centre.xlsx')
        
        # Configurare logging
        log_path = os.path.join(self.utile_path, 'email_reporting.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Inițializează baza de date
        self._init_database()
    
    def _init_database(self):
        """Inițializează baza de date SQLite pentru istoric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabel pentru istoricul rapoartelor
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rapoarte_istoric (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data_raport, hub, tip_raport, centru, ruta)
            )
        ''')
        
        # Index pentru performanță
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_centru 
            ON rapoarte_istoric (data_raport, centru, hub)
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info(f"Baza de date inițializată: {self.db_path}")
    
    def save_report_to_history(self, data_raport, hub_name, tip_raport, raport_data, file_path=None):
        """Salvează datele raportului în istoric cu logică consolidată pentru ambele tipuri de raport"""
        conn = sqlite3.connect(self.db_path)
        
        # Salvez doar rapoartele Statie-Hub - pentru Hub-Statie nu salvez separat
        if tip_raport != 'Statie-Hub':
            conn.close()
            return True
        
        # Încearcă să găsească fișierul Hub-Statie corespondent pentru a prelua procent intrare centru
        raport_data_hub_statie = None
        if file_path:
            hub_statie_file = file_path.replace('Statie-Hub', 'HUB-Statie')
            if os.path.exists(hub_statie_file):
                try:
                    raport_data_hub_statie = pd.read_excel(hub_statie_file, sheet_name='Sumar')
                    self.logger.info(f"Găsit fișier Hub-Statie corespondent: {hub_statie_file}")
                except Exception as e:
                    self.logger.warning(f"Eroare la citirea fișierului Hub-Statie {hub_statie_file}: {e}")
        
        # Încarcă fișierul de echivalențe rute pe baza hub-ului
        if hub_name.upper() == 'BRASOV':
            echivalente_file = os.path.join(self.base_path, 'Utile/ruteBrasov_Echivalenta.xlsx')
        else:  # SIBIU
            echivalente_file = os.path.join(self.base_path, 'Utile/ruteSibiu_echivalenta.xlsx')
            
        echivalente_dict = {}
        
        if os.path.exists(echivalente_file):
            try:
                echivalente_df = pd.read_excel(echivalente_file)
                if hub_name.upper() == 'BRASOV':
                    # Pentru Brasov: Rute Tara -> Rute Brasov
                    echivalente_dict = dict(zip(echivalente_df['Rute Tara'], echivalente_df['Rute Brasov']))
                else:
                    # Pentru Sibiu: RutaEchivalenta (din Statie-Hub) -> RutaOriginala (din Hub-Statie)
                    echivalente_dict = dict(zip(echivalente_df['RutaEchivalenta'], echivalente_df['RutaOriginala']))
                self.logger.info(f"Încărcat {len(echivalente_dict)} echivalențe de rute pentru {hub_name}")
            except Exception as e:
                self.logger.warning(f"Eroare la încărcarea echivalențelor de rute: {e}")
        
        # Încarcă fișierul de rute pentru a obține centrele
        if hub_name.upper() == 'BRASOV':
            rute_file = os.path.join(self.base_path, 'Utile/ruteBrasov.csv')
        else:
            rute_file = os.path.join(self.base_path, 'Utile/ruteSIBIU.csv')
        
        if not os.path.exists(rute_file):
            self.logger.error(f"Fișierul de rute nu există: {rute_file}")
            return False
        
        rute_df = pd.read_csv(rute_file)
        rute_to_centru = dict(zip(rute_df['Denumire'], rute_df['Centru']))
        
        try:
            cursor = conn.cursor()
            
            for _, row in raport_data.iterrows():
                if row['Ruta'] == 'Total':
                    continue
                    
                centru = rute_to_centru.get(row['Ruta'], 'NECUNOSCUT')
                
                # Procent Iesire Centru din fișierul Statie-Hub
                procent_iesire = row.get('Procent Iesire Centru', 0) * 100
                
                # Procent Intrare Centru din fișierul Hub-Statie (folosind tabelul de echivalențe)
                procent_intrare = 0
                if raport_data_hub_statie is not None:
                    ruta_statie_hub = row['Ruta']  # ex: ALB-SBH
                    
                    # Găsește ruta echivalentă din tabelul de echivalențe
                    ruta_echivalenta = echivalente_dict.get(ruta_statie_hub)
                    if ruta_echivalenta:
                        # Caută ruta echivalentă în datele Hub-Statie
                        matching_rows = raport_data_hub_statie[raport_data_hub_statie['Ruta'] == ruta_echivalenta]
                        if not matching_rows.empty:
                            procent_intrare = matching_rows.iloc[0].get('Procent Intrare Centru', 0) * 100
                            self.logger.info(f"Ruta {ruta_statie_hub} -> {ruta_echivalenta}: Procent intrare {procent_intrare:.2f}%")
                        else:
                            self.logger.warning(f"Nu s-a găsit ruta echivalentă {ruta_echivalenta} în Hub-Statie pentru {ruta_statie_hub}")
                    else:
                        self.logger.warning(f"Nu s-a găsit echivalența pentru ruta {ruta_statie_hub}")
                else:
                    self.logger.warning(f"Nu s-a găsit fișierul Hub-Statie corespondent pentru {file_path}")
                
                cursor.execute('''
                    INSERT OR REPLACE INTO rapoarte_istoric 
                    (data_raport, hub, tip_raport, centru, ruta, nr_colete, 
                     greutate, procent_iesire_centru, procent_intrare_centru)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_raport, hub_name, tip_raport, centru, row['Ruta'],
                    int(row['Nr Colete']), float(row['Greutate']),
                    float(procent_iesire), float(procent_intrare)
                ))
            
            conn.commit()
            self.logger.info(f"Salvat în istoric: {data_raport} - {hub_name} - {tip_raport}")
            return True
            
        except Exception as e:
            self.logger.error(f"Eroare la salvarea în istoric: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_centre_report_last_30_days(self, centru, data_raport):
        """Obține raportul pentru un centru pe ultimele 30 de zile"""
        conn = sqlite3.connect(self.db_path)
        
        data_start = (datetime.strptime(data_raport, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT 
                data_raport,
                centru,
                ruta,
                nr_colete,
                greutate,
                procent_iesire_centru,
                procent_intrare_centru
            FROM rapoarte_istoric
            WHERE centru = ? 
                AND data_raport >= ? 
                AND data_raport <= ?
            ORDER BY data_raport DESC, ruta
        '''
        
        df = pd.read_sql_query(query, conn, params=(centru, data_start, data_raport))
        conn.close()
        
        return df
    
    def create_email_config_template(self):
        """Creează template pentru configurația email"""
        config_template = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email": "your_email@gmail.com", 
            "password": "your_app_password",
            "sender_name": "HUB Reporting System"
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_template, f, indent=4, ensure_ascii=False)
        
        self.logger.info(f"Template configurație email creat: {self.config_path}")
        return self.config_path
    
    def create_email_addresses_template(self):
        """Creează template Excel pentru adresele email pe centre"""
        # Date template pentru Excel
        data = []
        centres_emails = {
            "ALBA IULIA": "manager.alba@company.com; supervisor.alba@company.com",
            "ARAD": "manager.arad@company.com",
            "BACĂU": "manager.bacau@company.com",
            "BISTRIȚA": "manager.bistrita@company.com",
            "BĂRĂGAN": "manager.baragan@company.com",
            "BRĂILA": "manager.braila@company.com",
            "BESTFACTOR": "manager.bestfactor@company.com",
            "BUZĂU": "manager.buzau@company.com",
            "CLUJ": "manager.cluj@company.com",
            "CĂLĂRAȘI": "manager.calarasi@company.com",
            "CÂMPINA": "manager.campina@company.com",
            "CRAIOVA": "manager.craiova@company.com",
            "CONSTANȚA": "manager.constanta@company.com",
            "DROBETA": "manager.drobeta@company.com",
            "DEVA": "manager.deva@company.com",
            "FOCȘANI": "manager.focsani@company.com",
            "FĂGĂRAȘ": "manager.fagaras@company.com",
            "GALAȚI": "manager.galati@company.com",
            "IAȘI": "manager.iasi@company.com",
            "LUGOJ": "manager.lugoj@company.com",
            "MEDIAȘ": "manager.medias@company.com",
            "ONEȘTÎ": "manager.onesti@company.com",
            "ORADEA": "manager.oradea@company.com",
            "OTOPENI": "manager.otopeni@company.com",
            "PITEȘTI": "manager.pitesti@company.com",
            "PLOIEȘTI": "manager.ploiesti@company.com",
            "POPEȘTI": "manager.popesti@company.com",
            "REȘIȚA": "manager.resita@company.com",
            "BUCUREȘTI": "manager.bucuresti@company.com",
            "RÂMNICU VÂLCEA": "manager.ramnicu@company.com",
            "SFÂNTU GHEORGHE": "manager.sfantu@company.com",
            "SIBIU": "manager.sibiu@company.com",
            "SĂLAJ": "manager.salaj@company.com",
            "SLATINA": "manager.slatina@company.com",
            "SATU MARE": "manager.satu@company.com",
            "TIMIȘOARA": "manager.timisoara@company.com",
            "TARGU JIU": "manager.targu@company.com",
            "TÂRGU MUREȘ": "manager.mures@company.com",
            "TÂRGOVIȘTE": "manager.targoviste@company.com",
            "TULCEA": "manager.tulcea@company.com",
            "TURNUL NOVAC": "manager.novac@company.com",
            "URZICENI": "manager.urziceni@company.com",
            "ZALĂU": "manager.zalau@company.com",
            "NUGAT": "manager.nugat@company.com"
        }
        
        for centru, emails in centres_emails.items():
            data.append({
                'Centru': centru,
                'Adrese_Email': emails,
                'Activ': 'DA',
                'Observatii': 'Adresele separate cu ; (punct și virgulă)'
            })
        
        df = pd.DataFrame(data)
        
        # Salvează în Excel cu formatare
        with pd.ExcelWriter(self.email_addresses_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Email_Addresses', index=False)
            
            # Formatarea coloanelor
            worksheet = writer.sheets['Email_Addresses']
            worksheet.column_dimensions['A'].width = 20  # Centru
            worksheet.column_dimensions['B'].width = 50  # Adrese Email
            worksheet.column_dimensions['C'].width = 10  # Activ
            worksheet.column_dimensions['D'].width = 40  # Observații
        
        self.logger.info(f"Template Excel adrese email creat: {self.email_addresses_path}")
        return self.email_addresses_path
    
    def load_email_config(self):
        """Încarcă configurația email"""
        if not os.path.exists(self.config_path):
            self.create_email_config_template()
            raise FileNotFoundError(f"Configurația email nu există. Template creat la: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_email_addresses(self):
        """Încarcă adresele email pentru centre din Excel"""
        if not os.path.exists(self.email_addresses_path):
            self.create_email_addresses_template()
            raise FileNotFoundError(f"Fișierul Excel cu adrese email nu există. Template creat la: {self.email_addresses_path}")
        
        try:
            # Citește fișierul Excel
            df = pd.read_excel(self.email_addresses_path, sheet_name='Email_Addresses')
            
            # Filtrează doar centrele active
            df_active = df[df['Activ'].str.upper() == 'DA']
            
            # Convertește în dicționar
            email_dict = {}
            for _, row in df_active.iterrows():
                centru = row['Centru']
                emails_str = str(row['Adrese_Email'])
                
                # Procesează adresele email (separate cu ; sau ,)
                emails = []
                if pd.notna(emails_str) and emails_str.strip():
                    # Separă pe ; sau ,
                    raw_emails = emails_str.replace(',', ';').split(';')
                    emails = [email.strip() for email in raw_emails if email.strip()]
                
                if emails:
                    email_dict[centru] = emails
            
            return email_dict
            
        except Exception as e:
            raise Exception(f"Eroare la citirea fișierului Excel: {str(e)}")
    
    def generate_email_report_html(self, centru, raport_data, data_raport=None):
        """Generează raportul HTML pentru email"""
        if raport_data.empty:
            return f"""
            <h2>Raport Centru {centru} - Ultimele 30 zile</h2>
            <p>Nu există date disponibile pentru acest centru în ultimele 30 de zile.</p>
            """
        
        # Data raportului pentru afișare
        data_display = data_raport if data_raport else datetime.now().strftime('%Y-%m-%d')
        
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0; 
                    font-size: 13px;
                    table-layout: fixed;
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 8px 10px; 
                    text-align: left;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                th {{ 
                    background-color: #34495e; 
                    color: white; 
                    font-weight: bold; 
                    text-align: center;
                    font-size: 12px;
                }}
                /* Dimensiuni fixe pentru coloane */
                th:nth-child(1), td:nth-child(1) {{ width: 80px; text-align: center; }} /* Data */
                th:nth-child(2), td:nth-child(2) {{ width: 120px; }} /* Centru */
                th:nth-child(3), td:nth-child(3) {{ width: 100px; }} /* Ruta */
                th:nth-child(4), td:nth-child(4) {{ width: 80px; text-align: right; }} /* Nr Colete */
                th:nth-child(5), td:nth-child(5) {{ width: 90px; text-align: right; }} /* Greutate */
                th:nth-child(6), td:nth-child(6) {{ width: 110px; text-align: right; }} /* Procent Iesire */
                th:nth-child(7), td:nth-child(7) {{ width: 110px; text-align: right; }} /* Procent Intrare */
                
                .header {{ 
                    color: #2c3e50; 
                    margin-bottom: 20px; 
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 15px;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    color: #7f8c8d; 
                    font-size: 11px; 
                    text-align: center;
                    border-top: 1px solid #ecf0f1;
                    padding-top: 15px;
                }}
                .percent {{ text-align: right; }}
                .total-row {{
                    background-color: #3498db !important;
                    color: white !important;
                    font-weight: bold;
                }}
                .total-row td {{
                    background-color: #3498db !important;
                    color: white !important;
                }}
                .intro-text {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #3498db;
                }}
                .objectives {{
                    background-color: #e8f5e8;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #27ae60;
                }}
                .objectives ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .closing {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #ffc107;
                }}
                /* Stiluri pentru procente sub 97% */
                .low-percent {{
                    background-color: #ffebee !important;
                    color: #c62828 !important;
                    font-weight: bold;
                }}
                .good-percent {{
                    background-color: #e8f5e8 !important;
                    color: #2e7d32 !important;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Raport Centru {centru}</h2>
                    <p style="margin: 5px 0; color: #7f8c8d;">Monitorizare Scanare IN/OUT TRK - Ultimele 30 zile</p>
                </div>
                
                <div class="intro-text">
                    <p><strong>Bună ziua,</strong></p>
                    <p>Începând cu 1 septembrie, am demarat monitorizarea activă a ratei de scanare IN/OUT TRK pentru toate stațiile și hub-urile DSC.<br/>
                    <strong>Obiectiv:</strong> Menținerea unui nivel minim de 97% este esențială pentru eficiența proceselor și calitatea serviciilor.<br/>
                    <strong>Probleme:</strong> Suntem conștienți că pot exista situații excepționale în care unele AWB-uri nu pot fi procesate, drept urmare avem rugămintea ca situațiile recurente să le sesizați pentru a lua măsuri și a le remedia.</p>
                </div>
                
                <p><strong>Mai jos găsiți statistica scanărilor de intrare/ieșire pentru stația dumneavoastră:</strong></p>
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Centru</th>
                        <th>Ruta</th>
                        <th>Nr Colete</th>
                        <th>Greutate (kg)</th>
                        <th>Procent Iesire Centru</th>
                        <th>Procent Intrare Centru</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        total_colete = 0
        total_greutate = 0
        
        for _, row in raport_data.iterrows():
            total_colete += int(row['nr_colete'])
            total_greutate += float(row['greutate'])
            
            html += f"""
                    <tr>
                        <td>{row['data_raport']}</td>
                        <td>{row['centru']}</td>
                        <td>{row['ruta']}</td>
                        <td style="text-align: right;">{int(row['nr_colete']):,}</td>
                        <td style="text-align: right;">{float(row['greutate']):.2f}</td>
                        <td class="percent">{float(row['procent_iesire_centru']):.2f}%</td>
                        <td class="percent">{float(row['procent_intrare_centru']):.2f}%</td>
                    </tr>
            """
        
        avg_iesire = raport_data['procent_iesire_centru'].mean()
        avg_intrare = raport_data['procent_intrare_centru'].mean()
        
        html += f"""
                    <tr style="background-color: #e8f4fd; font-weight: bold;">
                        <td>-</td>
                        <td>TOTAL</td>
                        <td>-</td>
                        <td style="text-align: right;">{total_colete:,}</td>
                        <td style="text-align: right;">{total_greutate:.2f}</td>
                        <td class="percent">{avg_iesire:.2f}%</td>
                        <td class="percent">{avg_intrare:.2f}%</td>
                    </tr>
                </tbody>
            </table>
            <div>
            <p>Pentru a asigura atingerea obiectivelor, va rugam:</p>
            <ul>
                <li>Sa identificati factorii care au determinat rata actuala;</li>
                <li>Sa propuneti masuri concrete pentru cresterea acestui indicator.</li>
            </ul>
            </div>
            <div>
            <p>Colaborarea ca feedback-ul dumneavoastra sunt foarte important pentru imbuntatirea continua a performantei</br>
            Echipa noastra va sta la dispozitie pentru clarificari punctuale, sesiuni rapide de training sau asistenta tehnica.</br>
            </p>
            <p>Va multumim pentru implicare si colaborare!</p>
            </div>
            
            <div class="footer">
                <p>Data generare: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                <p>Datele totale reprezintă media pe ultimele 30 de zile.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_centre_report(self, centru, data_raport):
        """Trimite raportul pentru un centru specific"""
        try:
            # Încarcă configurațiile
            email_config = self.load_email_config()
            email_addresses = self.load_email_addresses()
            
            # Verifică dacă centrul are adrese email
            if centru not in email_addresses:
                self.logger.warning(f"Nu există adrese email configurate pentru centrul: {centru}")
                return False
            
            # Log adresele găsite pentru centru
            addresses_str = ', '.join(email_addresses[centru])
            self.logger.info(f"Pregătesc email pentru centrul {centru} → destinatari: {addresses_str}")
            
            # Obține datele pentru raport
            raport_data = self.get_centre_report_last_30_days(centru, data_raport)
            
            if raport_data.empty:
                self.logger.info(f"Nu există date pentru centrul {centru} în ultimele 30 de zile")
                return True
            
            # Generează HTML-ul raportului
            html_content = self.generate_email_report_html(centru, raport_data, data_raport)
            
            # Configurează email-ul
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{email_config['sender_name']} <{email_config['email']}>"
            msg['To'] = ', '.join(email_addresses[centru])
            subject = f"Raport scanare IN/OUT TRK {centru} - {datetime.strptime(data_raport, '%Y-%m-%d').strftime('%d.%m.%Y')}"
            msg['Subject'] = subject
            
            # Adaugă conținutul HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Log detalii email
            self.logger.info(f"Email configurat: '{subject}' de la {email_config['sender_name']} ({len(html_content):,} caractere HTML)")
            
            # Trimite email-ul
            self.logger.info(f"Conectare la SMTP: {email_config['smtp_server']}:{email_config['smtp_port']}")
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            self.logger.info(f"Autentificare reușită pentru {email_config['email']}")
            
            text = msg.as_string()
            server.sendmail(email_config['email'], email_addresses[centru], text)
            server.quit()
            
            # Log detaliat cu adresele email
            addresses_str = ', '.join(email_addresses[centru])
            self.logger.info(f"Email trimis cu succes pentru centrul {centru} → {addresses_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"Eroare la trimiterea email pentru centrul {centru}: {str(e)}")
            return False
    
    def send_all_centre_reports(self, data_raport):
        """Trimite rapoarte pentru toate centrele care au date"""
        conn = sqlite3.connect(self.db_path)
        
        # Obține lista centrelor cu date
        query = '''
            SELECT DISTINCT centru 
            FROM rapoarte_istoric 
            WHERE data_raport >= ? 
            AND centru != 'NECUNOSCUT'
            ORDER BY centru
        '''
        
        data_start = (datetime.strptime(data_raport, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor = conn.cursor()
        cursor.execute(query, (data_start,))
        centre = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.logger.info(f"Se trimit rapoarte pentru {len(centre)} centre")
        
        success_count = 0
        failed_centres = []
        
        for i, centru in enumerate(centre):
            if self.send_centre_report(centru, data_raport):
                success_count += 1
            else:
                failed_centres.append(centru)
            
            # Adaugă delay între email-uri pentru a nu bloca serverul (excepție pentru ultimul)
            if i < len(centre) - 1:  # Nu pune delay după ultimul email
                delay_seconds = 2  # 2 secunde delay
                self.logger.info(f"Pauză de {delay_seconds} secunde înainte de următorul email...")
                import time
                time.sleep(delay_seconds)
        
        # Log sumar cu detalii
        self.logger.info(f"Rapoarte trimise cu succes: {success_count}/{len(centre)}")
        if failed_centres:
            self.logger.warning(f"Centre cu erori la trimiterea email: {', '.join(failed_centres)}")
        
        return success_count, len(centre)

def main():
    """Funcția principală pentru testare"""
    # Inițializează sistemul
    email_system = EmailReportingSystem()
    
    # Creează template-urile dacă nu există
    try:
        email_system.load_email_config()
    except FileNotFoundError as e:
        print(f"⚠️ {e}")
        print("Completați configurația email și rulați din nou.")
        return
    
    try:
        email_system.load_email_addresses()
    except FileNotFoundError as e:
        print(f"⚠️ {e}")
        print("Actualizați adresele email pentru centre și rulați din nou.")
        return
    
    print("✅ Sistemul de email reporting a fost inițializat cu succes!")
    print(f"📧 Configurație email: {email_system.config_path}")
    print(f"📬 Adrese email centre: {email_system.email_addresses_path}")
    print(f"🗄️ Baza de date istoric: {email_system.db_path}")

if __name__ == "__main__":
    main()