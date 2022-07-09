from flask import Flask
from flask_restful import Api, Resource, marshal_with, fields, abort
from flask_sqlalchemy import SQLAlchemy
import time
import threading
from datetime import datetime, timedelta
from enum import Enum


class Statuses(Enum):
    ACCEPTED = 1
    RUNNING = 2
    COMPLETE = 3
    ERROR = 4
    NOT_FOUND = 5


status_list = {
    Statuses.ACCEPTED: "Accepted",
    Statuses.RUNNING: "Running",
    Statuses.ERROR: "Error",
    Statuses.COMPLETE: "Complete",
    Statuses.NOT_FOUND: "Not-Found"
}

# Scan Db entity fields
scan_resource_fields = {
    'id': fields.Integer,
    'status': fields.String,
    'timestamp': fields.String
}

# Flask and SQLAlchemy Init
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


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


def clear_old_statuses():
    current_time = datetime.now()
    twenty_minutes_ago = current_time - timedelta(minutes=20)
    db.session.query(ScanModel).filter(ScanModel.timestamp < twenty_minutes_ago).delete()
    db.session.commit()


def update_scan_status(scan_id, status):
    scan = ScanModel.query.filter_by(id=scan_id).first()
    scan.status = status
    db.session.commit()


def scan_process(scan_ids, simulate_error=False):
    for scan_id in scan_ids:
        status = status_list[Statuses.ERROR]
        print("Started Scan ...")
        update_scan_status(scan_id, status_list[Statuses.RUNNING])  # To Running
        print(threading.current_thread().name)
        time.sleep(10)
        if not simulate_error:
            print("completed .....")
            status = status_list[Statuses.COMPLETE]
        update_scan_status(scan_id, status)  # To Completed


def add_new_scan(scan_id):
    scan = ScanModel(id=scan_id.count, status=status_list[Statuses.ACCEPTED], timestamp=str(datetime.now()))
    if not scan:
        return None
    db.session.add(scan)
    db.session.commit()
    return scan


def update_last_scan_id(scan_id):
    scan_id.count += 1
    db.session.commit()


def generate_scan_id():
    # Should actually be done with Base64 or any other hashing algo
    return db.session.query(ScanIdCounter).first()


# Scan status resource
# /status/scan_id
class ScanStatus(Resource):
    @marshal_with(scan_resource_fields)
    def get(self, scan_id):
        # Could be done with a cache manager also
        clear_old_statuses()
        scan = ScanModel.query.filter_by(id=scan_id).first()

        if not scan:
            scan = ScanModel()
            scan.status = status_list[Statuses.NOT_FOUND]

        return scan


# New scan resource
# /new-scan
class ScanIngest(Resource):
    def __init__(self, simulate_error=False):
        self.simulate_error = simulate_error

    @marshal_with(scan_resource_fields)
    def put(self):
        scan_id = generate_scan_id()
        scan = add_new_scan(scan_id)
        if not scan:
            scan.status = status_list[Statuses.ERROR]
            return scan, 500
        threading.Thread(target=scan_process, args=([scan_id.count], self.simulate_error)).start()
        update_last_scan_id(scan_id)
        return scan, 201


# API list
api.add_resource(ScanIngest, '/new-scan')
api.add_resource(ScanStatus, '/status/<int:scan_id>')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
