# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.component.core import Component


class AccountTax(models.Model):

    _inherit = 'account.tax'

    taxjar_bind_ids = fields.One2many(
        string='Taxjar Bindings',
        comodel_name='taxjar.account.tax',
        inverse_name='odoo_id',
    )
    taxjar_product_code = fields.Char()


class TaxjarAccountTax(models.Model):

    _name = 'taxjar.account.tax'
    _inherit = 'taxjar.binding'
    _inherits = {'account.tax': 'odoo_id'}
    _description = 'Taxjar Tax Categories'

    _rec_name = 'name'

    odoo_id = fields.Many2one(
        string='Tax',
        comodel_name='account.tax',
        required=True,
        ondelete='cascade',
    )

    @api.model
    def _get_default_vals(self):
        """Return values for creation of a new TaxJar tax."""
        backend = self.env.user.company_id.taxjar_backend_id
        return {
            'amount_type': 'cache',
            'type_tax_use': 'sale',
            'amount': 0.0,
            'tax_group_id': backend.tax_group_id.id,
        }


class TaxjarAccountTaxAdapter(Component):
    """Utilize the API in context."""
    _name = 'taxjar.account.tax.adapter'
    _inherit = 'taxjar.adapter'
    _apply_on = 'taxjar.account.tax'

    def search_read(self, filters=None):
        return self.taxjar.categories()
