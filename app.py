from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import os
import zipfile
from werkzeug.utils import secure_filename
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

FIRMAS = {
    'priscilla': 'static/firma_priscilla.png',
    'adriana': 'static/firma_adriana.png',
    'yngrid': 'static/firma_yngrid.png',
    'carolina': 'static/firma_carolina.png',
    'yetzalia': 'static/firma_yetzalia.png',
    'teran': 'static/firma_teran.png',
    'sara': 'static/firma_sara.png',
    'valderas': 'static/firma_valderas.png',
    'simon': 'static/firma_simon.png',
    'Timbre Adriana': 'static/firma_lugo.png',
    'maribel': 'static/firma_maribel.png'  # Nueva firma Maribel
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html', firmas=FIRMAS.keys())

@app.route('/upload', methods=['POST'])
def upload():
    doctora = request.form.get('doctora')
    signature_path = FIRMAS.get(doctora)

    if not signature_path or not os.path.exists(signature_path):
        return "Firma no válida o archivo de firma no encontrado.", 400

    files = request.files.getlist('pdfs')
    signed_pdfs = []

    for file in files:
        if file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            pdf_bytes = file.read()
            signed_pdf = insert_signature(pdf_bytes, signature_path, doctora)
            signed_filename = f"signed_{doctora}_{filename}"
            signed_pdfs.append((signed_filename, signed_pdf))

    if len(signed_pdfs) == 1:
        filename, filedata = signed_pdfs[0]
        return send_file(filedata, as_attachment=True, download_name=filename, mimetype='application/pdf')

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for filename, filedata in signed_pdfs:
            zipf.writestr(filename, filedata.getvalue())

    zip_buffer.seek(0)
    fecha = datetime.now().strftime('%d-%m-%Y')
    zip_name = f"documentos_firmados_{doctora}_{fecha}.zip"
    return send_file(zip_buffer, as_attachment=True, download_name=zip_name, mimetype='application/zip')


def insert_signature(pdf_data, signature_path, doctora=None):
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    signature = fitz.Pixmap(signature_path)

    # Configuración personalizada por doctora
    propiedades_firma = {
        'priscilla': {'size': (150, 60), 'margin': (50, 50)},
        'adriana':   {'size': (300, 150), 'margin': (30, 30)},
        'yngrid':    {'size': (220, 90),  'margin': (90, 110)},
        'carolina':  {'size': (180, 80),  'margin': (90, 110)},
        'yetzalia':  {'size': (200, 85),  'margin': (50, 50)},
        'teran':     {'size': (180, 80),  'margin': (95, 58)},
        'sara':      {'size': (200, 85),  'margin': (125, 58)},
        'valderas':  {'size': (180, 80),  'margin': (60, 60)},
        'Timbre Adriana':  {'size': (150, 60),  'margin': (70, 110)},
        'simon':     {'size': (140, 50),  'margin': (45, 130)},
        'maribel':   {'size': (180, 80),  'margin': (60,75)}  # Configuración de Maribel
    }

    defaults = {'size': (120, 50), 'margin': (50, 50)}
    config = propiedades_firma.get(doctora, defaults)

    sig_width, sig_height = config['size']
    margin_x, margin_y = config['margin']

    for page in doc:
        page_width = page.rect.width
        page_height = page.rect.height

        x0 = page_width - sig_width - margin_x
        y0 = page_height - sig_height - margin_y

        sig_rect = fitz.Rect(x0, y0, x0 + sig_width, y0 + sig_height)
        page.insert_image(sig_rect, pixmap=signature, overlay=True)

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

