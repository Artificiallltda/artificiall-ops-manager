"""
Setup Excel Online — Artificiall Ops Manager
=============================================
Este script:
  1. Cria o arquivo "ArtificiallOps.xlsx" no OneDrive do usuário
  2. Imprime o EXCEL_DRIVE_ITEM_ID para você colar no .env e no Railway
  3. Em seguida, execute: python scripts/create_tables.py

Execute uma vez antes de subir o bot para o Railway:
  python scripts/setup_excel.py
"""

import sys
import os
import io
import zipfile
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


def create_valid_xlsx():
    """Gera bytes de um arquivo .xlsx mínimo e válido (ZIP com XMLs corretos)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>')
        z.writestr("_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
        z.writestr("xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData/>'
            '</worksheet>')
    buf.seek(0)
    return buf.read()


def main():
    print("=== Setup Excel Online — Artificiall Ops Manager ===\n")

    token = get_token()
    user_id = Settings.MICROSOFT_ORGANIZER_ID
    print(f"✅ Token obtido para usuário: {user_id}\n")

    # 1. Verifica se o arquivo já existe e remove o corrompido
    search = graph(token, "GET", f"/users/{user_id}/drive/root/children")
    existing = {f["name"]: f["id"] for f in search.get("value", [])}

    if "ArtificiallOps.xlsx" in existing:
        old_id = existing["ArtificiallOps.xlsx"]
        print(f"📄 Arquivo existente encontrado. Removendo arquivo antigo...")
        requests.delete(
            f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/items/{old_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

    # 2. Cria o arquivo Excel válido
    print("📄 Criando ArtificiallOps.xlsx no OneDrive...")
    upload_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/ArtificiallOps.xlsx:/content"
    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    xlsx_bytes = create_valid_xlsx()
    resp = requests.put(upload_url, headers=upload_headers, data=xlsx_bytes)

    if resp.status_code in [200, 201]:
        drive_item_id = resp.json()["id"]
        print(f"✅ Arquivo criado! ID: {drive_item_id}")
    else:
        print(f"❌ Erro ao criar arquivo: {resp.status_code} - {resp.text}")
        sys.exit(1)

    print("\n" + "="*55)
    print("📋 EXCEL_DRIVE_ITEM_ID para o .env e Railway:")
    print(f"\n  EXCEL_DRIVE_ITEM_ID={drive_item_id}\n")
    print("="*55)
    print("\n✅ Próximo passo: python scripts/create_tables.py")


if __name__ == "__main__":
    main()
