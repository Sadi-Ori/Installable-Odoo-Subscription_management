{
    'name': 'Subscription Management',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Manage Subscriptions and Subscription Products',
    'author': 'Matjel Ltd',
    'depends': ['base', 'sale', 'account'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/subscription_view.xml',
    ],
    'installable': True,
    'application': True,
}
