#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
from ...app import app
from flask.ext.sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/docker-registry.db'
db = SQLAlchemy(app)

class Version(db.Model):
    "Schema version for the search-index database"
    __tablename__ = 'version'

    id = db.Column(db.Integer, primary_key=True)

    def __init__(self, *args, **kwargs):
        super(Version, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '<{0}(id={1})>'.format(type(self).__name__, self.id)

class Repository (db.Model):
    "Repository description for the search-index database"
    __tablename__ = 'repository'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(128))

    def __init__(self, *args, **kwargs):
        super(Repository, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<{0}(name='{1}', description='{2}', icon='{3}')>".format(
            type(self).__name__, self.name, self.description, self.icon)

class Service (db.Model):
    "Service description for the search-index database"
    __tablename__ = 'service'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(512), default='')
    registry=db.Column(db.String(128), default='')
    icon = db.Column(db.String(128), default='unkown')
    category = db.Column(db.String(128), default='unkown')
    version = db.Column(db.String(32), default='unkown')
    publish_time = db.Column(db.DateTime, default=datetime.utcnow)
    star_number = db.Column(db.Integer, default=0)
    download_number = db.Column(db.Integer, default=0)
    comment_url = db.Column(db.String(128), default='unkown')
    app_url = db.Column(db.String(128), default='unkown')
    compose_conf = db.Column(db.String(128), default='unkown')
    preview = db.Column(db.Text, default='[]')

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<{0}(name='{1}', description='{2}', icon='{3}', category='{4}', \
                    version='{5}', publish_time='{6}')>".format(
                    type(self).__name__, self.name, self.description, 
                    self.icon, self.category, self.version, self.publish_time)
                    #TODO not print preview.


class Recommend (db.Model):
    "Recommend description for the search-index database"
    __tablename__ = 'recommend'

    id = db.Column(db.Integer, primary_key=True)
    banner_img_url = db.Column(db.String(128), default='unkown')
    service_id = db.Column(db.Integer, db.ForeignKey(Service.id), nullable=False)
    service = db.relationship(Service, innerjoin=True, lazy="joined")

    def __init__(self, *args, **kwargs):
        super(Recommend, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<{0}(service_id='{1}', banner_img_url='{2}')>" \
                .format(type(self).__name__, self.service_id, self.banner_img_url)

class Category(db.Model):
    "Type description for the search-index database"
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    def __init__(self, *args, **kwargs):
        super(Category, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<{0}(name='{1}')>".format(type(self).__name__, self.name)

