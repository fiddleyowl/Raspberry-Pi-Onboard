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
    cnx.commit()
    return dataset


def get_user_data(device_id):
    all_data = try_user_data(device_id)
    user_data = all_data[len(all_data)-1]
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


def log_operation(system_time, remote_ip, raw_request, query_time, type, device_id, operation):
    sql_query = ("INSERT INTO `log` "
             "(system_time, remote_ip, raw_request, query_time, type, device_id, operation, result) "
             "VALUES (UNIX_TIMESTAMP(%s), %s, %s, UNIX_TIMESTAMP(%s), %s, %s, %s, %s)")
    data = (system_time, remote_ip, raw_request, query_time, type, device_id, operation, 0)
    cnx.cursor().execute(sql_query, data)
    cnx.commit()


def mark_operation_as_succeeded(system_time):
    sql_query = ("UPDATE `log` "
                 "SET `result` = 1 "
                 "WHERE `system_time` = '%s'" % system_time)
    cnx.cursor().execute(sql_query)
    cnx.commit()