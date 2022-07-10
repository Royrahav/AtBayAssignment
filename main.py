from flask import Flask
from flask_restful import Api, Resource, marshal_with, fields, abort, reqparse
from flask_sqlalchemy import SQLAlchemy
import time
import threading
from datetime import datetime, timedelta
from enum import Enum


#################
#   Globals     #
#################

# For statuses readability
class Statuses(Enum):
    ACCEPTED = 1
    RUNNING = 2
    COMPLETE = 3
    ERROR = 4
    NOT_FOUND = 5


# Statuses actual value
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

# Scan request argument list
scan_post_args = reqparse.RequestParser()
scan_post_args.add_argument("simulate-error", type=bool, help="For testing", required=False)
scan_post_args.add_argument("sleeping-time", type=int, help="For testing", required=False)

###################################
#   Flask and SQLAlchemy Init     #
###################################

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


###########################
#   SQLAlchemy models     #
###########################


# scan_model table for the sqlite DB
class ScanModel(db.Model):
    """
    Contains three columns:

    id: Scan unique id
    status: Scan current status
    timestamp: Scan adding time
    """
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.String, nullable=False)

    def __repr__(self):
        return "ScanModel(status={status}, timestamp={timestamp})"


# scan_id_counter, to keep track the last used scan ID
class ScanIdCounter(db.Model):
    """
    A "counter table", to mock cache, that saves the latest used scan id
    """
    count = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return "ScanIdCounter()"


#######################
#   Functionality     #
#######################


def clear_old_statuses(minutes):
    """
    Clears statuses that are older than "minutes" minutes ago
    """
    current_time = datetime.now()
    minutes_ago = current_time - timedelta(minutes=minutes)
    db.session.query(ScanModel).filter(ScanModel.timestamp < minutes_ago).delete()
    db.session.commit()


def update_scan_status(scan_id, status):
    """
    Updates the scan status to the value that being sent into the function
    Updates it to the scan_id value that being sent into the function
    """
    scan = ScanModel.query.filter_by(id=scan_id).first()
    scan.status = status
    db.session.commit()


def scan_process(scan_ids, simulate_error=False, sleeping_time=10):
    """
    Mocks the actual scan process
    Refers to the "Process" section in the assignment's specifications
    Supports a list of scan_ids, to process in a bulk
    """
    for scan_id in scan_ids:
        status = status_list[Statuses.ERROR]  # Initially Error status
        print("Started Scan ...")
        update_scan_status(scan_id, status_list[Statuses.RUNNING])  # To Running status
        print(threading.current_thread().name)
        time.sleep(sleeping_time)
        if not simulate_error:
            print("Completed .....")
            status = status_list[Statuses.COMPLETE]
        update_scan_status(scan_id, status)  # To Completed status


def add_new_scan(scan_id):
    """
    Creates a new scan entity, and commits it to the DB
    """
    scan = ScanModel(id=scan_id.count, status=status_list[Statuses.ACCEPTED], timestamp=str(datetime.now()))
    print(f"New scan been added. Scan id: {scan_id.count}. Status: {scan.status}")
    if not scan:
        return None
    db.session.add(scan)
    db.session.commit()
    return scan


def update_last_scan_id(scan_id):
    """
    Updates last scan id cache mock value
    """
    scan_id.count += 1
    db.session.commit()


def generate_scan_id():
    """
    Generates a new scan id to assign for a new value
    """
    # Should actually be done with Base64 or any other hashing algo
    return db.session.query(ScanIdCounter).first()


#########################
#   Flask resources     #
#########################


# Scan status resource
# /status/scan_id
class ScanStatus(Resource):
    """
    scan_status resource logic
    Has only GET request, to check the status of a specific scan_id
    Refers to the "Status" section in the assignment specifications
    """

    @marshal_with(scan_resource_fields)
    def get(self, scan_id):
        # Could be done with a cache manager also
        clear_old_statuses(20)  # 20 minutes
        scan = ScanModel.query.filter_by(id=scan_id).first()

        if not scan:
            scan = ScanModel()
            scan.status = status_list[Statuses.NOT_FOUND]

        return scan


# New scan resource
# /new-scan
class ScanIngest(Resource):
    """
    scan_ingest resource logic
    Has only POST request, to initiate a new scan
    Works threaded, so it creates a new thread for each scan request
    Refers to the "Ingest" section in the assignment specifications

    Has two parameters, for testing purposes:
    simulate-error- to test a situation where we have a scan error
    sleeping-time- to control the length of the scan-mock
    """
    def __init__(self, simulate_error=False, sleeping_time=10):
        self.simulate_error = simulate_error
        self.sleeping_time = sleeping_time

    @marshal_with(scan_resource_fields)
    def post(self):
        # For simulating an error
        args = scan_post_args.parse_args()
        if args['simulate-error']:
            self.simulate_error = True
        if args['sleeping-time']:
            self.sleeping_time = args['sleeping-time']

        scan_id = generate_scan_id()
        scan = add_new_scan(scan_id)
        if not scan:
            scan.status = status_list[Statuses.ERROR]
            return scan, 500
        threading.Thread(target=scan_process, args=([scan_id.count], self.simulate_error, self.sleeping_time)).start()
        update_last_scan_id(scan_id)
        return scan, 201


################################
#   Resources registration     #
################################

# API list
api.add_resource(ScanIngest, '/new-scan')
api.add_resource(ScanStatus, '/status/<int:scan_id>')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
