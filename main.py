from flask import Flask
from flask_restful import Api, Resource, marshal_with, fields, abort
from flask_sqlalchemy import SQLAlchemy
import time
import threading
from datetime import datetime

# Flask Init
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

status_list = ["Accepted", "Running", "Error", "Complete", "Not-Found"]

# Scan Db entity fields
scan_resource_fields = {
    'id': fields.Integer,
    'status': fields.String,
    'timestamp': fields.String
}


# scan_model table for the sqlite DB
class ScanModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.String, nullable=False)

    def __repr__(self):
        return "ScanModel(status={status}, timestamp={timestamp})"


# scan_id_counter, to keep track the last used scan ID
class ScanIdCounter(db.Model):
    count = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return "ScanIdCounter()"


def update_scan_status(scan_id, status):
    scan = ScanModel.query.filter_by(id=scan_id).first()
    scan.status = status
    db.session.commit()


def scan_process(scan_id):
    print("Started Scan ...")
    update_scan_status(scan_id, status_list[1])  # To Running
    print(threading.current_thread().name)
    time.sleep(10)
    print("completed .....")
    update_scan_status(scan_id, status_list[3])  # To Completed


def add_new_scan(scan_id):
    scan = ScanModel(id=scan_id.count, status=status_list[0], timestamp=str(datetime.now()))
    db.session.add(scan)
    db.session.commit()
    return scan


def update_last_scan_id(scan_id):
    scan_id.count += 1
    db.session.commit()


# Scan status resource
# /status/scan_id
class ScanStatus(Resource):
    @marshal_with(scan_resource_fields)
    def get(self, scan_id):
        scan = ScanModel.query.filter_by(id=scan_id).first()

        if not scan:
            scan = ScanModel()
            scan.status = "Not-Found"

        return scan


# New scan resource
# /new-scan
class ScanIngest(Resource):
    @marshal_with(scan_resource_fields)
    def put(self):
        scan_id = db.session.query(ScanIdCounter).first()
        scan = add_new_scan(scan_id)
        threading.Thread(target=scan_process, args=(scan_id.count,)).start()
        update_last_scan_id(scan_id)
        return scan, 201


# API list
api.add_resource(ScanIngest, '/new-scan')
api.add_resource(ScanStatus, '/status/<int:scan_id>')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
