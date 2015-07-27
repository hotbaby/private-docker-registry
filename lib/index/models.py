# -*- coding: utf-8 -*-

"""An SQLAlchemy backend for the search endpoint
"""

import re
import time
import logging
from datetime import datetime

from ... import storage
from ... import toolkit
from .   import Index
from .db import *
from docker_registry.core import compat

json = compat.json
DOMAIN_URL = 'http://192.168.1.9'
logger = logging.getLogger(__name__)

def retry(f):
    def _retry(self, *args, **kwargs):
        retry_times = 1
        i = 0
        while True:
            try:
                return f(self, *args, **kwargs)
            except Exception as e:
                if i < retry_times:
                    logger.warn("DB is disconnected. Reconnect to it.")
                    self.reconnect_db()
                    i += 1
                else:
                    raise e

    return _retry


class SQLAlchemyIndex (Index):
    """Maintain an index of repository data

    The index is a dictionary.  The keys are
    '{namespace}/{repository}' strings, and the values are description
    strings.  For example:

      index['library/ubuntu'] = 'An ubuntu image...'
    """
    def __init__(self, database=None):
        self.version = 1
        self._setup_database()
        super(SQLAlchemyIndex, self).__init__()

    def reconnect_db(self):
        pass

    @toolkit.exclusive_lock
    def _setup_database(self):
        logger.debug('storage: {0}'.format(storage.load()))

        record = Version.query.first()
        if record is None:
            version = None
        else:
            version = record.id;

        if version:
            if version != self.version:
                raise NotImplementedError(
                    'unrecognized search index version {0}'.format(version))
        else:
            self._generate_index()

    @retry
    def _generate_index(self):
        store = storage.load()
        version = Version(id=self.version)
        db.session.add(version)
        for repository in self._walk_storage(store=store):
            db.session.add(Repository(**repository))
        db.session.commit()

    @retry
    def _handle_repository_created(
            self, sender, namespace, repository, value):
        name = '{0}/{1}'.format(namespace, repository)
        description = ''  # TODO(wking): store descriptions

        repository = Repository(name=name, description=description)
        db.session.add(repository)
        db.session.commit()

    @retry
    def _handle_repository_updated(
            self, sender, namespace, repository, value):
        #name = '{0}/{1}'.format(namespace, repository)
        #description = ''  # TODO(wking): store descriptions

        #TODO flask.ext.sqlalchemy how to update record ?
        pass

    @retry
    def _handle_repository_deleted(self, sender, namespace, repository):
        name = '{0}/{1}'.format(namespace, repository)

        repository = Repository.query.filter(name=name).first()
        if repository is None:
            logger.warn('delete record {0} from repository is not exist.'.format(name))
        else:
            db.session.delete(repository)
            db.commit()

    @retry
    def results(self, search_term=None):
        repositories = None
        if search_term:
            field = getattr('Repository', 'name', None)
            repositories = Repository.query.filter(field.ilike(search_term))
            pass
        else:
            repositories = Repository.query.all()

        results = [
            {
                'name':  repository.name,
                'description': repository.description
            }
            for repository in repositories ]
        return results

class SQLAlchemyService (Index):
    """
    Maintain an index of services data
    """

    def __init__(self, database=None):
        self.version = 1
        self._setup_table()

    def reconnect_db(self):
        pass

    def _setup_table(self):
        #TODO how to judge whethe _walk_storage or not ?
        results = Service.query.all()
        if len(results) == 0:
            store = storage.load()
            pattern =re.compile(r'/')
            for repository in self._walk_storage(store=store):
                name = re.split(pattern, repository['name'])[1];
                db.session.add(Service(name=name, description=repository['description'], icon='', category='Application'))
        db.session.commit()

    def _handle_repository_created(self, sender, namespace, repository, value):
        #name = '{0}/{1}'.format(namespace, repository)
        service = Service(name=repository, description='', icon='', type='')
        db.session.add(service)
        db.commit()

    def _handle_repository_updated(self, sender, namespace, repository, value):
        #name = '{0}/{1}'.format(namespace, repository)
        #description = ''

        #TODO flask.ext.sqlalchemy how to update record ?
        pass
        

    def _handle_repository_deleted(self, sender, namespace, repository):
        name = '{0}/{1}'.format(namespace, repository)
        service = Service.query.filter_by(name=name).first()
        if service is None:
            logger.debug('Can not find the record {0} from service table.'.format(name))
            pass
        else:
            db.session.delete(service)
            db.session.commit()

    def results(self, search_term=None):
        services = None
        if search_term is None:
            services = Service.query.all()
        else:
            services = Service.query.filter(Service.category.like(search_term)) #TODO search services of the special type

        results = [
            {
                'name': service.name,
                'icon': service.icon,
            } for service in services ]
        return results

    def get_service(self, service_name):
        #name = '{0}/{1}'.format(namespace, service_name)
        #service = Service.query.filter_by(name=name).first()
        service = Service.query.filter(Service.name.like(service_name)).first()

        result =  {}
        if service is None:
            logger.debug('Can not find the record {0} from service table.'.format(service_name))
        else:
            timestamp = 0
            if service.publish_time != None:
                timestamp = int(time.mktime(service.publish_time.utctimetuple()))
            result = {
                'name': service.name,
                'icon': service.icon,
                'description': service.description,
                'registry': service.registry,
                #'category': service.category,
                'version': service.version,
                'publish_time': timestamp,
                'star_number': service.star_number,
                'download_number': service.download_number,
                'comment_url': service.comment_url,
                #'app_url': service.app_url,
                'compose_conf': DOMAIN_URL+service.compose_conf,
                'preview': json.loads(service.preview)
            }
        return result

    def add_service(self, data):
        service = None
        service = Service.query.filter_by(name=data['name']).first()
        if service != None:
            logger.warn('service {0} had existed.'.format(data['name']))
            return False

        service = Service(name = data['name'],
                          icon = data.get('icon', 'unkown'),
                          description = data.get('description', ''),
                          registry = data.get('registry', ''),
                          version = data.get('version', 'unkown'),
                          publish_time = data.get('publish_time', datetime.utcnow()),
                          star_number = data.get('star_number', 0),
                          download_number = data.get('download_number', 0),
                          compose_conf = data.get('compose_conf', 'unkown'),
                          preview = json.dumps(data.get('preview', []))
                         )
        db.session.add(service)
        db.session.commit()
        return True

    def delete_service(self, service_name):
        service = None
        service = Service.query.filter_by(name=service_name).first()
        if service is None:
            logger.debug('service {0} is not exist.'.format(service_name))
            return False
        else:
            db.session.delete(service)
            db.session.commit()
            return True

#TODO whethe inherit form Index ?
class SQLAlchemyRecommend():
    """
    Maintain an index of recommend services data.
    """

    def __init__(self):
        self._setup_table()
        pass

    def reconnect_db(self):
        pass

    def _setup_table(self):
        """
        Insert records into table for testing.
        """
        results = Recommend.query.all()
        if len(results) == 0:
            service = None
            service = Service.query.filter(Service.name=='dockerui').first()
            if service:
                db.session.add(Recommend(service=service, service_id=service.id, banner_img_url=''))
            service = None
            service = Service.query.filter(Service.name=='shipyard').first()
            if service:
                db.session.add(Recommend(service=service, service_id=service.id, banner_img_url=''))
            db.session.commit()
        else:
            pass
        pass

    def results(self):
        services = Service.query.filter(Recommend.service_id==Service.id)
        results = []
        if services is None:
            logger.debug('recommend table is empty.');
        else:
            for service in services:
                recommend = Recommend.query.filter_by(service_id=service.id).first()  #TODO Opetimizatoin

                timestamp = 0
                if service.publish_time != None:
                    timestamp = int(time.mktime(service.publish_time.utctimetuple()))
                obj = {
                    'banner_img_url':recommend.banner_img_url, 
                    'name': service.name,
                    'registry': service.registry,
                    'icon': service.icon,
                    'description': service.description,
                    'version': service.version,
                    'publish_time': timestamp,
                    'star_number': service.star_number,
                    'download_number': service.download_number,
                    'comment_url': service.comment_url,
                    'compose_conf': DOMAIN_URL+service.compose_conf,
                    'preview': json.loads(service.preview)
                    #'app_url': service.app_url,
                }
                results.append(obj)
        return results

class SQLAlchemyCategory():
    """
    Maintain an index of services category data. 
    """

    def __init__(self):
        self._setup_table()
        pass

    def reconnect_db(self):
        pass

    def _setup_table(self):
        """
        Insert a record into table for testing.
        """
        results = Category.query.all()
        if len(results) == 0:
            db.session.add(Category(name='Database'))
            db.session.add(Category(name='WebServer'))
            db.session.add(Category(name='OperatingSystem'))
            db.session.add(Category(name='Applicaton'))
            db.session.commit()
        else:
            pass
        pass

    def results(self):
        categories = Category.query.all()
        results = []

        if categories is None:
            logger.debug('Category table is empty.')
        else:
            for category in categories:
                results.append(category.name)
        return results

