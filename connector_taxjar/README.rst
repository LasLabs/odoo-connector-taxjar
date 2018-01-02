|License AGPL-3| | |Build Status| | |Test Coverage|

===============
Taxjar Connector
===============

This module allows for you to synchronize Odoo and Taxjar in the following
capacities:

* Import of TaxJar Product Tax codes as Odoo ``account.tax`` records
* Import of TaxJar Nexus Addresses as Odoo ``account.fiscal.position``
  records.
* Tax Rate Estimation on Sales and Invoices
* Creation of Tax Orders upon validation of Invoices
* Creation of Tax Refunds upon validation of Refund Invoices

Installation
============

To install this module, you need to:

#. Follow `queue_job <https://github.com/OCA/queue/tree/10.0/queue_job#installation>`_
   install instructions.

Configuration
=============

To configure this module, you need to:

#. Go to Connectors => [Taxjar] Backends
#. Create a new backend.
#. Click ``Import Metadata`` to perform the initial data import.
#. Restart Odoo
   * This is required for the async job queue. If purchases or refunds are not
     being sent, you either did not restart Odoo or did not properly setup
     ``queue_job``.


Usage
=====

Rate Computation
----------------

* Assign TaxJar rates to products as normal
* Create a sale or invoice including one of those products, or manually select
  a TaxJar tax in the line item.
* Tax rates should compute automatically.

Tax Purchase
------------

* Click validate in an invoice that includes a TaxJar tax
* The tax order will be sent to TaxJar

Tax Refund
----------

* Refund an invoice that includes a TaxJar tax
* Validate the refund invoice
* The tax refund will be sent to TaxJar

Known Issues / Road Map
=======================

* There will be issues if you assign more than one TaxJar applicable tax to
  the same product.
* Orders and Refunds only include the invoice information, and not the invoice
  lines. This is a limitation in Odoo and will require a lot of design, but
  should be done in ``base_tax_connector``.
* Freight tax is not yet supported for tax purchases and refunds.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/LasLabs/odoo-connector-taxjar/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Dave Lasley <dave@laslabs.com>

Do not contact contributors directly about support or help with technical issues.

Maintainer
----------

.. image:: https://laslabs.com/logo.png
   :alt: LasLabs Inc.
   :target: https://laslabs.com

This module is maintained by LasLabs Inc.


.. |Build Status| image:: https://img.shields.io/travis/LasLabs/odoo-connector-taxjar/11.0.svg
   :target: https://travis-ci.org/LasLabs/odoo-connector-taxjar
.. |Test Coverage| image:: https://img.shields.io/codecov/c/github/LasLabs/odoo-connector-taxjar/11.0.svg
   :target: https://codecov.io/gh/LasLabs/odoo-connector-taxjar
.. |License AGPL-3| image:: https://img.shields.io/badge/license-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3
