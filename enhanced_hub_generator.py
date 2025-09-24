#!/usr/bin/env python3
"""
Enhanced HUB Report Generator cu funcționalitate email
Extinde generatorul existent cu salvarea în istoric și trimiterea de email-uri
"""

import pandas as pd
import os
from datetime import datetime
from unified_hub_report_generator import (
    UnifiedHubReportGenerator, 
    BRASOV_CONFIG, 
    SIBIU_CONFIG,
    generate_all_hub_reports
)
from email_reporting_system import EmailReportingSystem

class EnhancedHubGenerator:
    def __init__(self, base_url=None):
        if base_url is None:
            base_url = '/Users/telermarius/Library/CloudStorage/Dropbox/DSC/Rapoarte/HUB Brasov/'
        
        self.base_url = base_url
        self.email_system = EmailReportingSystem(base_url)
    
    def generate_reports_with_email(self, data_raport, send_emails=True):
        """
        Generează rapoartele standard și trimite email-uri
        
        Args:
            data_raport (str): Data raportului în format YYYY-MM-DD
            send_emails (bool): Dacă să trimită email-uri automat
        """
        print(f"🏗️ Generez rapoarte cu email pentru data: {data_raport}")
        print("=" * 60)
        
        # Generează rapoartele standard
        success = self._generate_standard_reports(data_raport)
        
        if not success:
            print("❌ Eroare la generarea rapoartelor standard")
            return False
        
        # Salvează datele în istoric
        print("\n📊 Salvez datele în istoric...")
        self._save_reports_to_history(data_raport)
        
        # Trimite email-uri dacă este cerut
        if send_emails:
            print("\n📧 Trimit rapoarte pe email...")
            try:
                # Verifică configurația email
                self.email_system.load_email_config()
                self.email_system.load_email_addresses()
                
                success_count, total_count = self.email_system.send_all_centre_reports(data_raport)
                print(f"✅ Email-uri trimise cu succes: {success_count}/{total_count}")
                
            except FileNotFoundError as e:
                print(f"⚠️ Email-urile nu au fost trimise: {e}")
                print("Configurați email-urile și rulați din nou pentru a trimite rapoarte.")
        
        print("\n" + "=" * 60)
        print("✅ Procesarea completă a fost finalizată cu succes!")
        return True
    
    def _generate_standard_reports(self, data_raport):
        """Generează rapoartele standard folosind generatorul existent"""
        try:
            # Verifică dacă fișierul master există
            fisier_master = os.path.join(self.base_url, 'master_data.csv')
            if not os.path.exists(fisier_master):
                print(f"❌ Fișierul master nu există: {fisier_master}")
                return False
            
            print("📈 Generez rapoarte pentru Brașov...")
            generator_brasov = UnifiedHubReportGenerator(fisier_master, data_raport, self.base_url, BRASOV_CONFIG)
            generator_brasov.genereaza_rapoarte()
            
            print("\n📈 Generez rapoarte pentru Sibiu...")
            generator_sibiu = UnifiedHubReportGenerator(fisier_master, data_raport, self.base_url, SIBIU_CONFIG)
            generator_sibiu.genereaza_rapoarte()
            
            return True
            
        except Exception as e:
            print(f"❌ Eroare la generarea rapoartelor: {str(e)}")
            return False
    
    def _save_reports_to_history(self, data_raport):
        """Salvează rapoartele în istoric pentru email-uri"""
        try:
            data_obj = datetime.strptime(data_raport, "%Y-%m-%d")
            data_str = data_obj.strftime("%d.%m")
            data_urmatoare_str = (data_obj.replace(day=data_obj.day + 1) if data_obj.day < 28 
                                else data_obj.replace(month=data_obj.month + 1, day=1)).strftime("%d.%m")
            
            # Procesează rapoartele Brașov
            self._process_hub_reports('Brasov', data_str, data_urmatoare_str, data_raport)
            
            # Procesează rapoartele Sibiu
            self._process_hub_reports('Sibiu', data_str, data_urmatoare_str, data_raport)
            
        except Exception as e:
            print(f"⚠️ Eroare la salvarea în istoric: {str(e)}")
    
    def _process_hub_reports(self, hub_name, data_str, data_urmatoare_str, data_raport):
        """Procesează rapoartele pentru un hub specific"""
        # Paths pentru rapoarte
        statie_hub_path = os.path.join(
            self.base_url, 
            f"Raport Statie-Hub {hub_name} {data_str}-{data_urmatoare_str}.xlsx"
        )
        hub_statie_path = os.path.join(
            self.base_url, 
            f"Raport HUB-Statie {hub_name} {data_str}-{data_urmatoare_str}.xlsx"
        )
        
        # Procesează Statie-Hub
        if os.path.exists(statie_hub_path):
            try:
                df_sumar = pd.read_excel(statie_hub_path, sheet_name='Sumar')
                # Exclude rândul Total
                df_sumar = df_sumar[df_sumar['Ruta'] != 'Total']
                self.email_system.save_report_to_history(data_raport, hub_name, 'Statie-Hub', df_sumar, statie_hub_path)
                print(f"✅ Salvat istoric Statie-Hub {hub_name}")
            except Exception as e:
                print(f"⚠️ Eroare salvare Statie-Hub {hub_name}: {str(e)}")
                # Debug info
                import traceback
                traceback.print_exc()
        
        # Procesează Hub-Statie
        if os.path.exists(hub_statie_path):
            try:
                df_sumar = pd.read_excel(hub_statie_path, sheet_name='Sumar')
                # Exclude rândul Total
                df_sumar = df_sumar[df_sumar['Ruta'] != 'Total']
                self.email_system.save_report_to_history(data_raport, hub_name, 'Hub-Statie', df_sumar, hub_statie_path)
                print(f"✅ Salvat istoric Hub-Statie {hub_name}")
            except Exception as e:
                print(f"⚠️ Eroare salvare Hub-Statie {hub_name}: {str(e)}")
                # Debug info
                import traceback
                traceback.print_exc()
    
    def setup_email_system(self):
        """Configurează sistemul de email (creează template-urile)"""
        print("⚙️ Configurez sistemul de email...")
        
        # Creează template-urile
        config_path = self.email_system.create_email_config_template()
        addresses_path = self.email_system.create_email_addresses_template()
        
        print(f"📧 Template configurație email: {config_path}")
        print(f"📬 Template adrese email: {addresses_path}")
        print("\n📝 Pași pentru configurare:")
        print("1. Editați fișierul email_config.json cu credențialele SMTP")
        print("2. Actualizați fișierul email_addresses_centre.json cu adresele corecte")
        print("3. Rulați din nou generatorul pentru a trimite email-uri")
    
    def send_test_email(self, centru, data_raport):
        """Trimite un email de test pentru un centru specific"""
        print(f"📧 Trimit email de test pentru centrul: {centru}")
        
        try:
            # Verifică adresele email pentru centru înainte de trimitere
            email_addresses = self.email_system.load_email_addresses()
            if centru in email_addresses:
                addresses_str = ', '.join(email_addresses[centru])
                print(f"📬 Destinatari: {addresses_str}")
            
            success = self.email_system.send_centre_report(centru, data_raport)
            if success:
                print(f"✅ Email de test trimis cu succes pentru {centru}")
            else:
                print(f"❌ Eroare la trimiterea email-ului pentru {centru}")
            return success
        except Exception as e:
            print(f"❌ Eroare: {str(e)}")
            return False
    
    def get_available_centres(self, data_raport):
        """Returnează lista centrelor disponibile pentru raportare"""
        import sqlite3
        from datetime import timedelta
        
        conn = sqlite3.connect(self.email_system.db_path)
        
        data_start = (datetime.strptime(data_raport, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT DISTINCT centru, COUNT(*) as numar_rute
            FROM rapoarte_istoric 
            WHERE data_raport >= ? 
            AND data_raport <= ?
            AND centru != 'NECUNOSCUT'
            GROUP BY centru
            ORDER BY centru
        '''
        
        cursor = conn.cursor()
        cursor.execute(query, (data_start, data_raport))
        results = cursor.fetchall()
        conn.close()
        
        return results

def main():
    """Funcția principală"""
    print("🚀 Enhanced HUB Report Generator cu Email")
    print("=" * 50)
    
    # Inițializează generatorul
    generator = EnhancedHubGenerator()
    
    # Meniu interactiv
    while True:
        print("\nSelectați o opțiune:")
        print("1. Generează rapoarte cu email (complet)")
        print("2. Generează doar rapoarte (fără email)")
        print("3. Trimite doar email-uri (din istoric)")
        print("4. Configurează sistemul de email")
        print("5. Trimite email de test")
        print("6. Vezi centrele disponibile")
        print("0. Ieșire")
        
        try:
            optiune = input("\nOpțiunea (0-6): ").strip()
            
            if optiune == "0":
                print("👋 La revedere!")
                break
            
            elif optiune == "1":
                data_raport = input("Data raport (YYYY-MM-DD): ").strip()
                if not data_raport:
                    data_raport = datetime.now().strftime("%Y-%m-%d")
                
                generator.generate_reports_with_email(data_raport, send_emails=True)
            
            elif optiune == "2":
                data_raport = input("Data raport (YYYY-MM-DD): ").strip()
                if not data_raport:
                    data_raport = datetime.now().strftime("%Y-%m-%d")
                
                generator.generate_reports_with_email(data_raport, send_emails=False)
            
            elif optiune == "3":
                data_raport = input("Data raport (YYYY-MM-DD): ").strip()
                if not data_raport:
                    data_raport = datetime.now().strftime("%Y-%m-%d")
                
                try:
                    success_count, total_count = generator.email_system.send_all_centre_reports(data_raport)
                    print(f"✅ Email-uri trimise: {success_count}/{total_count}")
                except Exception as e:
                    print(f"❌ Eroare: {str(e)}")
            
            elif optiune == "4":
                generator.setup_email_system()
            
            elif optiune == "5":
                data_raport = input("Data raport (YYYY-MM-DD): ").strip()
                if not data_raport:
                    data_raport = datetime.now().strftime("%Y-%m-%d")
                
                centre_disponibile = generator.get_available_centres(data_raport)
                if not centre_disponibile:
                    print("❌ Nu există centre disponibile pentru această dată")
                    continue
                
                print("\nCentre disponibile:")
                for i, (centru, numar_rute) in enumerate(centre_disponibile, 1):
                    print(f"{i}. {centru} ({numar_rute} rute)")
                
                try:
                    idx = int(input("Selectați centrul pentru test (numărul): ")) - 1
                    if 0 <= idx < len(centre_disponibile):
                        centru = centre_disponibile[idx][0]
                        generator.send_test_email(centru, data_raport)
                    else:
                        print("❌ Selecție invalidă")
                except ValueError:
                    print("❌ Introduceți un număr valid")
            
            elif optiune == "6":
                data_raport = input("Data raport (YYYY-MM-DD): ").strip()
                if not data_raport:
                    data_raport = datetime.now().strftime("%Y-%m-%d")
                
                centre_disponibile = generator.get_available_centres(data_raport)
                
                print(f"\nCentre disponibile pentru {data_raport} (ultimele 30 zile):")
                if centre_disponibile:
                    for centru, numar_rute in centre_disponibile:
                        print(f"• {centru}: {numar_rute} rute")
                else:
                    print("❌ Nu există date pentru această perioadă")
            
            else:
                print("❌ Opțiune invalidă")
                
        except KeyboardInterrupt:
            print("\n👋 Operațiune anulată.")
            break
        except Exception as e:
            print(f"❌ Eroare: {str(e)}")

if __name__ == "__main__":
    main()