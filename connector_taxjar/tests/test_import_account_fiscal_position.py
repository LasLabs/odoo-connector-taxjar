# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .common import TaxjarSyncTestCase, recorder


class TestImportAccountFiscalPosition(TaxjarSyncTestCase):

    REMOTE_COUNT = 1

    def setUp(self):
        super(TestImportAccountFiscalPosition, self).setUp()
        self.model = self.env['taxjar.account.fiscal.position']

    @recorder.use_cassette
    def test_import_account_fiscal_position_all(self):
        """It should import the Nexus regions from the API."""
        self.assertEqual(self.model.search_count([]), 0)
        self.model.import_all(self.backend)
        self.assertEqual(self.model.search_count([]), self.REMOTE_COUNT)
