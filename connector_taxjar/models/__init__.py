# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Core; load before everything
from . import taxjar_backend
from . import taxjar_binding

# Data Models
from . import account_fiscal_position
from . import account_tax
from . import account_tax_group
from . import res_company
