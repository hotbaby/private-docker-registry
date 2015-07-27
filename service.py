# -*- coding: utf-8 -*-

import flask
import logging
from . import toolkit
from .app import app
from .lib import config
from .lib import index
from .lib import mirroring

from docker_registry.core import compat
from docker_registry.core import exceptions

json = compat.json
logger = logging.getLogger(__name__)
cfg = config.load()

# Enable the search index
logger.debug('search_backend: {0}'.format(cfg.search_backend.lower()))

CATEGORY = index.load_category()
SERVICE = index.load_service()
RECOMMEND = index.load_recommend()

@app.route('/v1/services', methods=['GET'])
@mirroring.source_lookup(index_route=True, merge_results=True)
def get_searvices():
    search_term = flask.request.args.get('q', None)
    logger.debug('search_term: {0}'.format(search_term))
    results = SERVICE.results(search_term=search_term)
    return toolkit.response(results)

    """
    return toolkit.response({
        'number_results': len(results),
        'results': results
    })
    """


@app.route('/v1/services/category', methods=['GET'])
def get_services_type():
    results = CATEGORY.results()
    return toolkit.response(results)

@app.route('/v1/services/category', methods=['PUT'])
def post_services_type():
    pass

@app.route('/v1/services/category', methods=['DELETE'])
def delete_service_type():
    pass


@app.route('/v1/services/gallery', methods=['GET'])
@mirroring.source_lookup(index_route=True, merge_results=True)
def get_services_recommend():
    results = RECOMMEND.results()
    return toolkit.response(results)

    """
    return toolkit.response({
        'number_results': len(results),
        'recommend': results
    })
    """


@app.route('/v1/services/<service_id>', methods=['GET'])
@mirroring.source_lookup(index_route=True, merge_results=True)
def get_service_info(service_id):
    result =SERVICE.get_service(service_name=service_id)
    return toolkit.response(result)
    """
    return toolkit.response({
        'result': result 
    })
    """

@app.route('/v1/services/<service_id>', methods=['PUT'])
def post_service_info(service_id):
    data = None
    try:
        data = json.loads(flask.request.data.decode('utf8'))
    except ValueError:
        pass
    if not data:
        return toolkit.api_error('Invalid data')

    result = SERVICE.add_service(data)
    return toolkit.response(result)

@app.route('/v1/services/<service_id>', methods=['DELETE'])
def delete_sevice_info(service_id):
    result = SERVICE.delete_service(service_id)
    return toolkit.response(result)

@app.route('/v1/service/<namespace>/<service_id>/comments', methods=['GET', 'PUT'])
def get_service_comments():
    pass

