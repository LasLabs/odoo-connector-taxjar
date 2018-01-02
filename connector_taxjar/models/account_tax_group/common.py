# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from uuid import uuid4

from odoo import api, models
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job


_logger = logging.getLogger(__name__)


class AccountTaxGroup(models.Model):

    _inherit = 'account.tax.group'

    @api.multi
    def compute_cache_rate(self, base_amount, rate_line_values):
        rate_line_values = super(AccountTaxGroup, self).compute_cache_rate(
            base_amount, rate_line_values,
        )
        _logger.info('Cache rate computation with %s', self.cache_name)
        if self.cache_name and 'taxjar' in self.cache_name:
            return self.env['taxjar.account.tax.group'].compute_cache_rate(
                base_amount, rate_line_values,
            )
        return rate_line_values

    @api.multi
    def do_tax_purchase(self, account_invoice_tax):
        transaction = super(AccountTaxGroup, self).do_tax_purchase(
            account_invoice_tax
        )
        if self.cache_name and 'taxjar' in self.cache_name:
            delayed = self.env['taxjar.account.tax.group'].with_delay()
            return delayed.do_tax_purchase(transaction)
        return transaction

    @api.multi
    def do_tax_refund(self, account_invoice_tax):
        transaction = super(AccountTaxGroup, self).do_tax_refund(
            account_invoice_tax
        )
        if self.cache_name and 'taxjar' in self.cache_name:
            delayed = self.env['taxjar.account.tax.group'].with_delay()
            return delayed.do_tax_refund(transaction)
        return transaction


class TaxjarAccountTaxGroup(models.AbstractModel):

    _name = 'taxjar.account.tax.group'
    _description = 'Taxjar Tax Groups'

    @api.model
    @job(default_channel='root.taxjar')
    def compute_cache_rate(self, _base_amount, rate_line_values):

        first_line = rate_line_values[0]
        partner = self.env['res.partner'].browse(first_line['partner_id'])
        company = self.env['res.company'].browse(first_line['company_id'])

        backend = self.get_partner_backend(partner, company)
        if not backend:
            return rate_line_values

        with backend.work_on(self._name) as work:
            adapter = work.component(usage='backend.adapter')
            rate_line_values = self._inject_uids(rate_line_values)
            return adapter.get_rate(partner, company, rate_line_values)

    @api.model
    @job(default_channel='root.taxjar')
    def do_tax_purchase(self, transaction):

        backend = self.get_partner_backend(
            transaction.partner_id, transaction.company_id,
        )
        if not backend or not backend.is_exporter:
            return transaction

        with backend.work_on(self._name) as work:
            adapter = work.component(usage='backend.adapter')
            return adapter.purchase(transaction)

    @api.model
    @job(default_channel='root.taxjar')
    def do_tax_refund(self, transaction):

        backend = self.get_partner_backend(
            transaction.partner_id, transaction.company_id,
        )
        if not backend or not backend.is_exporter:
            return transaction

        with backend.work_on(self._name) as work:
            adapter = work.component(usage='backend.adapter')
            return adapter.refund(transaction)

    @api.model
    def get_partner_backend(self, partner, company):

        backend = company.taxjar_backend_id
        if not backend:
            return False

        nexus = self.env['taxjar.account.fiscal.position'].get_by_partner(
            partner, backend,
        )
        if not nexus:
            return False

        return backend

    @api.model
    def _inject_uids(self, rate_line_values):
        for rate_line in rate_line_values:
            rate_line['_uid'] = str(uuid4())
        return rate_line_values


class TaxjarAccountTaxGroupAdapter(Component):
    """Utilize the API in context."""
    _name = 'taxjar.account.tax.group.adapter'
    _inherit = 'taxjar.adapter'
    _apply_on = 'taxjar.account.tax.group'

    def get_rate(self, partner, company, rate_line_values):

        api_lines = []
        rates_by_uid = {}
        shipping_lines = []
        shipping_charge = 0.0

        for rate_line in rate_line_values:

            rates_by_uid[rate_line['_uid']] = rate_line

            if rate_line['is_shipping_charge']:
                shipping_lines.append(rate_line)
                shipping_charge += (
                    rate_line['price_unit'] * rate_line['quantity']
                )

            else:
                tax = self.env['account.tax'].browse(rate_line['tax_id'])
                price_total = rate_line['price_unit'] * rate_line['quantity']
                discount = price_total * (rate_line['discount'] / 100)
                api_lines.append({
                    'id': rate_line['_uid'],
                    'quantity': rate_line['quantity'],
                    'product_tax_code': tax.taxjar_product_code,
                    'unit_price': rate_line['price_unit'],
                    'discount': discount,
                })

        values = {
            'shipping': shipping_charge,
            'line_items': api_lines,
        }
        values.update(self._get_partner_address(company, 'from'))
        values.update(self._get_partner_address(partner, 'to'))

        result = self.taxjar.tax_for_order(values)

        taxed_amount = 0.0

        for result_line in result['breakdown']['line_items']:
            rates_by_uid[result_line['id']].update({
                'price_tax': result_line['tax_collectable'],
                'rate_tax': result_line['combined_tax_rate'],
            })
            taxed_amount += result_line['tax_collectable']

        freight_tax = result.amount_to_collect - taxed_amount
        if freight_tax:
            freight_tax_price = freight_tax / len(shipping_lines)
            freight_tax_rate = freight_tax / shipping_charge
            for shipping_line in shipping_lines:
                shipping_line.update({
                    'price_tax': freight_tax_price,
                    'rate_tax': freight_tax_rate,
                })

        return rate_line_values

    def purchase(self, transaction):
        order_values = self._get_order_values_from_transaction(
            transaction,
        )
        return self.taxjar.create_order(order_values)

    def refund(self, transaction):
        refund_values = self._get_order_values_from_transaction(
            transaction,
        )
        purchase = transaction.line_ids[:1].parent_id.transaction_id
        refund_values['transaction_reference_id'] = purchase.id
        return self.taxjar.create_refund(refund_values)

    def _get_order_values_from_transaction(self, transaction):

        # @TODO: (In ReadMe): Support line items in base module
        # line_items = []
        # for invoice_line in transaction.invoice_line_ids:
        #
        #     for tax in invoice_line.product_id.taxes_id:
        #         if tax.taxjar_product_code:
        #             product_code = tax.taxjar_product_code
        #             break
        #     else:
        #         product_code = None
        #
        #     price_total = invoice_line.price_unit * invoice_line.quantity
        #     discount = price_total * (invoice_line.discount / 100)
        #
        #     line_items.append({
        #         'description': invoice_line.product_id.name,
        #         'unit_price': invoice_line.price_unit,
        #         'quantity': invoice_line.quantity,
        #         'product_identifier': invoice_line.product_id.id,
        #         'product_tax_code': product_code,
        #         'discount': discount,
        #     })

        values = {
            'transaction_id': transaction.id,
            'transaction_date': transaction.date,
            'amount': transaction.amount_subtotal,
            'shipping': 0,
            'sales_tax': transaction.amount_tax,
        }
        values.update(
            self._get_partner_address(transaction.company_id, 'from'),
        )
        values.update(
            self._get_partner_address(transaction.partner_id, 'to'),
        )
        return values

    def _get_partner_address(self, partner, direction='to'):
        return {
            '%s_country' % direction: partner.state_id.country_id.code,
            '%s_zip' % direction: partner.zip,
            '%s_state' % direction: partner.state_id.code,
            '%s_city' % direction: partner.city,
            '%s_street' % direction: partner.street,
        }
