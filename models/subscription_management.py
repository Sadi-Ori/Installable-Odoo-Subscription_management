from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_subscription_product = fields.Boolean('Is Subscription Product', default=False)

    @api.model
    def create(self, vals):
        # Set product type to 'Service' for subscription-based products
        if vals.get('is_subscription_product', False):
            vals['type'] = 'service'
        return super(ProductTemplate, self).create(vals)

class SubscriptionPlan(models.Model):
    _name = 'subscription.plan'
    _description = 'Subscription Plan'

    name = fields.Char('Plan Name', required=True)
    description = fields.Text('Description')
    product_ids = fields.Many2many('product.product', string='Subscription Products')

    @api.model
    def create_plan(self, name, products):
        plan = self.create({
            'name': name,
            'product_ids': [(6, 0, products)]
        })
        return plan

class SubscriptionProduct(models.Model):
    _name = 'subscription.product'
    _description = 'Subscription Product'

    name = fields.Char('Product Name', required=True)
    subscription_plan_ids = fields.Many2many('subscription.plan', string='Subscription Plans')

    @api.model
    def create_product(self, name, plans):
        product = self.create({
            'name': name,
            'subscription_plan_ids': [(6, 0, plans)]
        })
        return product

class Subscription(models.Model):
    _name = 'subscription.management'
    _description = 'Subscription Management'

    plan_id = fields.Many2one('subscription.plan', string='Subscription Plan')
    customer_id = fields.Many2one('res.partner', string='Customer')
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date')
    active = fields.Boolean('Active', default=True)
    recurrence_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Recurrence Frequency', default='monthly')
    bill_cycles = fields.Integer('Number of Bill Cycles', default=12)
    trial_period = fields.Boolean('Trial Period', default=True)
    trial_end_date = fields.Date('Trial End Date')

    @api.model
    def create_subscription(self, customer, plan):
        subscription = self.create({
            'customer_id': customer.id,
            'plan_id': plan.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.from_string(fields.Date.today()) + timedelta(days=365),
            'active': True,
        })
        return subscription

    def set_recurrence_and_billing(self, recurrence, cycles):
        self.recurrence_frequency = recurrence
        self.bill_cycles = cycles

    def create_invoice(self):
        if self.trial_period:
            raise UserError('Cannot generate invoice during the trial period.')
        else:
            # Logic to create an invoice
            invoice = self.env['account.invoice'].create({
                'partner_id': self.customer_id.id,
                'type': 'out_invoice',
                'subscription_id': self.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.plan_id.product_ids[0].id,  # Using the first product in the plan
                    'quantity': 1,
                    'price_unit': self.plan_id.product_ids[0].list_price,
                })],
            })
            return invoice

    def end_trial_period(self):
        self.trial_period = False
        self.trial_end_date = fields.Date.today()

    @api.model
    def open_subscription_management(self):
        # Fixing the context issue by explicitly passing active_id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscription Management',
            'res_model': 'subscription.management',
            'view_mode': 'tree,form',
            'context': {'active_id': self.id},  # Active_id added explicitly
        }

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create_subscription_from_sale_order(self, order_id):
        order = self.browse(order_id)
        for line in order.order_line:
            if line.product_id.is_subscription_product:
                subscription = self.env['subscription.management'].create({
                    'customer_id': order.partner_id.id,
                    'plan_id': line.product_id.subscription_plan_ids[0].id,  # Assuming one plan per product
                    'start_date': fields.Date.today(),
                    'end_date': fields.Date.from_string(fields.Date.today()) + timedelta(days=365),
                })
        return True