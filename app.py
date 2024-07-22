import logging
from flask import Flask, render_template, make_response, jsonify, request
from weasyprint import HTML
from num2words import num2words
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
cred = credentials.Certificate("./ereservation-f5852-firebase-adminsdk-fhiyz-4dcf86734f.json")
firebase_admin.initialize_app(cred)
# Initialize Firestore DB
db = firestore.client()

@app.route('/testing')
def testing():
    return "Hello World"

@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    try:
        users_ref = db.collection('data_pemesanan')
        docs = users_ref.stream()

        users = []
        for doc in docs:
            user = doc.to_dict()
            user['id'] = doc.id
            users.append(user)

        return jsonify(users), 200

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return f"An error occurred: {e}", 500

@app.route('/pdf/pemesanan/<doc_id>')
def generate_pemesanan(doc_id):
    try:
        # Fetch the specific document from Firestore collection 'data_pemesanan'
        doc_ref = db.collection('data_pemesanan').document(doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return f"Document with ID {doc_id} does not exist", 404

        order = doc.to_dict()

        # Parse the items in the order
        items = []
        counter = 1
        for key, item in order.items():
            if isinstance(item, dict):
                items.append({
                    "no": counter,
                    "nama_barang": item.get("nama_barang", ""),
                    "qty": item.get("quantity", 0),
                    "satuan": item.get("satuan", ""),
                    "keterangan": item.get("keterangan", "")
                })
                counter += 1

        # Get other details from the order
        order_date_time = order.get("date", "")
        order_date = order_date_time.split(' ')[0] + ' ' + order_date_time.split(' ')[1] + ' ' + order_date_time.split(' ')[2] if order_date_time else ""
        tujuan = order.get("tujuan", "")
        cc = order.get("cc", "")

        # Render the template with fetched data and the order date
        rendered_html = render_template('pemesanan.html', items=items, order_date=order_date, tujuan=tujuan, cc=cc)

        # Generate PDF using WeasyPrint
        pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

        # Create a response object
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=form_pemesanan_konsumsi_{doc_id}.pdf'

        return response

    except Exception as e:
        logging.error(f"Error generating PDF for pemesanan: {e}")
        return f"An error occurred: {e}", 500


@app.route('/pdf/pengajuan/<doc_id>')
def generate_pengajuan(doc_id):
    try:
        doc_ref = db.collection('data_pengajuan').document(doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return f"Document with ID {doc_id} does not exist", 404

        order = doc.to_dict()
        items = []
        counter = 1
        total = 0
        for key, item in order.items():
            if isinstance(item, dict):
                jumlah = int(item.get("jumlah_barang", 0))
                satuan_harga = int(item.get("satuan_harga", ""))
                total_satuan = jumlah * satuan_harga
                items.append({
                    "no": counter,
                    "uraian": item.get("uraian", ""),
                    "jumlah": "{:,}".format(jumlah).replace(',', '.'),
                    "satuan_harga": "{:,}".format(satuan_harga).replace(',', '.'),
                    "total_satuan": "{:,}".format(total_satuan).replace(',', '.')
                })
                counter += 1
                total += total_satuan

        angka = int(total)
        teks = num2words(angka, lang='id')
        teks_kapital = teks.capitalize() + " rupiah"
        teks_kapital = "\"" + teks_kapital + "\""
        total = "{:,}".format(total).replace(',', '.')
        order_date_time = order.get("date", "")
        order_date = order_date_time.split(' ')[0] + ' ' + order_date_time.split(' ')[1] + ' ' + order_date_time.split(' ')[2] if order_date_time else ""
        cc = order.get("cc","")

        rendered_html = render_template('pengajuan.html', items=items, order_date=order_date, total=total, teks_kapital=teks_kapital, cc=cc)

        pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=form_pengajuan_{doc_id}.pdf'

        return response

    except Exception as e:
        logging.error(f"Error generating PDF for pengajuan: {e}")
        return f"An error occurred: {e}", 500

@app.route('/pdf/pertanggungjawab/<doc_id>')
def generate_pertanggungjawab(doc_id):
    try:
        doc_ref = db.collection('data_pengajuan').document(doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            return f"Document with ID {doc_id} does not exist", 404

        order = doc.to_dict()
        items = []
        modified_order = order.get("modifiedPengajuan", {})
        counter = 1
        total = 0
        for key, item in modified_order.items():
            if isinstance(item, dict):
                items.append({
                    "no": counter,
                    "uraian": item.get("uraian", ""),
                    "jumlah": item.get("jumlah", 0),
                    "satuan_harga": item.get("satuan_harga", ""),
                })
                counter += 1

        order_date = modified_order.get("date", "")

        rendered_html = render_template('pertanggungjawab.html', items=items, order_date=order_date, total=total)

        pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=form_pertanggungjawab_{doc_id}.pdf'

        return response

    except Exception as e:
        logging.error(f"Error generating PDF for pertanggungjawab: {e}")
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
