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
import matplotlib
matplotlib.use('Agg')  # Backend non-interactiv pentru server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
    
    def get_centre_report_last_3_days(self, centru, data_raport):
        """Obține raportul pentru un centru pe ultimele 3 zile cu statistici zilnice"""
        conn = sqlite3.connect(self.db_path)
        
        # Calculăm data de start pentru ultimele 3 zile (inclusiv data raportului)
        data_end = datetime.strptime(data_raport, '%Y-%m-%d')
        data_start = data_end - timedelta(days=2)  # 3 zile: azi, ieri, alaltăieri
        data_start_str = data_start.strftime('%Y-%m-%d')
        
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
        
        df = pd.read_sql_query(query, conn, params=(centru, data_start_str, data_raport))
        conn.close()
        
        return df
    
    def get_daily_stats_last_3_days(self, centru, data_raport):
        """Calculează statistici zilnice pentru ultimele 3 zile"""
        df = self.get_centre_report_last_3_days(centru, data_raport)
        
        if df.empty:
            return pd.DataFrame()
        
        # Grupăm pe zi și calculăm statisticile
        daily_stats = df.groupby('data_raport').agg({
            'nr_colete': 'sum',
            'greutate': 'sum',
            'procent_iesire_centru': 'mean',
            'procent_intrare_centru': 'mean'
        }).round(2)
        
        # Calculăm diferențele și tendințele
        daily_stats = daily_stats.sort_index()
        daily_stats['diferenta_colete'] = daily_stats['nr_colete'].diff()
        daily_stats['procent_diferenta'] = ((daily_stats['nr_colete'].diff() / daily_stats['nr_colete'].shift(1)) * 100).round(1)
        
        # Adăugăm tendința
        daily_stats['tendinta'] = daily_stats['diferenta_colete'].apply(
            lambda x: '📈 Creștere' if x > 0 else '📉 Scădere' if x < 0 else '➡️ Constant'
        )
        
        # Pentru prima zi (nu are diferență)
        daily_stats.loc[daily_stats.index[0], 'tendinta'] = '📊 Bază'
        
        return daily_stats
    
    def generate_evolution_chart(self, centru, data_raport):
        """Generează graficul de evoluție pentru ultimele 3 zile"""
        daily_stats = self.get_daily_stats_last_3_days(centru, data_raport)
        
        if daily_stats.empty:
            return None
        
        # Configurare matplotlib pentru română
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        
        # Creează figura
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        # Pregătește datele
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in daily_stats.index]
        scanari = daily_stats['nr_colete'].values
        
        # Graficul principal - linie cu puncte
        ax.plot(dates, scanari, marker='o', linewidth=3, markersize=8, 
                color='#3498db', markerfacecolor='#2980b9', markeredgecolor='white', 
                markeredgewidth=2, label='Scanări zilnice')
        
        # Adaugă bare subtiri pentru claritate
        ax.bar(dates, scanari, alpha=0.3, color='#3498db', width=0.5)
        
        # Adaugă valorile pe grafic
        for i, (date, value) in enumerate(zip(dates, scanari)):
            ax.annotate(f'{int(value):,}', (date, value), 
                       textcoords="offset points", xytext=(0,10), 
                       ha='center', va='bottom', fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                               edgecolor='#3498db', alpha=0.8))
        
        # Calculează și afișează media
        media = scanari.mean()
        ax.axhline(y=media, color='#e74c3c', linestyle='--', alpha=0.7, 
                  label=f'Media: {int(media):,} scanări')
        
        # Configurare axe
        ax.set_xlabel('Data', fontweight='bold')
        ax.set_ylabel('Numărul de scanări', fontweight='bold')
        ax.set_title(f'Evoluția scanărilor - {centru}\nUltimele 3 zile', 
                    fontweight='bold', pad=20)
        
        # Formatare axă X pentru date
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center')
        
        # Grid pentru claritate
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Legende
        ax.legend(loc='upper right', framealpha=0.9)
        
        # Ajustare layout
        plt.tight_layout()
        
        # Salvează graficul
        chart_path = os.path.join(self.utile_path, f'chart_{centru}_{data_raport}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()  # Închide figura pentru a elibera memoria
        
        return chart_path
    
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
        """Generează raportul HTML pentru email - ULTIMELE 3 ZILE cu grafic"""
        # Obține statisticile zilnice pentru ultimele 3 zile
        daily_stats = self.get_daily_stats_last_3_days(centru, data_raport)
        
        if daily_stats.empty:
            return f"""
            <html>
            <body>
                <h2>Raport Centru {centru} - Ultimele 3 zile</h2>
                <p>Nu există date disponibile pentru acest centru în ultimele 3 zile.</p>
            </body>
            </html>
            """
        
        # Data raportului pentru afișare
        data_display = data_raport if data_raport else datetime.now().strftime('%Y-%m-%d')
        data_display_formatted = datetime.strptime(data_display, '%Y-%m-%d').strftime('%d.%m.%Y')
        
        # Calculează media și observațiile
        media_zilnica = daily_stats['nr_colete'].mean()
        zi_maxima = daily_stats['nr_colete'].idxmax()
        zi_maxima_formatted = datetime.strptime(zi_maxima, '%Y-%m-%d').strftime('%d.%m')
        
        # Generează tabelul cu statistici zilnice
        table_rows = ""
        for data, row in daily_stats.iterrows():
            data_formatted = datetime.strptime(data, '%Y-%m-%d').strftime('%d.%m')
            diferenta_str = ""
            if pd.notna(row['diferenta_colete']):
                semn = "+" if row['diferenta_colete'] > 0 else ""
                diferenta_str = f"{semn}{int(row['diferenta_colete'])}"
                if pd.notna(row['procent_diferenta']):
                    diferenta_str += f" ({semn}{row['procent_diferenta']:.1f}%)"
            else:
                diferenta_str = "-"
            
            table_rows += f"""
                <tr>
                    <td style="text-align: center;">{data_formatted}</td>
                    <td style="text-align: right; font-weight: bold;">{int(row['nr_colete']):,}</td>
                    <td style="text-align: center;">{diferenta_str}</td>
                    <td style="text-align: center;">{row['tendinta']}</td>
                </tr>
            """
        
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    max-width: 900px; 
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
                .header {{ 
                    color: #2c3e50; 
                    margin-bottom: 20px; 
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 15px;
                }}
                .stats-table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0; 
                    font-size: 14px;
                    background-color: white;
                }}
                .stats-table th, .stats-table td {{ 
                    border: 1px solid #ddd; 
                    padding: 12px 8px; 
                    text-align: left;
                }}
                .stats-table th {{ 
                    background-color: #34495e; 
                    color: white; 
                    font-weight: bold; 
                    text-align: center;
                    font-size: 13px;
                }}
                .intro-text {{
                    background-color: #e8f4fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #3498db;
                }}
                .summary-box {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #28a745;
                }}
                .chart-info {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid #ffc107;
                    text-align: center;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    color: #7f8c8d; 
                    font-size: 11px; 
                    text-align: center;
                    border-top: 1px solid #ecf0f1;
                    padding-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 Raport Scanări - {centru}</h2>
                    <p style="margin: 5px 0; color: #7f8c8d;">Ultimele 3 zile - {data_display_formatted}</p>
                </div>
                
                <div class="intro-text">
                    <p><strong>Bună ziua,</strong></p>
                    <p>Vă transmitem situația detaliată pentru ultimele 3 zile de activitate, 
                    împreună cu graficul de evoluție pentru o vizualizare clară a tendințelor.</p>
                </div>
                
                <h3>📋 SITUAȚIA DETALIATĂ</h3>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Scanări</th>
                            <th>Diferența</th>
                            <th>Tendința</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <div class="summary-box">
                    <h4>💡 OBSERVAȚII</h4>
                    <ul>
                        <li><strong>Media zilnică:</strong> {int(media_zilnica):,} scanări</li>
                        <li><strong>Zi cu cele mai multe scanări:</strong> {zi_maxima_formatted}</li>
                        <li><strong>Evoluția:</strong> Vezi graficul atașat pentru tendințe detaliate</li>
                    </ul>
                </div>
                
                <div class="chart-info">
                    <h4>📈 GRAFIC DE EVOLUȚIE</h4>
                    <p>Graficul cu evoluția scanărilor pe ultimele 3 zile este atașat la acest email.<br/>
                    <em>Graficul arată media zilnică și tendințele pentru o analiză vizuală completă.</em></p>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #27ae60;">
                    <p><strong>Pentru optimizarea continuă:</strong></p>
                    <ul>
                        <li>Analizați tendințele din grafic pentru identificarea cauzelor</li>
                        <li>Propuneți măsuri concrete pentru îmbunătățirea performanțelor</li>
                        <li>Raportați situațiile excepționale pentru rezolvare rapidă</li>
                    </ul>
                </div>
                
                <p><strong>Echipa noastră rămâne la dispoziția dumneavoastră pentru clarificări și suport tehnic.</strong></p>
                <p>Vă mulțumim pentru colaborare!</p>
                
                <div class="footer">
                    <p>Data generare: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                    <p>Raport generat automat pentru ultimele 3 zile de activitate.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_centre_report(self, centru, data_raport):
        """Trimite raportul pentru un centru specific - cu grafic PNG atașat"""
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
            
            # Verifică dacă există date pentru ultimele 3 zile
            daily_stats = self.get_daily_stats_last_3_days(centru, data_raport)
            
            if daily_stats.empty:
                self.logger.info(f"Nu există date pentru centrul {centru} în ultimele 3 zile")
                return True
            
            # Generează graficul PNG
            self.logger.info(f"Generez graficul de evoluție pentru {centru}...")
            chart_path = self.generate_evolution_chart(centru, data_raport)
            
            if not chart_path or not os.path.exists(chart_path):
                self.logger.warning(f"Nu s-a putut genera graficul pentru {centru}")
                chart_path = None
            else:
                self.logger.info(f"Grafic generat cu succes: {chart_path}")
            
            # Generează HTML-ul raportului (acum folosește ultimele 3 zile)
            html_content = self.generate_email_report_html(centru, None, data_raport)
            
            # Configurează email-ul
            msg = MIMEMultipart('mixed')  # 'mixed' pentru atașamente
            msg['From'] = f"{email_config['sender_name']} <{email_config['email']}>"
            msg['To'] = ', '.join(email_addresses[centru])
            subject = f"Raport scanări {centru} - Ultimele 3 zile - {datetime.strptime(data_raport, '%Y-%m-%d').strftime('%d.%m.%Y')}"
            msg['Subject'] = subject
            
            # Adaugă conținutul HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Adaugă graficul ca atașament dacă există
            if chart_path and os.path.exists(chart_path):
                try:
                    with open(chart_path, 'rb') as f:
                        chart_data = f.read()
                    
                    chart_attachment = MIMEBase('image', 'png')
                    chart_attachment.set_payload(chart_data)
                    encoders.encode_base64(chart_attachment)
                    chart_attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="Grafic_Evolutie_{centru}_{data_raport}.png"'
                    )
                    msg.attach(chart_attachment)
                    self.logger.info(f"Grafic atașat cu succes: {os.path.basename(chart_path)}")
                    
                    # Șterge fișierul temporar după atașare
                    try:
                        os.remove(chart_path)
                        self.logger.info(f"Fișier temporar șters: {chart_path}")
                    except:
                        pass  # Nu e critic dacă nu se poate șterge
                        
                except Exception as e:
                    self.logger.warning(f"Eroare la atașarea graficului: {str(e)}")
                    # Continuă fără grafic
            
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
        """Trimite rapoarte pentru toate centrele care au date în ultimele 3 zile"""
        conn = sqlite3.connect(self.db_path)
        
        # Obține lista centrelor cu date în ultimele 3 zile
        query = '''
            SELECT DISTINCT centru 
            FROM rapoarte_istoric 
            WHERE data_raport >= ? 
            AND centru != 'NECUNOSCUT'
            ORDER BY centru
        '''
        
        # Calculează data de start pentru ultimele 3 zile
        data_end = datetime.strptime(data_raport, '%Y-%m-%d')
        data_start = data_end - timedelta(days=2)  # 3 zile: azi, ieri, alaltăieri
        data_start_str = data_start.strftime('%Y-%m-%d')
        
        cursor = conn.cursor()
        cursor.execute(query, (data_start_str,))
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