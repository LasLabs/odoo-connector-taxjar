# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.component.core import Component


class AccountFiscalPosition(models.Model):

    _inherit = 'account.fiscal.position'

    taxjar_bind_ids = fields.One2many(
        string='Taxjar Bindings',
        comodel_name='taxjar.account.fiscal.position',
        inverse_name='odoo_id',
    )


class TaxjarAccountFiscalPosition(models.Model):

    _name = 'taxjar.account.fiscal.position'
    _inherit = 'taxjar.binding'
    _inherits = {'account.fiscal.position': 'odoo_id'}
    _description = 'TaxJar Nexus Regions'

    _rec_name = 'name'

    odoo_id = fields.Many2one(
        string='Fiscal Position',
        comodel_name='account.fiscal.position',
        required=True,
        ondelete='cascade',
    )
    api_address = fields.Serialized(
        compute='_compute_api_address',
    )

    @api.multi
    def _compute_api_address(self):
        for record in self:
            record.api_address = {
                'id': record.external_id or record.id,
                'country': record.country_id.code,
                'state': record.state_ids[0].code,
            }

    @api.model
    def get_by_partner(self, partner, backend=None):

        if backend is None:
            backend = partner.company_id.taxjar_backend_id
        if not backend:
            return

        if partner.property_account_position_id:
            return self.search([
                ('odoo_id', '=', partner.property_account_position_id.id),
                ('backend_id', '=', backend.id),
            ])

        return self.search([
            ('backend_id', '=', backend.id),
            ('country_id', '=', partner.state_id.country_id.id),
            ('state_ids', 'in', partner.state_id.ids),
        ])


class TaxjarAccountFiscalPositionAdapter(Component):
    """Utilize the API in context."""
    _name = 'taxjar.account.fiscal.position.adapter'
    _inherit = 'taxjar.adapter'
    _apply_on = 'taxjar.account.fiscal.position'

    def search_read(self, filters=None):
        return self.taxjar.nexus_regions()
