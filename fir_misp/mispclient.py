# This file is licensed under AGPL-3 or later.
# It includes code derived from TheHive Cortex-Analyzers project (https://github.com/TheHive-Project/Cortex-Analyzers/blob/master/analyzers/MISP/mispclient.py)
# which is licensed under the GNU Affero General Public License (AGPL 3.0)
# Original copyright : TheHive Project (and contributors)


import pymisp
import os

import logging

class MISPClientError(Exception):
    """Basic Error class"""
    pass


class EmptySearchtermError(MISPClientError):
    """Exception raised, when no search terms are given."""
    pass


class CertificateNotFoundError(MISPClientError):
    """Raised if certificate file could not be found"""
    pass


class MISPClient:
    """The MISPClient class just hides the "complexity" of the queries. All params can be lists to query more than one
    MISP instance.

    :param url: URL of MISP instance
    :type url: [str, list]
    :param key: API key
    :type key: [str, list]
    :param ssl: Use/dont' use ssl or path to ssl cert if not possible to verify through trusted CAs
    :type ssl: [bool, list, str]
    :param name: Name of the MISP instance, is sent back in the report for matching the results.
    :type name: [str, list]
    :param proxies: Proxy to use for pymisp instances
    :type proxies: dict
    """

    def __init__(self, url, key, ssl=True, name='Unnamed', proxies=None):
        self.misp_connections = []
        if type(url) is list:
            for idx, server in enumerate(url):
                verify = True

                # Given ssl parameter is a list
                if isinstance(ssl, list):
                    if isinstance(ssl[idx], str) and os.path.isfile(ssl[idx]):
                        verify = ssl[idx]
                    elif isinstance(ssl[idx], str) and not os.path.isfile(ssl[idx]) and ssl[idx] != "":
                        raise CertificateNotFoundError('Certificate not found under {}.'.format(ssl[idx]))
                    elif isinstance(ssl[idx], bool):
                        verify = ssl[idx]

                # Do the same checks again, for the non-list type
                elif isinstance(ssl, str) and os.path.isfile(ssl):
                    verify = ssl
                elif isinstance(ssl, str) and not os.path.isfile(ssl) and ssl != "":
                    raise CertificateNotFoundError('Certificate not found under {}.'.format(ssl))
                elif isinstance(ssl, bool):
                    verify = ssl
                self.misp_connections.append(pymisp.ExpandedPyMISP(url=server,
                                                                   key=key[idx],
                                                                   ssl=verify,
                                                                   proxies=proxies))
        else:
            verify = True
            if isinstance(ssl, str) and os.path.isfile(ssl):
                verify = ssl
            elif isinstance(ssl, str) and not os.path.isfile(ssl) and ssl != "":
                raise CertificateNotFoundError('Certificate not found under {}.'.format(ssl))
            elif isinstance(ssl, bool):
                verify = ssl
            self.misp_connections.append(pymisp.ExpandedPyMISP(url=url,
                                                               key=key,
                                                               ssl=verify,
                                                               proxies=proxies))
        self.misp_name = name

    def __clean_relatedevent(self, related_events):
        """
        Strip relatedevent sub content of event for lighter output.
        
        :param related_events: 
        :return: 
        """

        response = []
        for event in related_events:
            ev = {
                'info': event['Event']['info'],
                'id': event['Event']['id']
            }
            response.append(ev)

        return response

    def __clean_event(self, misp_event):
        """
        Strip event data for lighter output. Analyer report only contains useful data.
        
        :param event: misp event
        :return: misp event
        """

        filters = ['Attribute',
                   'Object',
                   'ShadowAttribute',
                   'Org',
                   'ShadowAttribute',
                   'SharingGroup',
                   'sharing_group_id',
                   'disable_correlation',
                   'locked',
                   'publish_timestamp',
                   'attribute_count',
                   'attribute_count',
                   'analysis',
                   'published',
                   'distribution',
                   'proposal_email_lock']

        for filter in filters:
            if filter in misp_event:
                del misp_event[filter]

        if 'RelatedEvent' in misp_event:
            misp_event['RelatedEvent'] = self.__clean_relatedevent(misp_event['RelatedEvent'])

        return misp_event

    def __clean(self, misp_response):
        """
        
        :param misp_response: 
        :return: 
        """
        response = []

        for event in misp_response:
            response.append(self.__clean_event(event['Event']))

        return response

    def __search(self, value, type_attribute):
        """Search method call wrapper.

        :param value: value to search for.
        :type value: str
        :param type_attribute: attribute types to search for.
        :type type_attribute: [list, none]
        """
        results = []
        if not value:
            raise EmptySearchtermError
        for idx, connection in enumerate(self.misp_connections):
            misp_response = connection.search(type_attribute=type_attribute, value=value)

            if isinstance(self.misp_name, list):
                name = self.misp_name[idx]
            else:
                name = self.misp_name

            results.append({'url': connection.root_url,
                            'name': name,
                            'result': self.__clean(misp_response)})
        return results

    def searchall(self, searchterm):
        """Search through all attribute types.
        
        :type searchterm: str
        :rtype: list
        """
        return self.__search(type_attribute=None, value=searchterm)
    
    def searchtag(self, searchterm):
        """Search for tags
        
        :type searchterm: str
        :rtype: list
        """
        results = []
        if not searchterm:
            raise EmptySearchtermError
        for idx, connection in enumerate(self.misp_connections):
            misp_response = connection.search(tags=searchterm)

            if isinstance(self.misp_name, list):
                name = self.misp_name[idx]
            else:
                name = self.misp_name

            results.append({'url': connection.root_url,
                            'name': name,
                            'result': self.__clean(misp_response)})
        return results
    
    def create_event(self, info, tags=["fir-incident"], distrib = 0, threat = 4, analysis = 0, ):
        """
        distrib : type=int, the distribution setting used for the attributes and for the newly created event, if relevant. [0-3].
        info : Used to populate the event info field if no event ID supplied.
        analysis : type=int, The analysis level of the newly created event, if applicable. [0-2]
        threat : type=int, The threat level ID of the newly created event, if applicable. [1-4]
        """
        events = []
        event = pymisp.MISPEvent()
        event.distribution = distrib
        event.threat_level_id = threat
        event.analysis = analysis
        event.info = info

        for idx, connection in enumerate(self.misp_connections):
            pym_event = connection.add_event(event, pythonify=True)
            for tag in tags:
                pym_tag = connection.tag(pym_event["uuid"], tag)
                success = pym_tag.get("success", False)
            events.append(pym_event.id)
        return events

    def add_tags_to_event(self, event_id, tags):
        try:
            for idx, connection in enumerate(self.misp_connections):
                pym_event = connection.get_event(event_id, pythonify=True) 
                for tag in tags:
                    pym_tag = connection.tag(pym_event["uuid"], tag)
                    success = pym_tag.get("success", False)
                return success
        except Exception as err:
            logging.error(str(err))
            return False

    
    def add_attributes_to_event(self, attributes, misp_event_id, comment = "Imported from FIR"):
        """
        Attributes is a dict of attributes to add to the event, containing value, tags & type for each attribute
        """
        for idx, connection in enumerate(self.misp_connections):
            attr_uuid_list = []
            for attribute in attributes:
                to_create = True
                # Check if attribute already exists for this event
                existing_attr = connection.search(controller='attributes', value=str(attribute["value"]), pythonify=True)

                for pym_attr in existing_attr:
                    if pym_attr.event_id == misp_event_id:
                        attr_uuid_list.append(pym_attr["uuid"])
                        to_create = False

                if to_create : 
                    misp_attribute = pymisp.MISPAttribute()
                    misp_attribute.value = str(attribute["value"])
                    misp_attribute.category = "Other"
                    misp_attribute.type = str(attribute["type"])
                    misp_attribute.comment = str(comment)
                    misp_attribute.to_ids = "0"
                    misp_attribute.distribution = "0"
                    attr = connection.add_attribute(misp_event_id, misp_attribute, pythonify=True) 
                    attr_uuid_list.append(attr["uuid"])
            # Check if tags are already added, add them if not
            for pym_attr in attr_uuid_list:
                for tag in attribute["tags"]:
                    pym_tag = connection.tag(pym_attr, tag)
                
