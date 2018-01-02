# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import AbstractComponent


_logger = logging.getLogger(__name__)


class TaxjarImporter(AbstractComponent):
    """ Base importer for Taxjar """

    _name = 'taxjar.importer'
    _inherit = ['base.importer', 'base.taxjar.connector']
    _usage = 'record.importer'

    def __init__(self, work_context):
        super(TaxjarImporter, self).__init__(work_context)
        self.external_id = None
        self.taxjar_record = None

    def _get_taxjar_data(self):
        """Return the raw Taxjar data for ``self.external_id``."""
        return self.backend_adapter.read(self.external_id)

    def _before_import(self):
        """Hook called before the import, when we have the Taxjar data."""
        return

    def _import_dependencies(self):
        """Import the dependencies for the record.

        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        return

    def _map_data(self):
        """Returns an instance of
        :py:class:`~odoo.addons.connector.components.mapper.MapRecord`
        """
        return self.mapper.map_record(self.taxjar_record)

    def _validate_data(self, data):
        """Check if the values to import are correct.

        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.

        Raises:
            InvalidDataError: In the event of a validation error
        """
        return

    def _must_skip(self):
        """Hook called right after we read the data from the backend.
        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).
        If it returns None, the import will continue normally.
        :returns: None | str | unicode
        """
        return

    def _get_binding(self):
        return self.binder.to_internal(self.external_id)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """Create the Odoo record. """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        _logger.debug(
            '%d created from taxjar %s', binding, self.external_id,
        )
        return binding

    def _after_import(self, binding):
        """Hook called at the end of the import."""
        return

    def run(self, external_id, force=False, external_record=None):
        """Run the synchronization.

        Args:
            external_id (int | taxjar.BaseModel): identifier of the
                record in Taxjar, or a Taxjar record.
            force (bool, optional): Set to ``True`` to force the sync.
            external_record (taxjar.models.BaseModel): Record from
                Taxjar. Defining this will force the import of this
                record, instead of the search of the remote.

        Returns:
            str: Canonical status message.
        """

        self.external_id = external_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.work.model_name,
            external_id,
        )

        if external_record is not None:
            self.taxjar_record = external_record
        else:
            self.taxjar_record = self._get_taxjar_data()

        skip = self._must_skip()
        if skip:
            return skip

        binding = self._get_binding()

        # Keep a lock on this import until the transaction is committed.
        # The lock is kept since we have detected that the information
        # will be updated in Odoo.
        self.advisory_lock_or_retry(lock_name)
        self._before_import()

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data()

        if binding:
            raise NotImplementedError(
                'Updating is not implemented.',
            )
        else:
            record = self._create_data(map_record)
            binding = self._create(record)

        self.binder.bind(self.external_id, binding)

        self._after_import(binding)

        return binding
