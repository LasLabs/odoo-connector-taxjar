# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class TaxjarAccountTaxImportMapper(Component):
    _name = 'taxjar.import.mapper.account.tax'
    _inherit = 'taxjar.import.mapper'
    _apply_on = 'taxjar.account.tax'

    direct = [('description', 'description'),
              ('product_tax_code', 'taxjar_product_code'),
              ]

    @mapping
    def name(self, record):
        return {
            'name': '[%s] %s' % (self.backend_record.name, record['name']),
        }

    @mapping
    @only_create
    def default_vals(self, _):
        return self.env['taxjar.account.tax']._get_default_vals()


class TaxjarAccountTaxImporter(Component):
    """Import one Taxjar record."""
    _name = 'taxjar.record.importer.account.tax'
    _inherit = 'taxjar.importer'
    _apply_on = 'taxjar.account.tax'
