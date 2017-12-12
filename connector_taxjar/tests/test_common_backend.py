# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .common import TaxjarSyncTestCase, recorder

from .test_import_account_tax import TestImportAccountTax
from .test_import_account_fiscal_position import (
    TestImportAccountFiscalPosition,
)


class TestCommonBackend(TaxjarSyncTestCase):

    def setUp(self):
        super(TestCommonBackend, self).setUp()

    @recorder.use_cassette
    def test_action_sync_metadata_imports_taxes(self):
        """It should import the taxes with the metadata."""
        self.backend.action_sync_metadata()
        self.assertEqual(
            self.env['taxjar.account.tax'].search_count([]),
            TestImportAccountTax.REMOTE_COUNT,
        )

    @recorder.use_cassette
    def test_action_sync_metadata_imports_taxes(self):
        """It should import the taxes with the metadata."""
        self.backend.action_sync_metadata()
        self.assertEqual(
            self.env['taxjar.account.fiscal.position'].search_count([]),
            TestImportAccountFiscalPosition.REMOTE_COUNT,
        )
