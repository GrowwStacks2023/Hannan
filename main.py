from flask import Flask, request, jsonify
import json
import requests  # Import requests to send payload to the webhook
from static_ips import allowed_ips  # This will hold the static IP pool

app = Flask(__name__)

WEBHOOK_URL = "https://webhook.site/f8d227a8-2d0f-4652-8187-ed64717165c4"  # Set your webhook URL here

@app.route('/encode', methods=['POST'])
def encode_request():
    request_ip = request.remote_addr

    # Check if the IP is allowed
    if request_ip not in allowed_ips:
        return jsonify({'error': 'Unauthorized IP'}), 403

    # Check if the request body is JSON and starts with `%{}`
    if request.data:
        try:
            raw_data = request.data.decode('utf-8')

            if raw_data.startswith('%{'):
                # Strip the % and parse the dynamic JSON part
                raw_data = raw_data[1:]  # Remove the starting %
                json_data = json.loads(raw_data)

                # Prepare the data to be sent to the webhook
                webhook_payload = {
                    'processed_json': json_data
                }

                # Send the payload to the webhook
                response = requests.post(WEBHOOK_URL, json=webhook_payload)

                # Check if the webhook call was successful
                if response.status_code == 200:
                    return jsonify({
                        'processed_json': json_data,
                        'webhook_status': 'Success'
                    }), 200
                else:
                    return jsonify({
                        'processed_json': json_data,
                        'webhook_status': f'Failed with status {response.status_code}'
                    }), 500
            else:
                return jsonify({'error': 'Invalid format, must start with `%{`'}), 400
        except json.JSONDecodeError:
            return jsonify({'error': 'Malformed JSON'}), 400
    else:
        return jsonify({'error': 'Request body must be provided'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
