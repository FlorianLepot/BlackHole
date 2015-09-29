# -*- coding: utf-8 -*-
import logging
import os
import stat
from itertools import chain

from django.db import models
from django.conf import settings
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from django.core import exceptions
import paramiko

SELF_IDENTIFICATION = "self"
CONNECTION_TYPE_SSH = 'SSH'
CONNECTION_TYPE_DB = 'DB'

logger = logging.getLogger("blackhole.models")

def no_white_space_validator(value):
    if " " in value:
        raise ValidationError(u'White spaces not allowed')


class Environment(models.Model):
    name = models.CharField(max_length=15, unique=True, verbose_name=_(u"Name"))
    description = models.CharField(max_length=50, verbose_name=_(u"Description"))

    def __unicode__(self):
        return u"%s" % self.description

    class Meta(object):
        verbose_name = _("Environment")
        verbose_name_plural = _("Environments")
        ordering = ['name']


class Host(models.Model):
    CONNECTION_TYPE = CONNECTION_TYPE_SSH
    OS_CHOICES = (('LINUX', 'Linux'),
                  ('SOLARIS', 'Solaris'),
                  ('OSX', 'Mac OSX'))
    
    name = models.CharField(max_length=30, unique=True, verbose_name=_(u"Name"), validators=[no_white_space_validator])
    ip = models.IPAddressField(verbose_name=_(u"IP Address"), unique=True)
    port = models.PositiveIntegerField(max_length=5, default=22, verbose_name=_(u"Port"))
    os = models.CharField(max_length=10, choices=OS_CHOICES, default='LINUX', verbose_name=_(u"Operating System"))
    description = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u"Description"))
    environment = models.ForeignKey(Environment, verbose_name=_(u"Environment"))
    
    def __unicode__(self):
        return u"{0.name} ({0.ip}) - [{0.environment}]".format(self)
    
    class Meta(object):
        verbose_name = _(u"Host")
        verbose_name_plural = _(u"Hosts")
        ordering = ['name']


class Database(models.Model):
    CONNECTION_TYPE = CONNECTION_TYPE_DB
    ENGINE_MYSQL = u'MYSQL'
    ENGINE_ORACLE = u'ORACLE'
    ENGINE_POSTGRES = u'POSTGRES'
    ENGINE_CHOICES = ((ENGINE_ORACLE, u'Oracle'),
                      (ENGINE_MYSQL, u'MySQL'),
                      (ENGINE_POSTGRES, u'PostgreSQL'))
    name = models.CharField(max_length=30, verbose_name=_(u"Name"), validators=[no_white_space_validator])
    ip = models.IPAddressField(verbose_name=_(u"IP Address"))
    port = models.PositiveIntegerField(max_length=5, default=1521, verbose_name=_(u"Port"))
    engine = models.CharField(max_length=10, choices=ENGINE_CHOICES, default=ENGINE_MYSQL, verbose_name=_(u"Engine"))
    description = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u"Description"))
    environment = models.ForeignKey(Environment, verbose_name=_(u"Environment"))

    def __unicode__(self):
        return u"{0.name}/{0.description} ({0.ip}) - ({0.engine}) [{0.environment}]".format(self)

    class Meta(object):
        verbose_name = _(u"Database")
        verbose_name_plural = _(u"Databases")
        ordering = ['name']
        unique_together = (("name", "ip"),)

class UserIdentity(models.Model):    
    username = models.CharField(max_length=30, unique=True, verbose_name=_(u"User"))
   
    def __unicode__(self):
        return u"%s" % self.username

    class Meta(object):
        verbose_name = _(u"User Identity")
        verbose_name_plural = _(u"User Identities")
        ordering = ['username']


class PrivateKey(models.Model):
    TYPE_CHOICES = (
                    ('DSA', 'DSA Key'),
                    ('RSA', 'RSA Key'),
                    )
    user = models.CharField(max_length=20, verbose_name=_(u"User"))
    environment = models.ForeignKey(Environment, verbose_name=_(u"Environment"))
    key_type = models.CharField(max_length=3, choices=TYPE_CHOICES, verbose_name=_(u"Key Type"))
    private_key = models.TextField(verbose_name=_(u"Private Key"))
    public_key = models.TextField(verbose_name=_(u"Public Key"))
    
    def __unicode__(self):
        return u"%s [%s]" % (self.user, self.environment.name)
    
    def readlines(self):
        pk_to_string = str(self.private_key).replace('\r', '')
        return pk_to_string.split('\n')
    
    class Meta(object):
        unique_together = ('user', 'environment')
        verbose_name = _(u"Private Key")
        verbose_name_plural = _(u"Private Keys")
        ordering = ['user', 'environment']


class HostConnection(models.Model):
    AUTHENTICATION_METHOD_PRIVATE_KEY = 'PRIVATE_KEY'
    AUTHENTICATION_METHOD_PASSWORD = 'PASSWORD'
    AUTHENTICATION_METHODS_CHOICES = ((AUTHENTICATION_METHOD_PRIVATE_KEY, _(u'Private Key')),
                                      (AUTHENTICATION_METHOD_PASSWORD, _(u'Password')))
    host = models.ForeignKey(Host, verbose_name=_(u"Host"))
    authentication_method = models.CharField(max_length=15, default=AUTHENTICATION_METHOD_PRIVATE_KEY,
                                             choices=AUTHENTICATION_METHODS_CHOICES, verbose_name=_(u"Authentication Method"))
    authentication_user = models.ForeignKey(UserIdentity, verbose_name=_(u"Login As"))
    password = models.CharField(max_length=100, verbose_name=_(u'Password'), blank=True, null=True)

    def __unicode__(self):
        return u"%s as %s using %s" % (self.host, self.authentication_user, self.get_authentication_method_display())
    
    def get_connection_user(self, user):
        if self.authentication_user.username == SELF_IDENTIFICATION:
            return user.username
        else:
            return self.authentication_user.username

    def get_private_key(self, user):
        try:
            pk = PrivateKey.objects.get(user=user, environment=self.host.environment)
            try:

                if pk.key_type == 'DSA':
                    key = paramiko.DSSKey.from_private_key(pk)
                else:
                    key = paramiko.RSAKey.from_private_key(pk)
            except Exception as e:
                logger.error(u"Invalid Private Key for user {0} to host {1} <{2}>".format(user, self.host, e.message))
                raise Exception(u"Invalid Private Key")
            else:
                return key
        except exceptions.ObjectDoesNotExist as e:
            logger.error(u"Missing Private Key for user {0} to host {1}".format(user, self.host))
            raise Exception(u"Missing Private Key")

    class Meta(object):
        unique_together = ('host', 'authentication_user')
        verbose_name = _("Host Connection")
        verbose_name_plural = _("Host Connections")
        ordering = ['host', 'authentication_user']


class DBConnection(models.Model):
    host = models.ForeignKey(Database, verbose_name=_(u"Database"))
    authentication_user = models.ForeignKey(UserIdentity, verbose_name=_(u"Login As"))
    password = models.CharField(max_length=100, verbose_name=_(u'Password'), blank=True, null=True)

    def __unicode__(self):
        return u"%s as %s" % (self.host, self.authentication_user)

    def get_connection_user(self, user):
        if self.authentication_user.username == SELF_IDENTIFICATION:
            return user.username
        else:
            return self.authentication_user.username

    def get_client_command(self, user):
        if self.host.engine == Database.ENGINE_MYSQL:
            return u"{0} -u {1} -p{2} -D {3} -h {4} -P {5}".format(settings.MYSQL_CLIENT, self.get_connection_user(user), self.password, self.host.name, self.host.ip, self.host.port)
        elif self.host.engine == Database.ENGINE_ORACLE:
            return u"{0} {1}/{2}@//{3}:{4}/{5}".format(settings.ORACLE_CLIENT, self.get_connection_user(user), self.password, self.host.ip, self.host.port, self.host.name)
        elif self.host.engine == Database.ENGINE_POSTGRES:
            os.environ['PGPASSWORD'] = self.password
            return u"{0} -U {1} -h {2} -p {3} -d {4}".format(settings.POSTGRES_CLIENT, self.get_connection_user(user),
                                                                                        self.host.ip, self.host.port, self.host.name)
        else:
            return ""

    class Meta(object):
        unique_together = ('host', 'authentication_user')
        verbose_name = _("Database Connection")
        verbose_name_plural = _("Databases Connections")
        ordering = ['host', 'authentication_user']


class Profile(models.Model):
    name = models.CharField(max_length=15, unique=True, verbose_name=_(u"Name"))
    hosts = models.ManyToManyField(HostConnection, blank=True, verbose_name=_(u"Hosts"))
    databases = models.ManyToManyField(DBConnection, blank=True, verbose_name=_(u"Databases"))
    
    def get_environments(self):
        environment_list = []
        for environment in Environment.objects.all().order_by('name'):
            if len(self.hosts.filter(host__environment=environment)) > 0:
                environment_list.append(environment)
            if len(self.databases.filter(host__environment=environment)) > 0:
                if environment not in environment_list:
                    environment_list.append(environment)
        return environment_list

    def get_hostsConnections(self, environment):
        return list(chain(self.hosts.filter(host__environment=environment).order_by('host__name'), self.databases.filter(host__environment=environment).order_by('host__name')))

    def __unicode__(self):
        return u"%s" % self.name

    class Meta(object):
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
        ordering = ['name']


class AppUser(models.Model):
    username = models.CharField(max_length=20, unique=True, verbose_name=_(u"User"))
    first_name = models.CharField(max_length=50, verbose_name=_(u"Name"))
    last_name = models.CharField(max_length=50, verbose_name=_(u"Last Name"))
    description = models.CharField(max_length=20, blank=True, null=True, verbose_name=_(u"Description"))
    profile = models.ForeignKey(Profile, verbose_name=_(u"Profile"))
    enabled = models.BooleanField(default=True, verbose_name=_(u"Enabled"))
    time_range_enabled = models.BooleanField(default=False, verbose_name=_(u"Enabled in Time Range"))
    time_range_enabled_since = models.TimeField(default=(lambda: datetime.now().time().replace(second=0)), verbose_name=_(u"Since"))
    time_range_enabled_to = models.TimeField(default=(lambda: datetime.now().time().replace(second=0)), verbose_name=_(u"Until"))
    allowed_environments = models.ManyToManyField(Environment, blank=True, verbose_name=_(u"Enabled Environments"))

    def get_full_name(self):
        return u"%s, %s (%s)" % (self.last_name, self.first_name, self.username)
    
    def __unicode__(self):
        return u"%s, %s (%s)" % (self.last_name, self.first_name, self.username)

    class Meta(object):
        verbose_name = _(u"User")
        verbose_name_plural = _(u"Users")
        ordering = ['username']


class SessionLog(models.Model):
    session_id = models.CharField(verbose_name=_(u"Session UUID"), editable=False, max_length=40)
    session_type = models.CharField(max_length=30, verbose_name=_(u'Session Type'))
    user = models.ForeignKey('AppUser', verbose_name=_(u"User"), editable=False)
    host = models.CharField(max_length=50, verbose_name=_(u'Host'))
    user_identity = models.CharField(max_length=30, verbose_name=_(u"Identified As"), editable=False)
    source_ip = models.IPAddressField(verbose_name=_(u"Source IP"), editable=False)
    login_date = models.DateTimeField(verbose_name=_(u"Login date"), editable=False, auto_now_add=True)
    logout_date = models.DateTimeField(verbose_name=_(u"Logout date"), editable=False, null=True)
    session_duration = models.DecimalField(max_digits=10, decimal_places=3, verbose_name=_(u"Session Duration"), editable=False, null=True)
    log_file = models.CharField(max_length=250, verbose_name=_(u"Log File"), null=True, editable=False)
    
    def __unicode__(self):
        return u"%s[%s] a %s (%s)" % (self.user, self.user_identity, self.host, self.login_date)

    def save_duration(self):
        self.session_duration = str(round((self.logout_date - self.login_date).seconds / 60.0, 3))
        self.save()

    def get_log_filename(self, log_folder):
        session_date = self.login_date
        if not os.path.isdir(log_folder):
            logger.debug(u"Creating Logs Path %s" % log_folder)
            os.mkdir(log_folder)
            os.chmod(log_folder, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        filename_mask = "{0}_{1}_{2}_{3}_{4}.log".format(self.user.username, self.user_identity, self.host,
                                                         self.session_id, session_date.strftime("%Y%m%d_%H%M%S"))
        return os.path.join(log_folder, filename_mask)

    class Meta(object):
        verbose_name = _(u"Session Log")
        verbose_name_plural = _(u"Session Logs")
        ordering = ['login_date', 'user']
        permissions = (('view_session_logs', 'Can View Session Logs'),)
