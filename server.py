from flask import Flask, request
import jsonpickle
import base64
from engine import Engine
from datetime import datetime
import os

# Initialize the Flask application
app = Flask(__name__)
hostName = "143.198.148.21"


# route http posts to this method
@app.route('/api/calendar', methods=['POST'])
def test():
    r = request
    image_name = r.headers['image-name']
    is_live = r.headers['live'] == 'True'
    image_64_decode = base64.decodebytes(r.data)

    if image_64_decode:
        image_result = open(f'{image_name}.jpg', 'wb')  # create a writable image and write the decoding result
        image_result.write(image_64_decode)

    folderName = datetime.now().strftime("%m-%d-%Y_%H.%M.%S")
    debugPath = os.path.join(f'{os.getcwd()}/deepData/', folderName)
    os.mkdir(debugPath)
    f = open(f'{debugPath}/log.txt', 'w')
    f.write(f"Request Received At (ZULU Time): {datetime.now().strftime('%m/%d/%Y %H:%M:%S')}\n")
    f.write(f"debugpath {debugPath} isLive {is_live}")
    f.close()

    # encode response using jsonpickle
    e = Engine(debug=debugPath, live=is_live)
    return e.returnResponse()


# start flask app
app.run(host="0.0.0.0", port=5000)