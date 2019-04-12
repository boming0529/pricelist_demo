# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class pricelist_test(models.Model):
#     _name = 'pricelist_test.pricelist_test'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()

#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class pricelist(models.Model):

    _inherit = ['product.pricelist']

    def _compute_pricelist_multi(self, products_qty_partner, date=False, uom_id=False, ids=False):
        """ Low-level method - Multi pricelist, multi products
        Returns: dict{product_id: dict{pricelist_id: (price, suitable_rule)} }"""
        if ids:
            pricelists = self.browse(ids)
        else:
            pricelists = self
        results = {}
        for pricelist in pricelists:
            subres = pricelist._compute_price_rule(
                products_qty_partner, date=date, uom_id=uom_id)
            for product_id, price in subres.selfs():
                results.setdefault(product_id, {})
                results[product_id][pricelist.id] = price
        return results


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    mpl = fields.Many2many(
        string='on sale',
        comodel_name='product.pricelist',
        relation='sale_order_line_mulit_pricelist_rel',
    )

    all_mpl = fields.Many2many(
        string='total on sale',
        comodel_name='product.pricelist',
        relation='sale_order_amount_all_pricelist_rel',
    )

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        if self.all_mpl :
            temp_discount = 0
            need_create = 0
            # product_discount = self.env.ref('pricelist_test.product_product_all_discount')
            for order in self:
                amount_untaxed = amount_tax = 0.0
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                    # if product_discount
                    
            if amount_untaxed > 0:
                for pl in self.all_mpl:
                    discount = 0
                    product = self.env.ref('pricelist_test.product_product_all_discount').with_context(
                        lang=self.partner_id.lang,
                        partner=self.partner_id,
                        quantity=1,
                        date=self.date_order,
                        pricelist=pl.id,
                        uom=self.env.ref('uom.product_uom_unit').id,
                        fiscal_position=self.env.context.get('fiscal_position')
                    )
                    product.list_price = amount_untaxed + amount_tax
                    product_context = dict(self.env.context, partner_id=self.partner_id.id,
                                        date=self.date_order, uom=self.env.ref('uom.product_uom_unit').id)
                    price, rule_id = pl.with_context(product_context).get_product_price_rule(
                        product, 1.0, self.partner_id)
                    discount = (amount_untaxed + amount_tax - price) / (amount_untaxed + amount_tax) * 100
                    if discount > 0:
                        if temp_discount > 0:
                            discount = 100 - (1 - discount/100.0) * (100 - temp_discount)
                        else:
                            discount = discount
                        temp_discount = discount
                percentage = (1 - discount/100)
                if need_create == 0:
                    line_id = self.env['sale.order.line'].new()
                    line_id.product_id = self.env.ref('pricelist_test.product_product_all_discount').id
                    line_id.price_unit = amount_untaxed - (amount_untaxed) * percentage
                    line_id.product_uom_qty = -1
                    line_id.tax_id = False
                    line_id.name = self.env.ref('pricelist_test.product_product_all_discount').name
                    line_id.discount = 0
                    line_id.discount_ok = True
                    line_id.order_id = order.id
                for order in self:
                    sum_amount_untaxed = sum_amount_tax = 0.0
                    
                    for line in order.order_line:

                        if need_create > 0 and discount > 0 and line.product_id.id == self.env.ref('pricelist_test.product_product_all_discount').id:
                            line.price_unit = (amount_untaxed + amount_tax) * percentage
                        sum_amount_untaxed += line.price_subtotal
                        sum_amount_tax += line.price_tax
                        
                    
                    order.update({
                        'amount_untaxed': sum_amount_untaxed ,
                        'amount_tax': sum_amount_tax ,
                        'amount_total': sum_amount_untaxed + sum_amount_tax,
                    })
        else:
            super(SaleOrder, self)._amount_all()

class SaleOrderLine(models.Model):
    _inherit = ["sale.order.line"]

    discount_ok = fields.Boolean(
        string='discount_ok',
    )
    

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        self.discount = 0.0
        result = super(SaleOrderLine, self)._onchange_discount()
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and
                self.env.user.has_group('sale.group_discount_per_so_line') and self.order_id.mpl):
            return
        temp_discount = 0
        for pl in self.order_id.mpl:
            discount = 0
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=pl.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id,
                                   date=self.order_id.date_order, uom=self.product_uom.id)
            price, rule_id = pl.with_context(product_context).get_product_price_rule(
                self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
            new_list_price, currency = self.with_context(product_context)._get_real_price_currency(
                product, rule_id, self.product_uom_qty, self.product_uom, pl.id)
            if new_list_price != 0:
                if pl.currency_id != currency:
                    # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                    new_list_price = currency._convert(
                        new_list_price, pl.currency_id,
                        self.order_id.company_id, self.order_id.date_order or fields.Date.today())
                discount = (new_list_price - price) / new_list_price * 100
            
                if discount > 0:
                    if temp_discount > 0:
                        discount = 100 - (1 - discount/100.0) * (100 - temp_discount)
                    else:
                        discount = discount
                    temp_discount = discount
        if discount > 0:
            if self.discount > 0:
                self.discount = 100 - (1 - self.discount/100.0) * (100 - discount)
            else:
                self.discount = discount

