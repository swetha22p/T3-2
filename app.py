from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from datetime import datetime
from bson.objectid import ObjectId
from bson.errors import InvalidId
from bson.json_util import dumps, loads



app = Flask(__name__)
CORS(app)

LOGSTASH_ENDPOINT = 'http://localhost:9600'
# Configure MongoDB
app.config['MONGO_URI'] = 'mongodb://localhost:27017/your_database_name'
mongo = PyMongo(app)





# @app.route('/get_last_created_at', methods=['GET'])
# def get_last_created_at():
#     # Retrieve the most recently created document
#     last_sync_timestamp_doc = mongo.db.medical_forms.find_one({}, sort=[('createdAt', -1)])
    

#     if last_sync_timestamp_doc:
#         last_created_at_value = last_sync_timestamp_doc['createdAt']
#         return jsonify({'lastCreatedAt': last_created_at_value})
#     else:
#         # Handle the case when no document is found
#         return jsonify({'error': 'No document found in the "medical_forms" collection.'}), 404

# @app.route('/saveSyncTimestamp', methods=['GET'])
# def save_sync_timestamp():
#     try:
        
#         timestamp = mongo.db.medical_forms.find_one(sort=[('createdAt', -1)],projection={'createdAt': 1})
#         timestamp= timestamp['createdAt']
#         print(f'createdAt value: {timestamp}')
#         # Save the sync timestamp to MongoDB
#         # mongo.db.syncTimestamps.insert_one({'timestamp': timestamp})

#         return jsonify({"message": "Sync timestamp saved successfully"})
#     except Exception as e:
#         print('Error saving sync timestamp to MongoDB:', str(e))
#         return jsonify({"error": str(e)}), 500




@app.route('/get_last_created_at', methods=['GET'])
def get_last_created_at():
    try:
        # Find the document with the latest createdAt value
        latest_document = mongo.db.medical_forms.find_one(sort=[('createdAt', -1)], projection={'createdAt': 1})
        
        # Check if there is a document
        if latest_document:
            timestamp = latest_document['createdAt']
            return jsonify({'lastSyncTimestamp': timestamp})
        else:
            timestamp = 0
            utc_formatted_timestamp = datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%a, %d %b %Y %H:%M:%S GMT')
            return jsonify({'lastSyncTimestamp': utc_formatted_timestamp})
    except Exception as e:
        return jsonify({'error': str(e)})
    


@app.route('/save_sync_timestamp', methods=['GET'])
def save_sync_timestamp():
    try:
        # Get the current timestamp
        current_timestamp = datetime.utcnow()

        # Insert a new document with the current timestamp
        result = mongo.db.medical_forms.insert_one({'createdAt': current_timestamp})

        if result.inserted_id:
            return jsonify({'message': 'Sync timestamp saved successfully'})
        else:
            return jsonify({'error': 'Failed to save sync timestamp'})
    except Exception as e:
        return jsonify({'error': str(e)})


    




@app.route('/bulkAddMedicalData', methods=['OPTIONS'])
def handle_options():
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Methods'] = 'POST'  # Add other allowed methods if needed
    return response
@app.route('/submit', methods=['POST'])
def submit():
    message = request.form['message']
    
    # Send message to Logstash
    logstash_payload = {'message': message}
    response = requests.post(LOGSTASH_ENDPOINT, json=logstash_payload)
    
    if response.status_code == 200:
        return 'Message submitted successfully!'
    else:
        return 'Error submitting message to Logstash'
@app.route('/medicalForm', methods=['POST'])
def save_medical_form():
    try:
        medical_data = request.json

        # Validate the data here (ensure required fields are present, etc.)

        # Add timestamp to the data
        medical_data['createdAt'] = datetime.utcnow()

        # Store the data in MongoDB
        mongo.db.medical_forms.insert_one(medical_data)

        return jsonify({"message": "Medical form data saved successfully"})
    except Exception as e:
        app.logger.error(f"Error saving medical form data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/getMedicalData', methods=['GET'])
def get_medical_data():
    try:
        medical_data = list(mongo.db.medical_forms.find())  # Retrieve all medical records

        # Convert ObjectId to string in the response using dumps
        serialized_data = dumps(medical_data)

        return serialized_data
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/getMedicalData/<string:id>', methods=['GET'])
def get_medical_data_by_id(id):
    try:
        # Use ObjectId to convert the string id to a valid ObjectId
        medical_data = mongo.db.medical_forms.find_one({'_id': ObjectId(id)})

        if medical_data:
            # Convert ObjectId to string in the response using dumps
            serialized_data = dumps(medical_data)
            return serialized_data
        else:
            return jsonify({"message": "Medical record not found"}), 404

    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/deleteMedicalData/<string:id>', methods=['DELETE'])
def delete_medical_data(id):
    try:
        # Use ObjectId to convert the string id to a valid ObjectId
        mongo.db.medical_forms.delete_one({'_id': ObjectId(id)})

        return jsonify({"message": "Medical record deleted successfully"})
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/updateMedicalData/<string:id>', methods=['PUT', 'PATCH'])
def update_medical_data(id):
    try:
        # Ensure that the request has a JSON payload
        if not request.is_json:
            raise BadRequest("Invalid request format. JSON expected.")

        # Get the updated data from the JSON payload
        updated_data = request.json

        # Validate the updated data here if needed

        # Use ObjectId to convert the string id to a valid ObjectId
        mongo.db.medical_forms.update_one({'_id': ObjectId(id)}, {'$set': updated_data})

        return jsonify({"message": "Medical record updated successfully"})
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except InvalidId:
        return jsonify({"error": "Invalid ObjectId"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/medicalForm/<email>', methods=['GET'])
def get_medical_form(email):
    try:
        medical_form = mongo.db.medical_forms.find_one({'email': email})

        if not medical_form:
            

            return jsonify({'message': 'Medical form not found'}), 404
        
        medical_form['_id'] = str(medical_form['_id'])


        return jsonify(medical_form)
    except Exception as e:
        print('Error fetching medical form:', str(e))
        return jsonify({'message': 'Internal Server Error'}), 500
    


if __name__ == '__main__':
    app.run(debug=True)
