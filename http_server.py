import hashlib, urllib
from binascii import unhexlify
from threading import Thread

from Crypto.Cipher import AES
from flask import Flask, request, Response
from werkzeug.urls import iri_to_uri

from crypto import *
from database import *
from motor_control import *


api = Flask(__name__)


# @api.route('/forward', methods=['GET'])
def forward_move():
    rev_per_second = float(request.args.get('rev', type=float))
    run_time = float(request.args.get('time', type=float))
    thread = Thread(target=move_motor, args=[rev_per_second, run_time, False])
    thread.start()
    return "Forward moving."


# @api.route('/reverse', methods=['GET'])
def reverse_move():
    rev_per_second = float(request.args.get('rev', type=float))
    run_time = float(request.args.get('time', type=float))
    thread = Thread(target=move_motor, args=[rev_per_second, run_time, True])
    thread.start()
    return "Reverse moving."


def move_motor(rev_per_second, run_time, reverse):
    rev_per_second = float(rev_per_second)
    run_time = float(run_time)
    reverse = bool(reverse)
    if rev_per_second < 0:
        return "rev must be greater than 0."
    if rev_per_second > 2:
        return "Too fast!"
    if run_time < 0:
        return "run_time must be greater than 0."
    if run_time > 10:
        return "Too long!"
    enable_motor()
    start_motor(rev_per_second, run_time, reverse)
    cleanup_pins()
    disable_motor()


@api.route('/register_user', methods=['GET'])
def register_user():
    system_time = round(time.time() * 1000)
    remote_ip = request.remote_addr
    raw_request = iri_to_uri(request.url)

    device_type = request.args.get('type', type=str)
    device_id = request.args.get('device_id', type=str)

    log_operation(system_time, remote_ip, raw_request, None, device_type, device_id, 'register_user')

    pre_shared_secret = request.args.get('pre_shared_secret', type=str)
    certificate = urllib.request.unquote(request.args.get('certificate', type=str))

    if device_type is None:
        return Response("Device type is required.", status=403)
    device_type = str(device_type)

    if device_id is None:
        return Response("Device ID is required.", status=403)
    device_id = str(device_id)

    if pre_shared_secret is None:
        return Response("Pre shared secret is required.", status=403)
    pre_shared_secret = str(pre_shared_secret)

    if certificate is None:
        return Response("Certificate is required.", status=403)
    certificate = str(certificate)

    if verify_client_certificate(certificate):
        database_add_user(device_type, device_id, pre_shared_secret, certificate)
        mark_operation_as_succeeded(system_time)
        return "Device registered."
        # return Response("{'status':'0', 'msg':'User added.'}", status=200, mimetype='application/json')
    else:
        return Response("Certificate is not valid.", status=403)
        # return Response("{'status':'-1', 'msg':'Information is invalid.'}", status=403, mimetype='application/json')


# @api.route('/enable_user', methods=['GET'])
def enable_user():
    device_id = str(request.args.get('device_id', type=str))
    database_enable_user(device_id)
    return "Enabling user."


# @api.route('/disable_user', methods=['GET'])
def disable_user():
    device_id = str(request.args.get('device_id', type=str))
    database_disable_user(device_id)
    return "Disabling user."


@api.route('/open_door', methods=['GET'])
def open_door():
    system_time = round(time.time() * 1000)
    remote_ip = request.remote_addr
    raw_request = iri_to_uri(request.url)

    timestamp = request.args.get('timestamp', type=int)
    device_type = request.args.get('type', type=str)
    signature = request.args.get('signature', type=str)
    device_id = request.args.get('device_id', type=str)

    log_operation(system_time, remote_ip, raw_request, timestamp, device_type, device_id, 'open_door')

    if timestamp is None:
        print("Time is required.")
        return Response("Time is required.", status=403)
    timestamp = int(timestamp)

    if device_type is None:
        print("Device type is required.")
        return Response("Device type is required.", status=403)
    device_type = str(device_type)

    if signature is None:
        print("Signature is required.")
        return Response("Signature is required.", status=403)
    signature = str(signature)

    if device_type == "Arduino":
        if abs(system_time - timestamp * 1000) > 5000:
            print("Request expired.")
            return Response("Request expired.", status=403)

        try:
            signature_test = unhexlify(signature)
        except:
            print("Signature is not a valid hexadecimal string.")
            return Response("Signature is not a valid hexadecimal string.", status=403)

        calculated_hash = hashlib.sha256(
            str("Open" + str(timestamp) + get_pre_shared_secret("Arduino")).encode()).hexdigest()
        if signature == calculated_hash:
            thread = Thread(target=drive_motor, args=[])
            thread.start()
            mark_operation_as_succeeded(system_time)
            return "Door opening."
        else:
            print("Hash mismatches.\nShould be " + calculated_hash + ", but found " + signature + ".")
            return Response("Hash mismatches.\nShould be " + calculated_hash + ", but found " + signature + ".",
                            status=403)
    else:
        if abs(system_time - timestamp) > 5000:
            return Response("Request expired.", status=403)

        if device_type != "iOS" and device_type != "Android":
            # Device type not found.
            return Response("Device type not found.", status=403)
        if device_id is None:
            # Device id not found in parameters.
            return Response("Device id is required.", status=403)
        device_id = str(device_id)
        if not is_user_valid(device_id):
            return Response("Device not found.", status=403)
        certificate = str(get_certificate(device_id))
        certificate_x509 = load_certificate(FILETYPE_PEM, certificate.encode())
        common_name = str(certificate_x509.get_subject().CN)
        if common_name != device_id:
            return Response("Common name mismatches.", status=403)
        pre_shared_secret = str(get_pre_shared_secret(device_id))
        message = "Open" + str(timestamp) + device_id + pre_shared_secret
        # print(message)
        signature = unhexlify(signature)
        if verify_signature(message, signature, certificate):
            if get_enabled(device_id):
                mark_operation_as_succeeded(system_time)
                thread = Thread(target=drive_motor, args=[])
                thread.start()
                return "Door opening."
            else:
                return Response("User is disabled.", status=403)
        else:
            return Response("Signature verification failed.", status=403)


@api.route('/deactivate_device', methods=['GET'])
def deactivate_device():
    system_time = round(time.time() * 1000)
    remote_ip = request.remote_addr
    raw_request = iri_to_uri(request.url)

    timestamp = request.args.get('timestamp', type=int)
    device_type = request.args.get('type', type=str)
    signature = request.args.get('signature', type=str)
    device_id = request.args.get('device_id', type=str)

    log_operation(system_time, remote_ip, raw_request, timestamp, device_type, device_id, 'deactivate_device')

    if timestamp is None:
        return Response("Time is required.", status=403)
    timestamp = int(timestamp)

    if abs(system_time - timestamp) > 5000:
        return Response("Request expired.", status=403)

    if device_type is None:
        return Response("Device type is required.", status=403)
    device_type = str(device_type)

    if signature is None:
        return Response("Signature is required.", status=403)
    signature = str(signature)

    if device_type != "iOS" and device_type != "Android":
        # Device type not found.
        return Response("Device type not found.", status=403)

    if device_id is None:
        # Device id not found in parameters.
        return Response("Device id is required.", status=403)
    device_id = str(device_id)
    if not is_user_valid(device_id):
        return Response("Device not found.", status=403)

    certificate = str(get_certificate(device_id))
    certificate_x509 = load_certificate(FILETYPE_PEM, certificate.encode())
    common_name = str(certificate_x509.get_subject().CN)
    if common_name != device_id:
        return Response("Common name mismatches.", status=403)
    pre_shared_secret = str(get_pre_shared_secret(device_id))
    message = "Deactivate" + str(timestamp) + device_id + pre_shared_secret
    # print(message)
    signature = unhexlify(signature)
    if verify_signature(message, signature, certificate):
        database_remove_user(device_id)
        mark_operation_as_succeeded(system_time)
        return "Device deactivated."
    else:
        return Response("Signature verification failed.", status=403)


def drive_motor():
    start_motor(1, 3.5, True)
    time.sleep(5)
    start_motor(1, 3.5, False)


def start_server_ssl():
    api.run(ssl_context=('/home/pi/fullchain.pem', '/home/pi/privkey.pem'), port=8443, host="::")


def start_server():
    api.run(port=8443, host="::")
