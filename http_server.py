from flask import Flask, request, Response
import urllib
import time
import hashlib
from Crypto.Cipher import AES
import Crypto.Cipher.AES
from binascii import hexlify, unhexlify
from threading import Thread


from motor_control import *
from database import *
from crypto import *

api = Flask(__name__)


@api.route('/forward', methods=['GET'])
def forward_move():
    rev_per_second = float(request.args.get('rev', type=float))
    run_time = float(request.args.get('time', type=float))
    if rev_per_second < 0:
        return "rev must be greater than 0."
    if rev_per_second > 2:
        return "Too fast!"
    if run_time < 0:
        return "run_time must be greater than 0."
    if run_time > 10:
        return "Too long!"
    enable_motor()
    start_motor(rev_per_second, run_time, False)
    cleanup_pins()
    disable_motor()
    return "Forward moving."


@api.route('/reverse', methods=['GET'])
def reverse_move():
    rev_per_second = float(request.args.get('rev', type=float))
    run_time = float(request.args.get('time', type=float))
    if rev_per_second < 0:
        return "rev must be greater than 0."
    if rev_per_second > 2:
        return "Too fast!"
    if run_time < 0:
        return "run_time must be greater than 0."
    if run_time > 10:
        return "Too long!"
    enable_motor()
    start_motor(rev_per_second, run_time, True)
    cleanup_pins()
    disable_motor()
    return "Reverse moving."


@api.route('/register_user', methods=['GET'])
def register_user():
    device_type = request.args.get('type', type=str)
    device_id = request.args.get('device_id', type=str)
    pre_shared_secret = request.args.get('pre_shared_secret', type=str)
    certificate = urllib.request.unquote(request.args.get('certificate', type=str))
    if verify_client_certificate(certificate):
        database_add_user(device_type, device_id, pre_shared_secret, certificate)
        return "Successfully added user."
        # return Response("{'status':'0', 'msg':'User added.'}", status=200, mimetype='application/json')
    else:
        return "Failed to add user."
        # return Response("{'status':'-1', 'msg':'Information is invalid.'}", status=403, mimetype='application/json')


@api.route('/remove_user', methods=['GET'])
def remove_user():
    timestamp = int(request.args.get('timestamp', type=int))
    current_time = int(time.time())
    if abs(current_time - timestamp) > 10:
        return Response("Request expired.\n", status=403)

    signature = str(request.args.get('signature', type=str))
    device_id = str(request.args.get('device_id', type=str))
    certificate = str(get_certificate(device_id))
    pre_shared_secret = str(get_pre_shared_secret(device_id))
    message = "Remove" + str(timestamp) + device_id + pre_shared_secret
    if verify_signature(message, signature, certificate):
        database_remove_user(device_id)
        return "User removed."
    else:
        return "Failed to remove user."


@api.route('/enable_user', methods=['GET'])
def enable_user():
    device_id = str(request.args.get('device_id', type=str))
    database_enable_user(device_id)
    return "Enabling user."


@api.route('/disable_user', methods=['GET'])
def disable_user():
    device_id = str(request.args.get('device_id', type=str))
    database_disable_user(device_id)
    return "Disabling user."


@api.route('/open_door', methods=['GET'])
def open_door():
    timestamp = request.args.get('timestamp', type=int)
    if timestamp is None:
        return Response("Time is required.\n", status=403)
    timestamp = int(timestamp)

    current_time = int(time.time())
    if abs(current_time - timestamp) > 10:
        return Response("Request expired.\n", status=403)

    device_type = request.args.get('type', type=str)
    if device_type is None:
        return Response("Device type is required.\n", status=403)
    device_type = str(device_type)

    signature = request.args.get('signature', type=str)
    if signature is None:
        return Response("Signature is required.\n", status=403)
    signature = str(signature)

    if device_type == "Arduino":
        key = unhexlify(config['DEFAULT']['arduino_aes_key'])
        IV = unhexlify(config['DEFAULT']['arduino_aes_iv'])
        decipher = AES.new(key,AES.MODE_CBC,IV)
        cipher_text = unhexlify(signature)
        plain_text = decipher.decrypt(cipher_text)
        calculated_hash = hashlib.sha256(str("open" + str(timestamp) + get_pre_shared_secret("Arduino")).encode()).hexdigest()
        if plain_text == calculated_hash:
            thread = Thread(target=drive_motor, args=[])
            thread.start()
            return "Door opening."
        else:
            return Response("Hash mismatches.\nShould be " + calculated_hash + ", but found " + plain_text, status=403)
    else:
        if device_type != "iOS" and device_type != "Android":
            # Device type not found.
            return Response("Device type not found.\n", status=403)
        device_id = request.args.get('device_id', type=str)
        if device_id is None:
            # Device id not found in parameters.
            return Response("Device id is required.\n", status=403)
        device_id = str(device_id)
        certificate = str(get_certificate(device_id))
        pre_shared_secret = str(get_pre_shared_secret(device_id))
        message = str(timestamp) + device_id + pre_shared_secret
        if verify_signature(message, signature, certificate):
            if get_enabled(device_id):
                thread = Thread(target=drive_motor, args=[])
                thread.start()
            else:
                return Response("User is disabled.\n", status=403)
            return "Door opening."
        else:
            return Response("Signature verification failed.\n", status=403)


def drive_motor():
    start_motor(1, 3.5, True)
    time.sleep(5)
    start_motor(1, 3.5, False)


def start_server_ssl():
    api.run(ssl_context=('/home/pi/fullchain.pem', '/home/pi/privkey.pem'), port=8443, host="::")


def start_server():
    api.run(port=8443, host="::")
