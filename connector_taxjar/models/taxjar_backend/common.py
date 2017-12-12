# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class TaxjarBackend(models.Model):
    _name = 'taxjar.backend'
    _description = 'Taxjar Backend'
    _inherit = 'connector.backend',
    _backend_type = 'taxjar'

    version = fields.Selection(
        selection='_get_versions',
        default='v2',
        required=True,
    )
    api_key = fields.Char(
        required=True,
    )
    is_exporter = fields.Boolean(
        string='Export Transactions',
        default=True,
        help='Uncheck this to disable transaction exporting to TaxJar. '
             'This is beneficial because it will reduce the amount of total '
             'API calls to TaxCloud, but as a consequence transactions will '
             'not be exported to TaxCloud for reporting or subsequent '
             'submission.',
    )
    active = fields.Boolean(
        default=True,
    )
    company_id = fields.Many2one(
        string='Companies',
        inverse_name='taxjar_backend_id',
        default=lambda s: s.env.user.company_id.id,
        comodel_name='res.company',
    )
    tax_group_id = fields.Many2one(
        string='Tax Group',
        comodel_name='account.tax.group',
        readonly=True,
    )
    nexus_location_ids = fields.One2many(
        string='Nexus Locations',
        comodel_name='taxjar.account.fiscal.position',
        inverse_name='backend_id',
    )

    _sql_constraints = [
        ('company_id_unique', 'UNIQUE(company_id)',
         'You cannot have two TaxJar connectors for the same company.'),
    ]

    @api.model
    def _get_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('v2', 'v2')]

    @api.model
    def create(self, vals):
        """Create the default tax and tax group."""
        backend = super(TaxjarBackend, self).create(vals)
        backend.tax_group_id = self.env['account.tax.group'].create({
            'name': backend.name,
            'cache_name': str(backend),
        })
        tax_vals = self.env['taxjar.account.tax']._get_default_vals()
        tax_vals.update({
            'name': '[%s] Default' % backend.name,
            'tax_group_id': backend.tax_group_id.id,
        })
        self.env['taxjar.account.tax'].create(tax_vals)
        return backend

    @api.multi
    def action_sync_metadata(self):
        for record in self:
            self.env['taxjar.account.tax'].import_all(record)
            self.env['taxjar.account.fiscal.position'].import_all(record)
