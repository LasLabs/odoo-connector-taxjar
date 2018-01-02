# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping, only_create


class TaxjarImportMapper(AbstractComponent):
    _name = 'taxjar.import.mapper'
    _inherit = ['base.taxjar.connector', 'base.import.mapper']
    _usage = 'import.mapper'

    @mapping
    @only_create
    def backend_id(self, _):
        return {'backend_id': self.backend_record.id}


class TaxjarExportMapper(AbstractComponent):
    _name = 'taxjar.export.mapper'
    _inherit = ['base.taxjar.connector', 'base.export.mapper']
    _usage = 'export.mapper'
