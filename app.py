from flask import Flask, request, jsonify
import json
import requests
import logging
from static_ips import allowed_ips  # Your list of allowed static IPs

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

WEBHOOK_URL = "https://webhook.site/f8d227a8-2d0f-4652-8187-ed64717165c4"  # Your webhook URL

def get_client_ip():
    # Check if the request is behind a proxy and use X-Forwarded-For header if available
    if request.headers.get('X-Forwarded-For'):
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0]  # Get the first IP in the list
        logging.info(f"Request coming from X-Forwarded-For IP: {client_ip}")
        return client_ip
    client_ip = request.remote_addr  # Fallback to remote_addr if no proxy is involved
    logging.info(f"Request coming from remote_addr IP: {client_ip}")
    return client_ip

@app.route('/encode', methods=['POST'])
def encode_request():
    # Get the real client IP address
    request_ip = get_client_ip()

    # Log the incoming request IP
    logging.info(f"Incoming request from IP: {request_ip}")
    logging.info(f"Allowed IPs: {allowed_ips}")

    # Check if the IP is allowed (add debug logs)
    if request_ip not in allowed_ips:
        logging.warning(f"Unauthorized IP attempted to access: {request_ip}")
        logging.warning(f"IP verification failed. Incoming IP: {request_ip} not in {allowed_ips}")
        return jsonify({'error': 'Unauthorized IP', 'ip': request_ip}), 403

    # Check if the request body is JSON and starts with `%{}`
    if request.data:
        try:
            raw_data = request.data.decode('utf-8')
            logging.info(f"Received data: {raw_data}")

            if raw_data.startswith('%{'):
                # Strip the % and parse the dynamic JSON part
                raw_data = raw_data[1:]  # Remove the starting %
                json_data = json.loads(raw_data)

                # Log the processed JSON
                logging.info(f"Processed JSON: {json_data}")

                # Prepare the data to be sent to the webhook
                webhook_payload = {
                    'processed_json': json_data
                }

                # Send the payload to the webhook
                response = requests.post(WEBHOOK_URL, json=webhook_payload)

                # Check if the webhook call was successful
                if response.status_code == 200:
                    logging.info("Webhook call succeeded.")
                    return jsonify({
                        'processed_json': json_data,
                        'webhook_status': 'Success'
                    }), 200
                else:
                    logging.error(f"Webhook call failed with status: {response.status_code}")
                    return jsonify({
                        'processed_json': json_data,
                        'webhook_status': f'Failed with status {response.status_code}'
                    }), 500
            else:
                logging.error("Invalid format, must start with `%{`.")
                return jsonify({'error': 'Invalid format, must start with `%{`'}), 400
        except json.JSONDecodeError:
            logging.error("Malformed JSON received.")
            return jsonify({'error': 'Malformed JSON'}), 400
    else:
        logging.error("No request body provided.")
        return jsonify({'error': 'Request body must be provided'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
