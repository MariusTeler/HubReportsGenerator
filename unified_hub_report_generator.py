import pandas as pd
from datetime import datetime, timedelta
import os

class UnifiedHubReportGenerator:
    def __init__(self, fisier_master, data_raport, base_url, hub_config=None):
        self.fisier_master = fisier_master
        self.data_raport = datetime.strptime(data_raport, "%Y-%m-%d")
        self.base_url = base_url
        
        # Configurarea implicită pentru Brașov (compatibilitate înapoi)
        default_config = {
            'nume': 'BRASOV',
            'prescurtare': 'BVH',
            'intrare_start_hour': 15,
            'intrare_start_minute': 30,
            'intrare_end_hour': 15,
            'intrare_end_minute': 30,
            'iesire_start_hour': 15,
            'iesire_start_minute': 30,
            'iesire_end_hour': 23,
            'iesire_end_minute': 59
        }
        
        # Aplică configurația specificată sau folosește cea implicită
        self.hub_config = {**default_config, **(hub_config or {})}
        
        # Construiește căile fișierelor pe baza configurației
        hub_nume_lower = self.hub_config['nume'].lower().capitalize()
        self.fisier_rute = f"{base_url}Utile/rute{self.hub_config['nume']}.csv"
        self.fisier_echivalenta = f"{base_url}Utile/rute{hub_nume_lower}_echivalenta.xlsx"
        self.fisier_fara_scan = f"{base_url}Utile/FirmeFaraScanIesire.xlsx"
        
    def genereaza_fisiere_temporare(self):
        """Generează fișierele temporare din fișierul master pe baza criteriilor"""
        print("Se încarcă fișierul master...")
        df_master = pd.read_csv(self.fisier_master, parse_dates=['Scanare'])
        
        # Calculează intervalele de timp pe baza configurației hub-ului
        data_raport_start = self.data_raport.replace(hour=0, minute=0, second=0)
        data_raport_end = self.data_raport.replace(hour=23, minute=59, second=59)
        
        # Intervalele pentru intrare hub (configurabile)
        intrare_start = self.data_raport.replace(
            hour=self.hub_config['intrare_start_hour'], 
            minute=self.hub_config['intrare_start_minute'], 
            second=0
        )
        if self.data_raport.weekday() == 4:  # 4 = vineri (0=luni, 1=marți, etc.)
            data_urmatoare = self.data_raport + timedelta(days=3)  # pentru intrare_centru (luni)
            intrare_hub_end_date = self.data_raport + timedelta(days=1)  # pentru intrare_hub (sâmbătă)
        else:
            data_urmatoare = self.data_raport + timedelta(days=1)
            intrare_hub_end_date = data_urmatoare
        intrare_end = intrare_hub_end_date.replace(
            hour=self.hub_config['intrare_end_hour'], 
            minute=self.hub_config['intrare_end_minute'], 
            second=0
        )
        
        # Intervalele pentru ieșire hub (configurabile)  
        iesire_start = self.data_raport.replace(
            hour=self.hub_config['iesire_start_hour'], 
            minute=self.hub_config['iesire_start_minute'], 
            second=0
        )
        if self.data_raport.weekday() == 4:  # vineri
            iesire_hub_end_date = self.data_raport + timedelta(days=1)  # pentru iesire_hub (sâmbătă)
        else:
            iesire_hub_end_date = data_urmatoare
        iesire_end = iesire_hub_end_date.replace(
            hour=self.hub_config['iesire_end_hour'], 
            minute=self.hub_config['iesire_end_minute'], 
            second=59
        )
        
        # Intervalul pentru intrarea centru (rămâne fix)
        data_urmatoare_16_59 = data_urmatoare.replace(hour=16, minute=59, second=59)
        
        print(f"Generez fișierele pentru data raport: {self.data_raport.strftime('%Y-%m-%d')}")
        
        # Generează fișiere pentru primul raport (Statie-Hub)
        # Ieșire centru: "Iesire Centru" din data raport 00:00-23:59
        iesire_centru = df_master[
            (df_master['Tip Scanare'] == 'Iesire Centru') &
            (df_master['Scanare'] >= data_raport_start) &
            (df_master['Scanare'] <= data_raport_end)
        ]
        
        # Intrare hub: "Intrare Centru", centru=config, din interval configurabil
        intrare_hub = df_master[
            (df_master['Tip Scanare'] == 'Intrare Centru') &
            (df_master['Centru'] == self.hub_config['nume']) &
            (df_master['Scanare'] >= intrare_start) &
            (df_master['Scanare'] <= intrare_end)
        ]
        
        # Generează fișiere pentru al doilea raport (Hub-Statie)
        # Ieșire HUB: "Iesire Centru", centru=config, din interval configurabil
        iesire_hub = df_master[
            (df_master['Tip Scanare'] == 'Iesire Centru') &
            (df_master['Centru'] == self.hub_config['nume']) &
            (df_master['Scanare'] >= iesire_start) &
            (df_master['Scanare'] <= iesire_end)
        ]
        
        # Intrare centru: pentru vineri din sâmbătă 00:00 - luni 16:59, altfel din data+1 00:00 - data+1 16:59
        if self.data_raport.weekday() == 4:  # vineri
            intrare_centru_start = (self.data_raport + timedelta(days=1)).replace(hour=0, minute=0, second=0)  # sâmbătă 00:00
        else:
            intrare_centru_start = data_urmatoare.replace(hour=0, minute=0, second=0)  # data+1 00:00
        
        intrare_centru = df_master[
            (df_master['Tip Scanare'] == 'Intrare Centru') &
            (df_master['Scanare'] >= intrare_centru_start) &
            (df_master['Scanare'] <= data_urmatoare_16_59)
        ]
        
        # Salvează fișierele temporare
        data_str = self.data_raport.strftime("%d.%m")
        data_urmatoare_str = data_urmatoare.strftime("%d.%m")
        
        fisier_iesire_centru = f"{self.base_url}temp_iesire_centru_{data_str}.csv"
        fisier_intrare_hub = f"{self.base_url}temp_intrare_hub_{data_str}-{data_urmatoare_str}.csv"
        fisier_iesire_hub = f"{self.base_url}temp_iesire_hub_{data_str}-{data_urmatoare_str}.csv"
        fisier_intrare_centru = f"{self.base_url}temp_intrare_centru_{data_urmatoare_str}.csv"
        
        iesire_centru.to_csv(fisier_iesire_centru, index=False)
        intrare_hub.to_csv(fisier_intrare_hub, index=False)
        iesire_hub.to_csv(fisier_iesire_hub, index=False)
        intrare_centru.to_csv(fisier_intrare_centru, index=False)
        
        print(f"Generat: {len(iesire_centru)} înregistrări pentru ieșire centru")
        print(f"Generat: {len(intrare_hub)} înregistrări pentru intrare hub")
        print(f"Generat: {len(iesire_hub)} înregistrări pentru ieșire hub")
        print(f"Generat: {len(intrare_centru)} înregistrări pentru intrare centru")
        
        return {
            'statie_hub': {
                'iesire': fisier_iesire_centru,
                'intrare': fisier_intrare_hub
            },
            'hub_statie': {
                'iesire': fisier_iesire_hub,
                'intrare': fisier_intrare_centru
            }
        }
    
    def sumarizeaza_date_logistice_statie_hub(self, fisier_iesire, fisier_intrare, fisier_output):
        """Generează raportul Statie-Hub (similar cu primul script)"""
        print(f"Generez raportul Statie-Hub...")
        
        df_iesire = pd.read_csv(fisier_iesire, parse_dates=['Scanare'])
        df_intrare = pd.read_csv(fisier_intrare, parse_dates=['Scanare'])
        rute = pd.read_csv(self.fisier_rute)
        
        df_echivalenta = pd.read_excel(self.fisier_echivalenta, sheet_name='Sheet1')
        df_fara_scan = pd.read_excel(self.fisier_fara_scan, sheet_name='Sheet3')
        
        valori_fara_scan = set(df_fara_scan.iloc[:, 0].dropna().astype(str))
        
        conditii_filtrare = lambda df: (
            df['Categorie'].isin(['Colete', 'Paleti']) &
            df['Ruta'].isin(rute['Denumire'])
        )
        
        df_iesire = df_iesire[conditii_filtrare(df_iesire) & (df_iesire['Centru'] != self.hub_config['nume'])]
        df_intrare = df_intrare[conditii_filtrare(df_intrare) & (df_intrare['Centru'] == self.hub_config['nume'])]
        
        coloane_necesare = ['CodBare', 'Ruta', 'Centru exp', 'Centru dest', 
                             'Expeditor', 'Destinatar', 'bucati', 'Greutate', 
                             'Categorie', 'Scanare', 'User']
        
        df_iesire = df_iesire[coloane_necesare].rename(columns={
            'Ruta': 'Ruta Iesire Centru',
            'Scanare': 'DataScanare Iesire Centru',
            'User': 'User_iesire'
        })
        
        df_intrare = df_intrare[coloane_necesare].rename(columns={
            'Ruta': 'Ruta Intrare Hub',
            'Scanare': 'DataScanare Intrare Centru',
            'User': 'User_intrare'
        })
        
        df_final = pd.merge(
            df_iesire, 
            df_intrare, 
            on=['CodBare'], 
            how='outer',
            suffixes=('_iesire', '_intrare')
        )
        
        for col in ['Centru exp', 'Centru dest', 'Expeditor', 'Destinatar', 
                    'bucati', 'Greutate', 'Categorie']:
            df_final[col] = df_final[f'{col}_iesire'].fillna(df_final[f'{col}_intrare'])
            df_final = df_final.drop([f'{col}_iesire', f'{col}_intrare'], axis=1)
        
        df_final['User'] = df_final['User_intrare']
        df_final = df_final.drop(['User_iesire', 'User_intrare'], axis=1)
        
        df_final['Data'] = df_final['DataScanare Iesire Centru'].fillna(
            df_final['DataScanare Intrare Centru']
        )
        
        df_final['Greutate Medie'] = df_final.apply(
            lambda row: round(row['Greutate'] / row['bucati'], 2) if row['bucati'] != 0 else 0,
            axis=1
        )
        
        dict_echivalenta = dict(zip(df_echivalenta.iloc[:, 0], df_echivalenta.iloc[:, 1]))
        
        df_final['Ruta Iesire Centru'] = df_final.apply(
            lambda row: dict_echivalenta.get(row['Ruta Intrare Hub']) 
            if pd.isna(row['Ruta Iesire Centru']) and row['Ruta Intrare Hub'] in dict_echivalenta
            else row['Ruta Iesire Centru'],
            axis=1
        )
        
        df_final['DataScanare Iesire Centru'] = df_final.apply(
            lambda row: "Fara scan iesire" 
            if pd.isna(row['DataScanare Iesire Centru']) and str(row['Expeditor']) in valori_fara_scan
            else row['DataScanare Iesire Centru'],
            axis=1
        )
        
        # Creez coloane helper pentru contorizare
        df_final['has_scan_iesire'] = df_final['DataScanare Iesire Centru'].notna()
        df_final['has_scan_intrare'] = df_final['DataScanare Intrare Centru'].notna()
        
        df_sumar = df_final.groupby("Ruta Iesire Centru").agg(
            **{
                "Nr Colete": ("Ruta Iesire Centru", "count"),
                "Greutate": ("Greutate Medie", "sum"),
                "Scan iesire Centru": ("has_scan_iesire", "sum"),
                "Scan intrare Hub": ("has_scan_intrare", "sum")
            }
        ).reset_index().rename(columns={"Ruta Iesire Centru": "Ruta"})
        
        df_sumar["Procent Iesire Centru"] = df_sumar.apply(
            lambda row: row["Scan iesire Centru"] / row["Nr Colete"] if row["Nr Colete"] != 0 else 0,
            axis=1
        )
        df_sumar["Procent Intrare Hub"] = df_sumar.apply(
            lambda row: row["Scan intrare Hub"] / row["Nr Colete"] if row["Nr Colete"] != 0 else 0,
            axis=1
        )
        
        total_nr_colete = int(df_sumar["Nr Colete"].sum())
        total_greutate = float(df_sumar["Greutate"].sum())
        total_scan_iesire = int(df_sumar["Scan iesire Centru"].sum())
        total_scan_intrare = int(df_sumar["Scan intrare Hub"].sum())
        total_procent_iesire = total_scan_iesire / total_nr_colete if total_nr_colete != 0 else 0
        total_procent_intrare = total_scan_intrare / total_nr_colete if total_nr_colete != 0 else 0

        total_row = pd.DataFrame({
            "Ruta": ["Total"],
            "Nr Colete": [total_nr_colete],
            "Greutate": [total_greutate],
            "Scan iesire Centru": [total_scan_iesire],
            "Scan intrare Hub": [total_scan_intrare],
            "Procent Iesire Centru": [total_procent_iesire],
            "Procent Intrare Hub": [total_procent_intrare]
        })
        df_sumar = pd.concat([df_sumar, total_row], ignore_index=True)
        
        def formula_user(idx, ruta):
            if ruta == "Total":
                return ""
            else:
                return f"=VLOOKUP(A{idx+2},Detaliat!B:M,12,FALSE)"
        
        df_sumar["User:"] = [formula_user(idx, row["Ruta"]) for idx, row in df_sumar.iterrows()]
        
        # Sortează df_final după coloana User
        df_final_sorted = df_final.sort_values('User', na_position='last')
        
        with pd.ExcelWriter(fisier_output, engine="openpyxl") as writer:
            df_final_sorted.to_excel(writer, sheet_name="Detaliat", index=False)
            df_sumar.to_excel(writer, sheet_name="Sumar", index=False)
            
            # Formatează celulele de procente în sheet-ul Sumar cu openpyxl
            from openpyxl.styles import NamedStyle
            from openpyxl.utils import get_column_letter
            
            workbook = writer.book
            worksheet_sumar = writer.sheets["Sumar"]
            
            # Definește stilul pentru procente
            percentage_style = NamedStyle(name="percentage")
            percentage_style.number_format = "0.00%"
            
            # Aplică formatul pentru coloanele de procente (F și G)
            for row in range(2, len(df_sumar) + 2):  # începe de la rândul 2 (după header)
                # Coloana F = "Procent Iesire Centru"
                cell_f = worksheet_sumar[f'F{row}']
                cell_f.number_format = "0.00%"
                
                # Coloana G = "Procent Intrare Hub"
                cell_g = worksheet_sumar[f'G{row}']
                cell_g.number_format = "0.00%"
        
        print(f"Raportul Statie-Hub a fost salvat în: {fisier_output}")
    
    def sumarizeaza_date_logistice_hub_statie(self, fisier_iesire, fisier_intrare, fisier_output):
        """Generează raportul Hub-Statie (similar cu al doilea script)"""
        print(f"Generez raportul Hub-Statie...")
        
        df_iesire = pd.read_csv(fisier_iesire, parse_dates=['Scanare'])
        df_intrare = pd.read_csv(fisier_intrare, parse_dates=['Scanare'])
        rute = pd.read_csv(self.fisier_rute)
        
        df_echivalenta = pd.read_excel(self.fisier_echivalenta, sheet_name='Sheet1')
        
        conditii_filtrare = lambda df: (
            df['Categorie'].isin(['Colete', 'Paleti']) &
            df['Ruta'].isin(rute['Denumire'])
        )
        
        df_iesire = df_iesire[conditii_filtrare(df_iesire) & (df_iesire['Centru'] == self.hub_config['nume'])]
        df_intrare = df_intrare[conditii_filtrare(df_intrare) & (df_intrare['Centru'] != self.hub_config['nume'])]
        
        coloane_necesare = ['CodBare', 'Ruta', 'Centru exp', 'Centru dest', 
                             'Expeditor', 'Destinatar', 'bucati', 'Greutate', 
                             'Categorie', 'Scanare', 'User']
        
        df_iesire = df_iesire[coloane_necesare].rename(columns={
            'Ruta': 'Ruta Iesire HUB',
            'Scanare': 'DataScanare Iesire Centru',
            'User': 'User_iesire'
        })
        
        df_intrare = df_intrare[coloane_necesare].rename(columns={
            'Ruta': 'Ruta Intrare Centru',
            'Scanare': 'DataScanare Intrare Centru',
            'User': 'User_intrare'
        })
        
        df_final = pd.merge(
            df_iesire, 
            df_intrare, 
            on=['CodBare'], 
            how='outer',
            suffixes=('_iesire', '_intrare')
        )
        
        for col in ['Centru exp', 'Centru dest', 'Expeditor', 'Destinatar', 
                    'bucati', 'Greutate', 'Categorie']:
            df_final[col] = df_final[f'{col}_iesire'].fillna(df_final[f'{col}_intrare']).infer_objects(copy=False)
            df_final = df_final.drop([f'{col}_iesire', f'{col}_intrare'], axis=1)
        
        df_final['User'] = df_final['User_iesire']
        df_final = df_final.drop(['User_iesire', 'User_intrare'], axis=1)
        
        df_final['Data'] = df_final['DataScanare Iesire Centru'].fillna(
            df_final['DataScanare Intrare Centru']
        ).infer_objects(copy=False)
        
        df_final['Greutate Medie'] = df_final.apply(
            lambda row: round(row['Greutate'] / row['bucati'], 2) if row['bucati'] != 0 else 0,
            axis=1
        )
        
        dict_echivalenta = dict(zip(df_echivalenta.iloc[:, 1], df_echivalenta.iloc[:, 2]))
        
        df_final['Ruta Iesire HUB'] = df_final.apply(
            lambda row: dict_echivalenta.get(row['Ruta Intrare Centru']) 
            if pd.isna(row['Ruta Iesire HUB']) and row['Ruta Intrare Centru'] in dict_echivalenta
            else row['Ruta Iesire HUB'],
            axis=1
        )
        
        # Creez coloane helper pentru contorizare
        df_final['has_scan_iesire'] = df_final['DataScanare Iesire Centru'].notna()
        df_final['has_scan_intrare'] = df_final['DataScanare Intrare Centru'].notna()
        
        df_sumar = df_final.groupby("Ruta Iesire HUB").agg(
            **{
                "Nr Colete": ("Ruta Iesire HUB", "count"),
                "Greutate": ("Greutate Medie", "sum"),
                "Scan iesire HUB": ("has_scan_iesire", "sum"),
                "Scan intrare Centru": ("has_scan_intrare", "sum")
            }
        ).reset_index().rename(columns={"Ruta Iesire HUB": "Ruta"})
        
        df_sumar["Procent Iesire HUB"] = df_sumar.apply(
            lambda row: row["Scan iesire HUB"] / row["Nr Colete"] if row["Nr Colete"] != 0 else 0,
            axis=1
        )
        df_sumar["Procent Intrare Centru"] = df_sumar.apply(
            lambda row: row["Scan intrare Centru"] / row["Nr Colete"] if row["Nr Colete"] != 0 else 0,
            axis=1
        )
        
        total_nr_colete = int(df_sumar["Nr Colete"].sum())
        total_greutate = float(df_sumar["Greutate"].sum())
        total_scan_iesire = int(df_sumar["Scan iesire HUB"].sum())
        total_scan_intrare = int(df_sumar["Scan intrare Centru"].sum())
        total_procent_iesire = total_scan_iesire / total_nr_colete if total_nr_colete != 0 else 0
        total_procent_intrare = total_scan_intrare / total_nr_colete if total_nr_colete != 0 else 0

        total_row = pd.DataFrame({
            "Ruta": ["Total"],
            "Nr Colete": [total_nr_colete],
            "Greutate": [total_greutate],
            "Scan iesire HUB": [total_scan_iesire],
            "Scan intrare Centru": [total_scan_intrare],
            "Procent Iesire HUB": [total_procent_iesire],
            "Procent Intrare Centru": [total_procent_intrare]
        })
        df_sumar = pd.concat([df_sumar, total_row], ignore_index=True)
        
        def formula_user(idx, ruta):
            if ruta == "Total":
                return ""
            else:
                return f"=VLOOKUP(A{idx+2},Detaliat!B:M,12,FALSE)"
        
        df_sumar["User:"] = [formula_user(idx, row["Ruta"]) for idx, row in df_sumar.iterrows()]
        
        # Sortează df_final după coloana User
        df_final_sorted = df_final.sort_values('User', na_position='last')
        
        with pd.ExcelWriter(fisier_output, engine="openpyxl") as writer:
            df_final_sorted.to_excel(writer, sheet_name="Detaliat", index=False)
            df_sumar.to_excel(writer, sheet_name="Sumar", index=False)
            
            # Formatează celulele de procente în sheet-ul Sumar cu openpyxl
            from openpyxl.styles import NamedStyle
            from openpyxl.utils import get_column_letter
            
            workbook = writer.book
            worksheet_sumar = writer.sheets["Sumar"]
            
            # Definește stilul pentru procente
            percentage_style = NamedStyle(name="percentage")
            percentage_style.number_format = "0.00%"
            
            # Aplică formatul pentru coloanele de procente (F și G)
            for row in range(2, len(df_sumar) + 2):  # începe de la rândul 2 (după header)
                # Coloana F = "Procent Iesire HUB"
                cell_f = worksheet_sumar[f'F{row}']
                cell_f.number_format = "0.00%"
                
                # Coloana G = "Procent Intrare Centru"
                cell_g = worksheet_sumar[f'G{row}']
                cell_g.number_format = "0.00%"
        
        print(f"Raportul Hub-Statie a fost salvat în: {fisier_output}")
    
    def sterge_fisiere_temporare(self, fisiere_temp):
        """Șterge fișierele temporare create"""
        for tip_raport in fisiere_temp.values():
            for fisier in tip_raport.values():
                if os.path.exists(fisier):
                    os.remove(fisier)
                    print(f"Șters fișier temporar: {fisier}")
    
    def genereaza_rapoarte(self):
        """Generează ambele rapoarte pornind de la fișierul master"""
        try:
            # Generează fișierele temporare
            fisiere_temp = self.genereaza_fisiere_temporare()
            
            # Generează output-urile cu numele hub-ului
            data_str = self.data_raport.strftime("%d.%m")
            data_urmatoare_str = (self.data_raport + timedelta(days=1)).strftime("%d.%m")
            hub_nume = self.hub_config['nume'].capitalize()
            
            output_statie_hub = f"{self.base_url}Raport Statie-Hub {hub_nume} {data_str}-{data_urmatoare_str}.xlsx"
            output_hub_statie = f"{self.base_url}Raport HUB-Statie {hub_nume} {data_str}-{data_urmatoare_str}.xlsx"
            
            # Generează primul raport (Statie-Hub)
            self.sumarizeaza_date_logistice_statie_hub(
                fisiere_temp['statie_hub']['iesire'],
                fisiere_temp['statie_hub']['intrare'],
                output_statie_hub
            )
            
            # Generează al doilea raport (Hub-Statie)
            self.sumarizeaza_date_logistice_hub_statie(
                fisiere_temp['hub_statie']['iesire'],
                fisiere_temp['hub_statie']['intrare'],
                output_hub_statie
            )
            
            # Șterge fișierele temporare
            self.sterge_fisiere_temporare(fisiere_temp)
            
            print(f"\n✅ Rapoartele au fost generate cu succes!")
            print(f"📊 Raport Statie-Hub: {output_statie_hub}")
            print(f"📊 Raport Hub-Statie: {output_hub_statie}")
            
        except Exception as e:
            print(f"❌ Eroare la generarea rapoartelor: {str(e)}")
            raise

# Configurații predefinite pentru hub-uri
BRASOV_CONFIG = {
    'nume': 'BRASOV',
    'prescurtare': 'BVH',
    'intrare_start_hour': 15,
    'intrare_start_minute': 30,
    'intrare_end_hour': 15,
    'intrare_end_minute': 30,
    'iesire_start_hour': 15,
    'iesire_start_minute': 30,
    'iesire_end_hour': 23,
    'iesire_end_minute': 59
}

SIBIU_CONFIG = {
    'nume': 'SIBIU',
    'prescurtare': 'SBH',
    'intrare_start_hour': 21,
    'intrare_start_minute': 0,
    'intrare_end_hour': 6,
    'intrare_end_minute': 0,
    'iesire_start_hour': 21,
    'iesire_start_minute': 0,
    'iesire_end_hour': 6,
    'iesire_end_minute': 0
}

def create_brasov_generator(fisier_master, data_raport, base_url):
    """Creează generator pentru hub-ul Brașov"""
    return UnifiedHubReportGenerator(fisier_master, data_raport, base_url, BRASOV_CONFIG)

def create_sibiu_generator(fisier_master, data_raport, base_url):
    """Creează generator pentru hub-ul Sibiu"""
    return UnifiedHubReportGenerator(fisier_master, data_raport, base_url, SIBIU_CONFIG)

def generate_brasov_reports(data_raport, base_url=None):
    """Generează rapoarte pentru hub-ul Brașov"""
    if base_url is None:
        base_url = '/Users/telermarius/Library/CloudStorage/Dropbox/DSC/Rapoarte/HUB Brasov/'
    
    fisier_master = f"{base_url}master_data.csv"
    
    if not os.path.exists(fisier_master):
        print(f"❌ Fișierul master nu există: {fisier_master}")
        return False
    
    print(f"🏗️ Generez rapoarte pentru hub-ul Brașov...")
    generator = create_brasov_generator(fisier_master, data_raport, base_url)
    generator.genereaza_rapoarte()
    return True

def generate_sibiu_reports(data_raport, base_url=None):
    """Generează rapoarte pentru hub-ul Sibiu"""
    if base_url is None:
        base_url = '/Users/telermarius/Library/CloudStorage/Dropbox/DSC/Rapoarte/HUB Brasov/'
    
    fisier_master = f"{base_url}master_data.csv"
    
    if not os.path.exists(fisier_master):
        print(f"❌ Fișierul master nu există: {fisier_master}")
        return False
    
    print(f"🏗️ Generez rapoarte pentru hub-ul Sibiu...")
    generator = create_sibiu_generator(fisier_master, data_raport, base_url)
    generator.genereaza_rapoarte()
    return True

def generate_all_hub_reports(data_raport, base_url=None):
    """Generează rapoarte pentru toate hub-urile"""
    print(f"🏗️ Generez rapoarte pentru toate hub-urile...")
    
    brasov_success = generate_brasov_reports(data_raport, base_url)
    sibiu_success = generate_sibiu_reports(data_raport, base_url)
    
    if brasov_success and sibiu_success:
        print(f"✅ Toate rapoartele au fost generate cu succes!")
    elif brasov_success:
        print(f"⚠️ Doar rapoartele pentru Brașov au fost generate.")
    elif sibiu_success:
        print(f"⚠️ Doar rapoartele pentru Sibiu au fost generate.")
    else:
        print(f"❌ Nu s-au putut genera rapoarte.")

def main():
    """Funcția principală - exemplu de utilizare"""
    
    data_raport = "2025-08-27"  # Format: YYYY-MM-DD
    
    print("Selectează opțiunea:")
    print("1. Generează rapoarte pentru Brașov")
    print("2. Generează rapoarte pentru Sibiu") 
    print("3. Generează rapoarte pentru toate hub-urile")
    
    try:
        optiune = input("Opțiunea (1-3): ").strip()
        
        if optiune == "1":
            generate_brasov_reports(data_raport)
        elif optiune == "2":
            generate_sibiu_reports(data_raport)
        elif optiune == "3":
            generate_all_hub_reports(data_raport)
        else:
            print("❌ Opțiune invalidă. Generez rapoarte pentru Brașov (implicit)...")
            generate_brasov_reports(data_raport)
            
    except KeyboardInterrupt:
        print("\n👋 Operațiune anulată.")
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")

if __name__ == "__main__":
    main()