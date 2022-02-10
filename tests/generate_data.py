import os, sys, logging
import csv, time
import random, string

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from config import PROJECT_ROOT
sys.path.append(PROJECT_ROOT)
from src.instrument_stream import InstrumentStream
from app import app

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel('INFO')

t_end = time.time() + (60 * 5)   # 5 mins from now
logger.info(f"start time: {time.ctime()}")

stream = InstrumentStream()
for event in stream.read():
    if time.time() > t_end:
        break

    # Adding random userid to event stream, for tests
    event.update({"userid": random.choice(string.ascii_letters.upper())})
    event['instrid'] = event.pop('id')  # renaming id -> instrid

    # Add into DB
    with app.test_client() as client:
        resp = client.post('/add/request', json=event)
        if resp.status_code != 200:
            logging.error(resp)

    # Optionally, also write to csv for tests
    with open(os.path.join(PROJECT_ROOT, 'data/test_instruments_dataset.csv'), mode='a') as csv_file:
        fieldnames = list(event.keys())
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if csv_file.tell() == 0:
            writer.writeheader()
        writer.writerow(event)

    # print(event)
logger.info(f"end time: {time.ctime()}")
