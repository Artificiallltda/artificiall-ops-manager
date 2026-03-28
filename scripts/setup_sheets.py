#!/usr/bin/env python3
"""
Script de setup inicial do Artificiall Ops Manager.

Cria as abas no Google Sheets e configura headers.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from integrations.google_sheets import GoogleSheetsIntegration


def main():
    """Run setup script."""
    print("🚀 Artificiall Ops Manager - Setup Script")
    print("=" * 50)

    # Validate settings
    print("\n📋 Validando configuração...")
    if not Settings.validate():
        print("❌ Erro: Configuração inválida. Verifique o arquivo .env")
        sys.exit(1)
    print("✅ Configuração válida")

    # Initialize Google Sheets integration
    print("\n📊 Conectando ao Google Sheets...")
    try:
        sheets = GoogleSheetsIntegration(
            sheet_id=Settings.GOOGLE_SHEET_ID,
            service_account_json=Settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        )
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)

    # Ensure sheets exist
    print("\n📁 Verificando abas...")
    if sheets.ensure_sheets_exist():
        print("✅ Abas configuradas com sucesso:")
        print("   - Funcionários")
        print("   - Ponto")
        print("   - Decisões")
    else:
        print("❌ Erro ao configurar abas")
        sys.exit(1)

    # Test connection
    print("\n🧪 Testando conexão...")
    try:
        # Try to read from sheets
        worksheet = sheets._get_worksheet("Funcionários")
        print(f"✅ Conexão bem-sucedida: {worksheet.title}")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("✅ Setup concluído com sucesso!")
    print("\nPróximos passos:")
    print("1. Execute: python bot.py")
    print("2. No Telegram, envie: /start")
    print("3. Registre administradores: /registrar @user Nome +5511999998888 Cargo")
    print("4. Teste os comandos: /cheguei, /fui, /reuniao, /decisao")


if __name__ == "__main__":
    main()
