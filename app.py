from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import os
import zipfile
from werkzeug.utils import secure_filename
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Diccionario de firmas disponibles
FIRMAS = {
    'priscilla': 'static/firma_priscilla.png',
    'adriana': 'static/firma_adriana.png',
    'yngrid': 'static/firma_yngrid.png',
    'carolina': 'static/firma_carolina.png'
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html', firmas=FIRMAS.keys())

@app.route('/upload', methods=['POST'])
def upload():
    doctora = request.form.get('doctora')  # Obtener opción de firma
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

    # Múltiples PDFs → crear archivo ZIP
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

    # Tamaños personalizados por doctora
    tamaños_firma = {
        'priscilla': (150, 60),
        'adriana': (140, 50),
        'yngrid': (180, 80),
        'carolina': (160, 65)
    }

    # Usa el tamaño correspondiente o uno por defecto
    sig_width, sig_height = tamaños_firma.get(doctora, (120, 50))

    for page in doc:
        x0 = 370
        y0 = 700
        sig_rect = fitz.Rect(x0, y0, x0 + sig_width, y0 + sig_height)
        page.insert_image(sig_rect, pixmap=signature, overlay=True)

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)






