# -*- coding: utf-8 -*-

"""
Copyright (C) 2018, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import base64
import os
import logging
from json import loads

# Bunch
from bunch import bunchify

# configobj
from configobj import ConfigObj

# cryptography
from cryptography.fernet import Fernet

# ################################################################################################################################

logger = logging.getLogger(__name__)

# ################################################################################################################################

well_known_data = b'3.141592...' # π number

# ################################################################################################################################

class CryptoManager(object):
    """ Used for encryption and decryption of secrets.
    """
    def __init__(self):
        self.secret_key = None
        self.well_known_data = None

# ################################################################################################################################

    def set_config(self, secret_key, well_known_data):
        self.secret_key = Fernet(secret_key.encode('utf8'))
        self.well_known_data = well_known_data.encode('utf8') if well_known_data else None

        if self.well_known_data:
            self.check_consistency()

# ################################################################################################################################

    @staticmethod
    def generate_key():
        return Fernet.generate_key()

# ################################################################################################################################

    @staticmethod
    def generate_password(bits=128):
        return base64.urlsafe_b64encode(os.urandom(int(bits / 8)))

# ################################################################################################################################

    @classmethod
    def from_repo_dir(cls, repo_dir):
        return cls(repo_dir=repo_dir)

# ################################################################################################################################

    @classmethod
    def from_secret_key(cls, secret_key, well_known_data=None):
        return cls(secret_key=secret_key, well_known_data=well_known_data)

# ################################################################################################################################

    def check_consistency(self):
        """ Used as a consistency check to confirm that a given component's key can decrypt well-known data.
        """
        decrypted = self.decrypt(self.well_known_data)
        if decrypted != well_known_data:
            raise ValueError('Expected for value `{}` to decrypt to `{}`'.format(encrypted, well_known_data))

# ################################################################################################################################

    def encrypt(self, data):
        return self.secret_key.encrypt(data)

# ################################################################################################################################

    def decrypt(self, encrypted):
        return self.secret_key.decrypt(encrypted.encode('utf8'))

# ################################################################################################################################

    def get_config_entry(self, entry):
        raise NotImplementedError('May be implemented by subclasses')

# ################################################################################################################################

class WebAdminCryptoManager(CryptoManager):
    """ CryptoManager for web-admin instances.
    """
    def __init__(self, repo_dir=None, secret_key=None, well_known_data=None):
        if repo_dir:
            conf_path = os.path.join(repo_dir, 'web-admin.conf')
            conf = bunchify(loads(open(conf_path).read()))
            secret_key = conf['zato_secret_key']
            well_known_data = conf['well_known_data']

        self.set_config(secret_key, well_known_data)

# ################################################################################################################################

class SchedulerCryptoManager(CryptoManager):
    """ CryptoManager for schedulers.
    """
    def __init__(self, repo_dir=None, secret_key=None, well_known_data=None):
        if repo_dir:
            conf_path = os.path.join(repo_dir, 'web-admin.conf')
            conf = bunchify(loads(open(conf_path).read()))
            secret_key = conf['zato_secret_key']
            well_known_data = conf['well_known_data']

        self.set_config(secret_key, well_known_data)

# ################################################################################################################################
