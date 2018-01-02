# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# pylint: disable=C8101
{
    "name": "TaxJar Connector",
    "summary": "Two way synchronization with TaxJar",
    "version": "11.0.1.0.0",
    "category": "Connector",
    "website": "https://laslabs.com",
    "author": "LasLabs",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ['taxjar'],
    },
    "depends": [
        "connector",
        "sale_tax_connector",
        "sales_team",
    ],
    "data": [
        "views/taxjar_account_fiscal_position_view.xml",
        "views/taxjar_backend_view.xml",
        # Menu must come last
        "views/connector_menu.xml",
        "security/ir.model.access.csv",
    ],
}
