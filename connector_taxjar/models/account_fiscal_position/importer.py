# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class TaxjarAccountFiscalPositionImportMapper(Component):
    _name = 'taxjar.import.mapper.account.fiscal.position'
    _inherit = 'taxjar.import.mapper'
    _apply_on = 'taxjar.account.fiscal.position'

    @mapping
    def name(self, record):
        return {
            'name': '[%s] %s, %s' % (
                self.backend_record.name,
                record['region'],
                record['region_code'],
            )
        }

    @mapping
    def country_id_state_ids(self, record):
        country = self.env['res.country'].search([
            ('code', '=', record['country_code']),
        ])
        state = self.env['res.country.state'].search([
            ('country_id', '=', country.id),
            ('code', '=', record['region_code']),
        ])
        return {
            'country_id': country.id,
            'state_ids': [(6, 0, state.ids)],
        }

    @mapping
    @only_create
    def static_mappings(self, _):
        """Return the staticly defined values."""
        return {'auto_apply': True,
                }


class TaxjarAccountFiscalPositionImporter(Component):
    """Import one Taxjar record."""
    _name = 'taxjar.record.importer.account.fiscal.position'
    _inherit = 'taxjar.importer'
    _apply_on = 'taxjar.account.fiscal.position'
