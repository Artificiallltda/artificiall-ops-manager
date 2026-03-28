"""
PDF Generator - Artificiall Ops Manager
========================================
Gera o manual do usuário em PDF usando xhtml2pdf.
"""

import sys
import os
from xhtml2pdf import pisa             # import python module

# Define o conteúdo HTML (pode ser o mesmo do manual premium)
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: a4;
            margin: 2cm;
        }
        body {
            font-family: Helvetica, Arial, sans-serif;
            color: #333;
            line-height: 1.5;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #0078d4;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #0078d4;
        }
        h1 {
            font-size: 20px;
            color: #666;
            margin: 0;
        }
        .section {
            margin-bottom: 25px;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 5px solid #0078d4;
        }
        .section-title {
            font-weight: bold;
            color: #0078d4;
            font-size: 16px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .command {
            font-family: monospace;
            background-color: #eee;
            padding: 2px 5px;
            font-weight: bold;
            color: #d1123e;
        }
        .footer {
            text-align: center;
            font-size: 10px;
            color: #999;
            margin-top: 50px;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">ARTIFICIALL OPS MANAGER</div>
        <h1>Manual do Usuário - Comandos Telegram</h1>
    </div>

    <div class="section">
        <div class="section-title">🕒 Ponto Eletrônico</div>
        <p><span class="command">/cheguei</span> : Registra o início da sua jornada de trabalho.</p>
        <p><span class="command">/fui</span> : Registra o encerramento da sua jornada.</p>
        <p><i>Nota: Pode ser feito no grupo da empresa ou no privado com o bot.</i></p>
    </div>

    <div class="section" style="border-left-color: #28a745;">
        <div class="section-title">🎥 Reuniões e Vídeo</div>
        <p><span class="command">/reuniao [tema] [@usuario ou e-mail]</span> : Cria convite no Outlook e Teams.</p>
        <p><span class="command">/reuniao [tema] DD/MM/AAAA HH:MM [@usuario]</span> : Agenda reunião futura.</p>
        <p><i>Nota: O bot converte automaticamente @nomedeusuario no e-mail cadastrado.</i></p>
    </div>

    <div class="section" style="border-left-color: #ffc107;">
        <div class="section-title">⚖️ Governança e Decisões</div>
        <p><span class="command">/decisao [texto]</span> : (CEO) Registra decisões estratégicas no Excel.</p>
    </div>

    <div class="section" style="border-left-color: #6c757d;">
        <div class="section-title">🛠️ Administração</div>
        <p><span class="command">/registrar @usuario Nome Telefone E-mail Cargo</span> : Cadastra novo colaborador.</p>
        <p><span class="command">/help</span> : Lista de comandos ativos.</p>
    </div>

    <div class="footer">
        Artificiall LTDA © 2026 - Gestão Integrada Microsoft 365
    </div>
</body>
</html>
"""

def convert_html_to_pdf(source_html, output_filename):
    # open output file for writing (truncated binary)
    result_file = open(output_filename, "w+b")

    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
            source_html,                # the HTML to convert
            dest=result_file)           # file handle to recieve result

    # close output file
    result_file.close()                 # close output file

    # return True on success and False on errors
    return pisa_status.err

if __name__ == "__main__":
    output_path = "docs/manual_usuario.pdf"
    print(f"📄 Gerando PDF em: {output_path}...")
    
    if not os.path.exists("docs"):
        os.makedirs("docs")
        
    err = convert_html_to_pdf(HTML_CONTENT, output_path)
    if not err:
        print("✅ PDF gerado com sucesso!")
    else:
        print(f"❌ Erro ao gerar PDF: {err}")
