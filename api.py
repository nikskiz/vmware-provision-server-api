#! /usr/bin/python2.7
from flask import Flask, jsonify, abort, make_response, request
import CloneSpecs_Class
import VMClone
import Logger
app = Flask(__name__)

@app.route('/api/v1.0/clone', methods=['POST'])
def clone():
    # Define a blank list
    specs = []

    # Define variables based on the POST
    vps_name = request.json['vps_name'],
    vps_product = request.json['vps_product'],
    folder = request.json['folder'],
    #ncpu =  request.json['ncpu'],
    #npsocket = request.json['npsocket'],
    #mem = request.json['mem'],
    #chotadd = request.json['chotadd'],
    #mhotadd = request.json['mhotadd'],
    template_vm_uid =  request.json['template_vm_uid'],
    #greencode =  request.json['greencode'],
    #console_os_id = request.json['console_os_id'],

    # Append the variables to the list
    Logger.logging.debug('Importing the specs')
    try:
        specs.append(CloneSpecs_Class.CloneSpecs(vps_name, vps_product, folder, template_vm_uid))
    except:
        return jsonify("Error Occured Failed to provision VPS")

    for spec in specs:
        # Run the main function in VMClone.py which clones
        return jsonify({"UID":VMClone.main(spec.vps_name, spec.vps_product, spec.folder, spec.template_vm_uid)})

def debug(specs):
    # Return the all the objects in the CloneSpecs_Class class
    for spec in specs:
        return jsonify({"specs":spec.printSpecs()}), 200

@app.errorhandler(404)
def not_found(error):
    # If 404 is return reply with 404
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    # Listn on all IP's which this app is running on, port 8080 is used
    app.run(host='0.0.0.0', port=8080)
