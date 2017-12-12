# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class AccountTaxRate(models.Model):

    _inherit = 'account.tax.rate'

    taxjar_bind_ids = fields.One2many(
        string='Taxjar Bindings',
        comodel_name='taxjar.account.tax.rate',
        inverse_name='odoo_id',
    )
    taxjar_product_code = fields.Char()


class TaxjarAccountTaxRate(models.Model):

    _name = 'taxjar.account.tax.rate'
    _inherit = 'taxjar.binding'
    _inherits = {'account.tax.rate': 'odoo_id'}
    _description = 'Taxjar Tax Rate'

    odoo_id = fields.Many2one(
        string='Tax',
        comodel_name='account.tax.rate',
        required=True,
        ondelete='cascade',
    )


class TaxjarAccountTaxRateAdapter(Component):
    """Utilize the API in context."""
    _name = 'taxjar.account.tax.rate.adapter'
    _inherit = 'taxjar.adapter'
    _apply_on = 'taxjar.account.tax.rate'

    def search_read(self, filters=None):
        return self.taxjar.categories()

    def get_rate(self, tax, price_unit, quantity, partner, company):
        result = self.taxjar.tax_for_order({
            'from_country': company.state_id.country_id.code,
            'from_zip': company.zip,
            'from_state': company.state_id.code,
            'from_city': company.city,
            'from_street': company.street,
            'to_country': partner.state_id.country_id.code,
            'to_zip': partner.zip,
            'to_state': partner.state_id.code,
            'to_city': partner.city,
            'to_street': partner.street,
            'shipping': 0.0,
            'line_items': [{
                'id': self.env['ir.sequence'].next_by_code(
                    'taxjar.estimation.line',
                ),
                'quantity': quantity,
                'product_tax_code': tax.taxjar_product_code,
                'unit_price': price_unit,
                'discount': 0,
            }]
        })
        return result.amount_to_collect
