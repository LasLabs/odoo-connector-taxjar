# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .common import TaxjarSyncTestCase, recorder


class TestImportAccountTax(TaxjarSyncTestCase):

    REMOTE_COUNT = 18

    def setUp(self):
        super(TestImportAccountTax, self).setUp()
        self.model = self.env['taxjar.account.tax']

    @recorder.use_cassette
    def test_import_account_tax_all(self):
        """It should import the tax types from the API."""
        self.assertEqual(self.model.search_count([]), 1)
        self._import_taxes()
        self.assertEqual(self.model.search_count([]), self.REMOTE_COUNT)
