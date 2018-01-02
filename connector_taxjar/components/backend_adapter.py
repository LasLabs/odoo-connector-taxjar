# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

try:
    import taxjar
except ImportError:
    _logger.debug("`taxjar` Python library not installed.")


class TaxjarAdapter(AbstractComponent):

    _name = 'taxjar.adapter'
    _inherit = ['base.backend.adapter', 'base.taxjar.connector']
    _usage = 'backend.adapter'

    UID_FIELD = 'name'

    def __init__(self, connector_env):
        super(TaxjarAdapter, self).__init__(connector_env)
        self.taxjar = taxjar.Client(api_key=self.backend_record.api_key)

    # pylint: disable=W8106
    def read(self, external_id):
        """Return the record from the remote.

        This is a default implementation that uses ``search_read``.

        Args:
            external_id (int): The ID on the remote. Taxjar doesn't actually
                have a concept of an ID though, so this is the UID that was
                created for tracking.
        """
        results = self.search_read({
            self.UID_FIELD: external_id,
        })
        for result in results:
            return result._obj

    def search(self, filters=None):
        return [
            r[self.UID_FIELD] for r in self.search_read(filters)
        ]

    def search_read(self, filters=None):
        raise NotImplementedError

    # pylint: disable=W8106
    def create(self, data):
        """Create the web connector on the remote.

        Args:
            data (dict): The data dictionary to create on remote.
        """
        raise NotImplementedError

    # pylint: disable=W8106
    def write(self, external_id, data):
        """Update a record on the remote.

        Args:
            data (dict): A dictionary representing the record data.
        """
        raise NotImplementedError

    def delete(self, external_id):
        raise NotImplementedError
