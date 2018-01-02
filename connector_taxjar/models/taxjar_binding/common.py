# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class TaxjarBinding(models.AbstractModel):
    """Abstract model for all Taxjar binding models.

    All binding models should `_inherit` from this. They also need to declare
    the ``odoo_id`` Many2One field that relates to the Odoo record that the
    binding record represents.
    """
    _name = 'taxjar.binding'
    _inherit = 'external.binding'
    _description = 'Taxjar Binding Abstract'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='taxjar.backend',
        string='Taxjar Backend',
        required=True,
        readonly=True,
        ondelete='restrict',
        default=lambda s: s._default_backend_id(),
    )
    external_id = fields.Char(
        string='ID on Taxjar',
    )

    _sql_constraints = [
        ('taxjar_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same Taxjar ID.'),
    ]

    @api.model
    def _default_backend_id(self):
        return self.env.user.company_id.taxjar_backend_id

    @api.model
    def import_all(self, backend):
        with backend.work_on(self._name) as work:
            adapter = work.component(usage='backend.adapter')
            for record in adapter.search_read():
                self.import_direct(backend, record._obj)

    @api.model
    def import_direct(self, backend, external_record):
        """Directly import a data record."""
        try:
            external_record = external_record._obj
        except AttributeError:
            pass
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            external_id = external_record.get('id')
            return importer.run(
                external_id,
                external_record=external_record,
                force=True,
            )

    @api.multi
    def _get_external_id(self):
        self.ensure_one()
        return '%s,%s' % (self._name, self.odoo_id.id)
