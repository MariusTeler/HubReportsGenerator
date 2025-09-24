#!/usr/bin/env python3
"""
Script pentru configurarea sistemului de email
"""

import os
from email_reporting_system import EmailReportingSystem

def setup_email_system():
    """Configurează sistemul de email"""
    print("🚀 Configurare sistem de email HUB Reporting")
    print("=" * 50)
    
    # Inițializează sistemul
    email_system = EmailReportingSystem()
    
    print(f"📊 Baza de date: {email_system.db_path}")
    
    # Creează template-urile
    print("\n⚙️ Creez template-urile de configurare...")
    
    config_path = email_system.create_email_config_template()
    addresses_path = email_system.create_email_addresses_template()
    
    print(f"✅ Template configurație email: {config_path}")
    print(f"✅ Template adrese email centre: {addresses_path}")
    
    print("\n" + "=" * 50)
    print("📝 Pași următori:")
    print("1. Editați fișierul email_config.json cu credențialele SMTP")
    print("2. Editați fișierul Excel email_addresses_centre.xlsx cu adresele corecte")
    print("3. Utilizați enhanced_hub_generator.py pentru a genera și trimite rapoarte")
    print("\n📋 Format Excel:")
    print("• Coloana 'Adrese_Email': separate cu ; (punct și virgulă)")
    print("• Coloana 'Activ': DA/NU pentru a activa/dezactiva centre")
    print("• Exemple: email1@company.com; email2@company.com")
    print("\n💡 Pentru Gmail, folosiți un App Password în loc de parola normală")
    print("💡 Activați 2-Factor Authentication și generați App Password din Google Account")

if __name__ == "__main__":
    setup_email_system()