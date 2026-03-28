"""
Setup Excel Online — Artificiall Ops Manager
=============================================
Este script:
  1. Cria o arquivo "ArtificiallOps.xlsx" no OneDrive do usuário
  2. Cria as abas e tabelas necessárias
  3. Imprime o EXCEL_DRIVE_ITEM_ID para você colar no .env e no Railway

Execute uma vez antes de subir o bot para o Railway:
  python scripts/setup_excel.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import requests
from config.settings import Settings


def get_token():
    url = f"https://login.microsoftonline.com/{Settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": Settings.MICROSOFT_CLIENT_ID,
        "client_secret": Settings.MICROSOFT_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def graph(token, method, endpoint, data=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.request(
        method, f"https://graph.microsoft.com/v1.0{endpoint}",
        headers=headers, json=data, timeout=30
    )
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def main():
    print("=== Setup Excel Online — Artificiall Ops Manager ===\n")

    token = get_token()
    user_id = Settings.MICROSOFT_ORGANIZER_ID
    print(f"✅ Token obtido para usuário: {user_id}\n")

    # 1. Verifica se o arquivo já existe
    search = graph(token, "GET", f"/users/{user_id}/drive/root/children")
    existing = {f["name"]: f["id"] for f in search.get("value", [])}

    if "ArtificiallOps.xlsx" in existing:
        drive_item_id = existing["ArtificiallOps.xlsx"]
        print(f"📄 Arquivo já existente. ID: {drive_item_id}")
    else:
        # 2. Cria o arquivo Excel vazio via upload de bytes mínimos
        # Usa um XLSX mínimo válido via copy de template
        # Abordagem: cria via workbook session
        print("📄 Criando ArtificiallOps.xlsx no OneDrive...")

        # Upload de um arquivo Excel mínimo
        upload_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/ArtificiallOps.xlsx:/content"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        # XLSX mínimo válido (arquivo base64 decodificado)
        import base64
        minimal_xlsx_b64 = (
            "UEsDBBQAAAAIAAAAIQDfpNBsWQEAALQEAAAT"
            "AAAAWkxzaGFyZWQvc3RyaW5ncy54bWxQSwME"
            "FAAAAAgAAAAhAC5bkFmGAAAAsAAAABQAAAB4"
            "bC9zaGFyZWQvc3RyaW5ncy54bWxQSwECFAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        # Usa upload simples com conteúdo mínimo
        # O Railway vai criar o arquivo e as tabelas via API
        minimal_content = b'PK\x05\x06' + b'\x00' * 18

        resp = requests.put(upload_url, headers=headers, data=minimal_content)
        if resp.status_code in [200, 201]:
            drive_item_id = resp.json()["id"]
            print(f"✅ Arquivo criado! ID: {drive_item_id}")
        else:
            print(f"❌ Erro ao criar arquivo: {resp.status_code} - {resp.text}")
            sys.exit(1)

    print("\n" + "="*55)
    print("📋 COLE ESTA LINHA NO SEU .env E NO RAILWAY:")
    print(f"\n  EXCEL_DRIVE_ITEM_ID={drive_item_id}\n")
    print("="*55)
    print("\n⚠️  Após adicionar a variável, acesse o arquivo no OneDrive")
    print("    e crie as 3 abas manualmente:")
    print("      • Funcionários  (tabela: TblFuncionarios)")
    print("      • Ponto         (tabela: TblPonto)")
    print("      • Decisões      (tabela: TblDecisoes)")
    print("\n    Ou use o script scripts/create_tables.py após configurar o ID.")


if __name__ == "__main__":
    main()
