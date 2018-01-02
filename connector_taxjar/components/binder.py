# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class TaxjarModelBinder(Component):
    """Bind records and give odoo/taxjar ID relations."""

    _name = 'taxjar.binder'
    _inherit = ['base.binder', 'base.taxjar.connector']
    _apply_on = [
        'taxjar.account.fiscal.position',
        'taxjar.account.tax',
        'taxjar.sale.order',
        'taxjar.sale.tax.rate',
    ]

    def bind(self, external_id, binding):
        if external_id is None:
            external_id = binding._get_external_id()
        return super(TaxjarModelBinder, self).bind(external_id, binding)
