# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class BaseTaxjarConnectorComponent(AbstractComponent):

    _name = 'base.taxjar.connector'
    _inherit = 'base.connector'
    _collection = 'taxjar.backend'
