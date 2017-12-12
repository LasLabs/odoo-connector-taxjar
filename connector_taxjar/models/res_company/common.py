# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    taxjar_backend_id = fields.Many2one(
        string='Default TaxJar Backend',
        comodel_name='taxjar.backend',
        compute='_compute_taxjar_backend_id',
    )

    @api.multi
    def _compute_taxjar_backend_id(self):
        for record in self:
            backend = self.env['taxjar.backend'].search([
                ('company_id', '=', record.id),
            ])
            record.taxjar_backend_id = backend.id
