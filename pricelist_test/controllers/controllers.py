# -*- coding: utf-8 -*-
from odoo import http

# class PricelistTest(http.Controller):
#     @http.route('/pricelist_test/pricelist_test/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pricelist_test/pricelist_test/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pricelist_test.listing', {
#             'root': '/pricelist_test/pricelist_test',
#             'objects': http.request.env['pricelist_test.pricelist_test'].search([]),
#         })

#     @http.route('/pricelist_test/pricelist_test/objects/<model("pricelist_test.pricelist_test"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pricelist_test.object', {
#             'object': obj
#         })