import mysql.connector
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
username = config['DEFAULT']['database_username']
password = config['DEFAULT']['database_password']
database_name = config['DEFAULT']['database_name']

cnx = mysql.connector.connect(user=username, password=password,
                              host='127.0.0.1',
                              database=database_name)


def database_add_user(type, device_id, pre_shared_secret, certificate):
    query = ("INSERT INTO `users` "
                 "(type, device_id, pre_shared_secret, certificate) "
                 "VALUES (%s, %s, %s, %s)")
    data = (type, device_id, pre_shared_secret, certificate)
    cnx.cursor().execute(query, data)
    cnx.commit()


def database_remove_user(device_id):
    query = str("DELETE FROM `users` "
                 "WHERE `device_id` = '%s'" % str(device_id))
    cnx.cursor().execute(query)
    cnx.commit()


def database_enable_user(device_id):
    # UPDATE `users` SET `enabled` = '1' WHERE `users`.`id` = 1
    query = str("UPDATE `users` "
                 "SET `enabled` = 1"
                 "WHERE `device_id` = '%s'" % str(device_id))
    cnx.cursor().execute(query)
    cnx.commit()


def database_disable_user(device_id):
    # UPDATE `users` SET `enabled` = '1' WHERE `users`.`id` = 1
    query = str("UPDATE `users` "
                 "SET `enabled` = 0"
                 "WHERE `device_id` = '%s'" % str(device_id))
    cnx.cursor().execute(query)
    cnx.commit()


def try_user_data(device_id):
    cursor = cnx.cursor()
    query = str("SELECT `type`, `device_id`, `pre_shared_secret`, `enabled`, `certificate` FROM `users` "
             "WHERE `device_id` = '%s'" % str(device_id))
    cursor.execute(query)
    dataset = cursor.fetchall()
    return dataset


def get_user_data(device_id):
    user_data = try_user_data(device_id)[0]
    return user_data


def is_user_valid(device_id):
    result = try_user_data(device_id)
    if len(result) == 1:
        return True
    return False


def get_device_type(device_id):
    if not is_user_valid(device_id):
        return ""
    return get_user_data(device_id)[0]


def get_pre_shared_secret(device_id):
    if not is_user_valid(device_id):
        return ""
    return get_user_data(device_id)[2]


def get_enabled(device_id):
    if not is_user_valid(device_id):
        return False
    value = get_user_data(device_id)[3]
    if value == 1:
        return True
    return False


def get_certificate(device_id):
    if not is_user_valid(device_id):
        return ""
    return get_user_data(device_id)[4]


# def get_e(device_id):
#     if not is_user_valid(device_id):
#         return ""
#     return get_user_data(device_id)[4]
#
#
# def get_n(device_id):
#     if not is_user_valid(device_id):
#         return ""
#     return get_user_data(device_id)[5]


