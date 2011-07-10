from flask import request, render_template, redirect, url_for

from datahub.core import app
from datahub import logic
from datahub.exc import Gone
from datahub.util import request_content, jsonify

@app.route('/api/v1/resource/<owner>', methods=['GET'])
def resource_index(owner):
    """ List all the resources of a particular user. """
    result = logic.resource.list_by_owner(owner)
    return jsonify(list(result))

@app.route('/api/v1/resource/<owner>', methods=['POST'])
def resource_create(owner):
    """ Create a new resource for the given user. """
    data = request_content(request)
    resource = logic.resource.create(owner, data)
    return redirect(url_for('resource_get', owner=owner, 
                            resource=resource.name))

@app.route('/api/v1/resource/<owner>/<resource>', methods=['GET'])
def resource_get(owner, resource):
    """ Get a JSON representation of the resource. """
    resource = logic.resource.find(owner, resource)
    return jsonify(resource)

@app.route('/api/v1/resource/<owner>/<resource>', methods=['PUT'])
def resource_update(owner, resource):
    """ Update the data of the resource. """
    data = request_content(request)
    resource = logic.resource.update(owner, resource, data)
    return jsonify(resource)

@app.route('/api/v1/resource/<owner>/<resource>', methods=['DELETE'])
def resource_delete(owner, resource):
    """ Delete the resource. """
    logic.resource.delete(owner, resource)
    raise Gone('Successfully deleted: %s / %s' % (owner, resource))

@app.route('/')
def home():
    return render_template('home.tmpl')
