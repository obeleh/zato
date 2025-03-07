# -*- coding: utf-8 -*-

"""
Copyright (C) 2019, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing

# Python 2/3 compatibility
from six import add_metaclass

# Zato
from zato.common.broker_message import RBAC
from zato.common.odb.model import RBACClientRole, RBACRole
from zato.common.odb.query import rbac_client_role_list
from zato.server.service.internal import AdminService, AdminSIO
from zato.server.service.meta import CreateEditMeta, DeleteMeta, GetListMeta

elem = 'security_rbac_client_role'
model = RBACClientRole
label = 'an RBAC client role'
get_list_docs = 'RBAC client roles'
broker_message = RBAC
broker_message_prefix = 'CLIENT_ROLE_'
list_func = rbac_client_role_list
output_optional_extra = ['client_name', 'role_name']
create_edit_rewrite = ['id']
skip_input_params = ['name']
extra_delete_attrs = ['client_def', 'role_id']
check_existing_one = False

# ################################################################################################################################

def instance_hook(service, input, instance, attrs):

    if attrs.is_create_edit:
        with closing(service.odb.session()) as session:
            role = session.query(RBACRole).\
                filter(RBACRole.id==input.role_id).one()

        instance.name = '{}:::{}'.format(instance.client_def, role.name)

# ################################################################################################################################

def response_hook(service, input, instance, attrs, service_type):
    if service_type == 'get_list':
        for item in service.response.payload:
            with closing(service.odb.session()) as session:
                role = session.query(RBACRole).\
                    filter(RBACRole.id==item.role_id).one()
                item.client_name = item.client_def
                item.role_name = role.name

    elif service_type == 'create_edit':
        with closing(service.odb.session()) as session:
            role = session.query(RBACRole).\
                filter(RBACRole.id==instance.role_id).one()

        service.response.payload.client_name = instance.client_def
        service.response.payload.role_name = role.name

# ################################################################################################################################

@add_metaclass(GetListMeta)
class GetList(AdminService):
    _filter_by = RBACClientRole.name,

# ################################################################################################################################

@add_metaclass(CreateEditMeta)
class Create(AdminService):
    pass

# ################################################################################################################################

@add_metaclass(DeleteMeta)
class Delete(AdminService):
    pass

# ################################################################################################################################

class GetClientDefList(AdminService):
    """ Returns a list of client definitions - Zato's built-in security mechanisms as well as custom ones, as defined by users.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_security_rbac_client_role_get_client_def_list_request'
        response_elem = 'zato_security_rbac_client_role_get_client_def_list_response'
        input_required = ('cluster_id',)
        output_required = ('client_def', 'client_name')

    def get_data(self, session):

        out = []
        service = 'zato.security.get-list'
        request = {'cluster_id':self.request.input.cluster_id, 'needs_internal':False}

        for item in self.invoke(service, request, as_bunch=True)['zato_security_get_list_response']:
            client_name = '{}:::{}'.format(item.sec_type, item.name)
            out.append({'client_def':'sec_def:::{}'.format(client_name), 'client_name':client_name})

        # It's possible users defined their own security definitions outside of Zato
        # and they also need to be taken into account.

        custom_auth_list_service = self.server.fs_server_config.rbac.custom_auth_list_service
        if custom_auth_list_service:
            out.extend(self.invoke(custom_auth_list_service, {})['response']['items'])

        return out

    def handle(self):
        with closing(self.odb.session()) as session:
            self.response.payload[:] = self.get_data(session)

# ################################################################################################################################
