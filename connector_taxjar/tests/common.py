# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

"""
Helpers usable in the tests
"""

import xmlrpclib
import logging

import mock
import odoo

from contextlib import contextmanager
from os.path import dirname, join
from odoo import models
from odoo.addons.component.tests.common import SavepointComponentCase

from vcr import VCR

logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode='once',
    cassette_library_dir=join(dirname(__file__), 'fixtures/cassettes'),
    path_transformer=VCR.ensure_suffix('.yaml'),
    filter_headers=['Authorization'],
    decode_compressed_response=True,
)


class MockResponseImage(object):

    def __init__(self, resp_data, code=200, msg='OK'):
        self.resp_data = resp_data
        self.code = code
        self.msg = msg
        self.headers = {'content-type': 'image/jpeg'}

    def read(self):
        # pylint: disable=W8106
        return self.resp_data

    def getcode(self):
        return self.code


@contextmanager
def mock_urlopen_image():
    with mock.patch('urllib2.urlopen') as urlopen:
        urlopen.return_value = MockResponseImage('')
        yield


class TaxjarHelper(object):

    def __init__(self, cr, registry, model_name):
        self.cr = cr
        self.model = registry(model_name)

    def get_next_id(self):
        self.cr.execute("SELECT max(external_id::int) FROM %s " %
                        self.model._table)
        result = self.cr.fetchone()
        if result:
            return int(result[0] or 0) + 1
        else:
            return 1


class TaxjarTestCase(SavepointComponentCase):
    """ Base class - Test the imports from a Taxjar Mock.

    The data returned by Taxjar are those created for the
    demo version of Taxjar on a standard 1.9 version.
    """

    def setUp(self):
        super(TaxjarTestCase, self).setUp()
        # disable commits when run from pytest/nosetest
        odoo.tools.config['test_enable'] = True

        self.backend_model = self.env['taxjar.backend']
        self.backend = self.backend_model.create(
            {'name': 'Test Taxjar',
             'version': 'v2',
             'api_key': '',
             'company_id': self.env.user.company_id.id,
             'is_default': True,
             }
        )

    def get_taxjar_helper(self, model_name):
        return TaxjarHelper(self.cr, self.registry, model_name)

    def create_binding_no_export(self, model_name, odoo_id, external_id=None,
                                 **cols):
        if isinstance(odoo_id, models.BaseModel):
            odoo_id = odoo_id.id
        values = {
            'backend_id': self.backend.id,
            'odoo_id': odoo_id,
            'external_id': external_id,
        }
        if cols:
            values.update(cols)
        return self.env[model_name].with_context(
            connector_no_export=True,
        ).create(values)

    @contextmanager
    def mock_with_delay(self):
        with mock.patch(
                'odoo.addons.queue_job.models.base.DelayableRecordset',
                name='DelayableRecordset', spec=True
        ) as delayable_cls:
            # prepare the mocks
            delayable = mock.MagicMock(name='DelayableBinding')
            delayable_cls.return_value = delayable
            yield delayable_cls, delayable

    def parse_cassette_request(self, body):
        args, __ = xmlrpclib.loads(body)
        # the first argument is a hash, we don't mind
        return args[1:]

    def _get_external(self, external_id):
        with self.backend.work_on(self.model._name) as work:
            adapter = work.component(usage='backend.adapter')
            return adapter.read(external_id)

    def _import_record(self, model_name, taxjar_id, cassette=True):
        assert model_name.startswith('taxjar.')
        table_name = model_name.replace('.', '_')
        # strip 'taxjar_' from the model_name to shorted the filename
        filename = 'import_%s_%s' % (table_name[8:], str(taxjar_id))

        def run_import():
            with mock_urlopen_image():
                self.env[model_name].import_record(self.backend, taxjar_id)

        if cassette:
            with recorder.use_cassette(filename):
                run_import()
        else:
            run_import()

        binding = self.env[model_name].search(
            [('backend_id', '=', self.backend.id),
             ('external_id', '=', str(taxjar_id))]
        )
        self.assertEqual(len(binding), 1)
        return binding

    def assert_records(self, expected_records, records):
        """ Assert that a recordset matches with expected values.

        The expected records are a list of nametuple, the fields of the
        namedtuple must have the same name than the recordset's fields.

        The expected values are compared to the recordset and records that
        differ from the expected ones are show as ``-`` (missing) or ``+``
        (extra) lines.

        Example::

            ExpectedShop = namedtuple('ExpectedShop',
                                      'name company_id')
            expected = [
                ExpectedShop(
                    name='MyShop1',
                    company_id=self.company_ch
                ),
                ExpectedShop(
                    name='MyShop2',
                    company_id=self.company_ch
                ),
            ]
            self.assert_records(expected, shops)

        Possible output:

         - foo.shop(name: MyShop1, company_id: res.company(2,))
         - foo.shop(name: MyShop2, company_id: res.company(1,))
         + foo.shop(name: MyShop3, company_id: res.company(1,))

        :param expected_records: list of namedtuple with matching values
                                 for the records
        :param records: the recordset to check
        :raises: AssertionError if the values do not match
        """
        model_name = records._name
        records = list(records)
        assert len(expected_records) > 0, "must have > 0 expected record"
        fields = expected_records[0]._fields
        not_found = []
        equals = []
        for expected in expected_records:
            for record in records:
                for field, value in expected._asdict().iteritems():
                    if not getattr(record, field) == value:
                        break
                else:
                    records.remove(record)
                    equals.append(record)
                    break
            else:
                not_found.append(expected)
        message = []
        for record in equals:
            # same records
            message.append(
                u' ✓ {}({})'.format(
                    model_name,
                    u', '.join(u'%s: %s' % (field, getattr(record, field)) for
                               field in fields)
                )
            )
        for expected in not_found:
            # missing records
            message.append(
                u' - {}({})'.format(
                    model_name,
                    u', '.join(u'%s: %s' % (k, v) for
                               k, v in expected._asdict().iteritems())
                )
            )
        for record in records:
            # extra records
            message.append(
                u' + {}({})'.format(
                    model_name,
                    u', '.join(u'%s: %s' % (field, getattr(record, field)) for
                               field in fields)
                )
            )
        if not_found or records:
            raise AssertionError(u'Records do not match:\n\n{}'.format(
                '\n'.join(message)
            ))


class TaxjarSyncTestCase(TaxjarTestCase):

    def setUp(self):
        super(TaxjarSyncTestCase, self).setUp()

    def _create_partner(self):
        partner = self.env['res.partner'].create({
            'name': 'City of Henderson',
            'street': '240 S Water St.',
            'zip': '89015',
            'state_id': self.env.ref('base.state_us_23').id,
        })
        return partner

    def _create_sale(self, taxable=False, use_tax=None):
        self.partner = self._create_partner()
        if use_tax:
            self.tax = use_tax
        else:
            self.tax = self.env['taxjar.account.tax'].search([
                ('backend_id', '=', self.backend.id),
                ('name', 'like', 'Default'),
            ])
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'taxes_id': [(6, 0, self.tax.odoo_id.ids)],
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 79.00,
                'name': self.product.display_name,
                'customer_lead': 0.00,
            })]
        })
        if taxable:
            self.env['taxjar.account.fiscal.position'].create({
                'name': 'Test',
                'country_id': self.partner.state_id.country_id.id,
                'state_ids': [(6, 0, self.partner.state_id.ids)],
                'backend_id': self.backend.id,
            })
        return self.sale

    def _create_invoice(self, confirm=True):
        sale = self._create_sale(True)
        sale.action_confirm()
        invoice = self.env['account.invoice'].browse(
            sale.action_invoice_create(),
        )
        if confirm:
            invoice.action_invoice_open()
        return invoice

    def _import_taxes(self, return_taxes=False):
        self.env['taxjar.account.tax'].import_all(self.backend)
        if return_taxes:
            return self.env['taxjar.account.tax'].search([
                ('backend_id', '=', self.backend.id),
            ])

    def _get_transaction_for_invoice(self, invoice):
        return self.env['account.tax.transaction'].search([
            ('invoice_line_ids', 'in', invoice.invoice_line_ids.ids),
        ])
