from flask import Flask, render_template, make_response, jsonify, request
from weasyprint import HTML
from num2words import num2words
from dotenv import load_dotenv
load_dotenv()


import os
import firebase_admin
from firebase_admin import credentials, firestore



app = Flask(__name__)
service_key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
cred = credentials.Certificate("./ereservation-f5852-firebase-adminsdk-fhiyz-e5444c7ba7.json")
firebase_admin.initialize_app(cred)
# Initialize Firestore DB
db = firestore.client()


@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    try:
        # Reference to your Firestore collection
        users_ref = db.collection('data_pemesanan')
        docs = users_ref.stream()

        # Process and structure the data
        users = []
        for doc in docs:
            user = doc.to_dict()
            user['id'] = doc.id
            users.append(user)

        return jsonify(users), 200

    except Exception as e:
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

        items = []
        modified_order = order.get("modifiedOrder", {})
        counter=1
        for key, item in modified_order.items():
            if isinstance(item, dict):
                items.append({
                    "no": counter,
                    "nama_barang": item.get("nama_barang", ""),
                    "qty": item.get("quantity", 0),
                    "satuan": item.get("satuan", ""),
                    "keterangan": item.get("keterangan", "")
                })
                counter+=1
                

        order_date = modified_order.get("date", "")
        tujuan = modified_order.get("tujuan", "")   
        cc = modified_order.get("cc", "")

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
        return f"An error occurred: {e}", 500
    

@app.route('/pdf/pengajuan/<doc_id>')
def generate_pengajuan(doc_id):
    try:
        # Fetch the specific document from Firestore collection 'data_pemesanan'
        doc_ref = db.collection('data_pengajuan').document(doc_id)
        doc = doc_ref.get()


        if not doc.exists:
            return f"Document with ID {doc_id} does not exist", 404

        order = doc.to_dict()

        items = []
        modified_order = order.get("modifiedPengajuan", {})
        counter=1
        total=0
        for key, item in modified_order.items():
            if isinstance(item, dict):
                jumlah = int(item.get("jumlah", 0))
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
        
        teks_kapital = teks.capitalize()
        teks_kapital += " rupiah"
        teks_kapital = "\"" + teks_kapital + "\""
        
        
        total = "{:,}".format(total).replace(',', '.')
        order_date = modified_order.get("date", "")
        
        
        


        # Render the template with fetched data and the order date
        rendered_html = render_template('pengajuan.html', items=items, order_date=order_date, total=total, teks_kapital=teks_kapital)

        # Generate PDF using WeasyPrint
        pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

        # Create a response object
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=form_pemesanan_konsumsi_{doc_id}.pdf'

        return response

    except Exception as e:
        return f"An error occurred: {e}", 500
    

@app.route('/pdf/pertanggungjawab/<doc_id>')
def generate_pertanggungjawab(doc_id):
    try:
        # Fetch the specific document from Firestore collection 'data_pemesanan'
        doc_ref = db.collection('data_pengajuan').document(doc_id)
        doc = doc_ref.get()


        if not doc.exists:
            return f"Document with ID {doc_id} does not exist", 404

        order = doc.to_dict()

        items = []
        modified_order = order.get("modifiedPengajuan", {})
        counter=1
        total=0
        for key, item in modified_order.items():
            if isinstance(item, dict):
                items.append({
                    "no": counter,
                    "uraian": item.get("uraian", ""),
                    "jumlah": item.get("jumlah", 0),
                    "satuan_harga": item.get("satuan_harga", ""),
                })
                counter+=1
                
                
        
        order_date = modified_order.get("date", "")
        


        # Render the template with fetched data and the order date
        rendered_html = render_template('pertanggungjawab.html', items=items, order_date=order_date, total=total)

        # Generate PDF using WeasyPrint
        pdf = HTML(string=rendered_html, base_url=request.base_url).write_pdf()

        # Create a response object
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=form_pemesanan_konsumsi_{doc_id}.pdf'

        return response

    except Exception as e:
        return f"An error occurred: {e}", 500
    



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
