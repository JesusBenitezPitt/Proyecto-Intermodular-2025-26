{
    'name': 'Autenticacion Inteligente Básica',
    'version': '1.0',
    'summary': 'Módulo personalizado de autenticación inteligente básica para Odoo',
    'description': 'Este módulo proporciona funcionalidades básicas de autenticación inteligente para mejorar la seguridad en Odoo.',
    'author': 'Jesús Benítez Pitt',
    'category': 'Custom',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/perfil_usuarios_view.xml',
        'views/informe_usuarios_adaptado.xml'
    ],
    'installable': True,
    'application': True,
}