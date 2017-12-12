# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

from contextlib import contextmanager

from .common import TaxjarSyncTestCase, recorder

from taxjar.data.order import TaxJarOrder


class TestCommonAccountTaxGroup(TaxjarSyncTestCase):

    def setUp(self):
        super(TestCommonAccountTaxGroup, self).setUp()
        self.model = self.env['taxjar.account.tax.group']

    @contextmanager
    def _identical_uid(self):
        """Override the UUID4 to return the same thing.

        This allows for recording of normally unique transactions.
        """
        patch = 'odoo.addons.connector_taxjar.models.account_tax_group' \
                '.common.uuid4'
        with mock.patch(patch) as mk:
            mk.return_value = 'The Same UUID!'
            yield mk

    @recorder.use_cassette()
    def test_account_tax_group_compute_cache(self):
        """It should lookup the rate from TaxJar."""
        sale = self._create_sale(True)
        with self._identical_uid():
            # Trigger the depends
            sale.order_line.write({'product_uom_qty': 2})
        self.assertTrue(sale.amount_tax)

    @recorder.use_cassette()
    def test_do_tax_purchase_calls_delay(self):
        """It should call the delayed method with proper args."""
        with self.mock_with_delay() as (delayable_cls, delayable):
            with self._identical_uid():
                self._create_invoice()
            self.assertEqual(
                delayable_cls.call_count, 1, '`with_delay` was not called.',
            )
            delay_args, delay_kwargs = delayable_cls.call_args
            self.assertEqual(
                delay_args,
                (self.env['taxjar.account.tax.group'], ),
                '`with_delay` was not called on the correct model.',
            )
            delayable.do_tax_purchase.assert_called_once()

    @recorder.use_cassette()
    def test_do_tax_refund_calls_delay(self):
        """It should call the delayed method with proper args."""
        with self._identical_uid():
            invoice = self._create_invoice()
        refund = invoice.refund()
        with self.mock_with_delay() as (delayable_cls, delayable):
            with self._identical_uid():
                refund.action_invoice_open()
            self.assertEqual(
                delayable_cls.call_count, 1, '`with_delay` was not called.',
            )
            delay_args, delay_kwargs = delayable_cls.call_args
            self.assertEqual(
                delay_args,
                (self.model, ),
                '`with_delay` was not called on the correct model.',
            )
            delayable.do_tax_refund.assert_called_once()

    @recorder.use_cassette()
    def test_taxjar_do_tax_purchase(self):
        """It should send the order to TaxJar & receive the proper response.
        """
        with self.mock_with_delay():
            with self._identical_uid():
                invoice = self._create_invoice()
        result = self.model.do_tax_purchase(
            self._get_transaction_for_invoice(invoice),
        )
        self.assertIsInstance(result, TaxJarOrder)
        self.assertGreater(result.amount, 0)

    @recorder.use_cassette()
    def test_taxjar_do_tax_refund(self):
        """It should send the refund to TaxJar & receive the proper response.
        """
        with self.mock_with_delay():
            with self._identical_uid():
                invoice = self._create_invoice()
                refund = invoice.refund()
                refund.action_invoice_open()
        result = self.model.do_tax_refund(
            self._get_transaction_for_invoice(refund),
        )
        self.assertIsInstance(result, TaxJarOrder)
        self.assertLess(result.amount, 0)
