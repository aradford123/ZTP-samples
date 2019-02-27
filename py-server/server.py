#!/usr/bin/env python
from __future__ import print_function
import csv
from flask import Flask
from flask import request, jsonify, make_response
app = Flask(__name__)
FILE ="serial-ip.csv"



@app.route('/device', methods=["GET"])
def get_all():
    #print (request.args)
    #print("Method {}".format(request.method))
    if request.method == "GET":

        # this is a list
        serials = request.args.getlist('serial')
        print("serial:{}".format(serials))

        if serials == []:
            return jsonify({"error:" : "No serial provided as query param (?serial=aaa)"}), 404
        for serial in serials:
            try:
                result = db[serial]
                print(result)
                return jsonify(result), 200
            except KeyError:
                pass

        return jsonify({"Error": "Cannot find serial:{}".format(serial)}), 404





if __name__ == '__main__':
    global db
    db = {}
    with open(FILE,"r")as f:
        try:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                db[row['serial']] = row
        except ValueError as e:
            pass

    app.run(host="0.0.0.0", port="1880")
