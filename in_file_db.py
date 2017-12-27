#!flask/bin/python
from flask import Flask, jsonify, request, abort, make_response, g
from werkzeug.contrib.cache import SimpleCache

import json

app = Flask(__name__)
cache = SimpleCache()
blocked = 'blocked'
timeout_time = 5 * 60


class Transactions:
    # rest API, static tx class(singleton-like)
    # python3
    # work in progress:

    PATH_TO_DB = "c:/data/test.txt"

    @staticmethod
    def write_db(content):
        content = json.dumps(content)
        try:
            with open(Transactions.PATH_TO_DB, "w+") as data_file:
                data_file.write(content)
        except:
            print("Unexpected error")
            data_file.close()
            return False

        data_file.close()
        return True

    @staticmethod
    def read_db():
        try:
            with open(Transactions.PATH_TO_DB) as data_file:
                data = json.load(data_file)
        except ValueError:
            data_file.close()
            return {}
        except IOError:
            with open(Transactions.PATH_TO_DB, 'w') as data_file:
                data_file.close()
            return {}
        data_file.close()
        return data

    @staticmethod
    def create(db, key, value=None, push=False):
        if key:
            db[key] = value
            if push:
                return Transactions.write_db(db)
            return True
        return False

    @staticmethod
    def read(db, key):
        try:
            return db[key]
        except:
            return None

    @staticmethod
    def update(db, key, value, push):
        Transactions.create(db, key, value, push)

    @staticmethod
    def delete(db, key, push):
        try:
            del db[key]
        except:
            return False
        if push:
            return Transactions.write_db(db)
        return True


@app.after_request
def unlock_db(response):
    cache.set(blocked, False, timeout=timeout_time)
    return response


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/db/api/v1.0/<key>', methods=['GET'])
def get_value(key):
    if cache.get(blocked):
        return jsonify({"success": False, "db_blocked": True}), 409
    cache.set(blocked, True, timeout=timeout_time)

    db = Transactions.read_db()
    return jsonify({key: Transactions.read(db, key)}), 200


@app.route('/db/api/v1.0/<key>', methods=['DELETE'])
def delete_value(key):
    if cache.get(blocked):
        return jsonify({"success": False, "db_blocked": True}), 409
    cache.set(blocked, True, timeout=timeout_time)

    db = Transactions.read_db()
    return jsonify({"success": Transactions.delete(db, key, True)}), 200


@app.route('/db/api/v1.0', methods=['POST'])
def create_entry():
    if cache.get(blocked):
        return jsonify({"success": False, "db_blocked": True}), 409
    cache.set(blocked, True, timeout=timeout_time)

    if not request.json or not 'key' in request.json or not 'value' in request.json:
        abort(400)

    entry = {
        'key': request.json['key'],
        'value': request.json.get('value', "")
    }

    db = Transactions.read_db()
    return jsonify({"success": Transactions.create(db, entry['key'], entry['value'], True)}), 201


@app.route('/db/api/v1.0', methods=['PATCH'])
def update_entry():
    if cache.get(blocked):
        return jsonify({"success": False, "db_blocked": True}), 409
    cache.set(blocked, True, timeout=timeout_time)

    if not request.json or not 'key' in request.json or not 'value' in request.json:
        abort(400)

    entry = {
        'key': request.json['key'],
        'value': request.json.get('value', "")
    }

    db = Transactions.read_db()
    return jsonify({"success": Transactions.update(db, entry['key'], entry['value'], True)}), 200


if __name__ == '__main__':
    app.run(debug=True)
