{
    'name': 'Autenticacion Inteligente y Detección de fraude',
    'version': '1.0',
    'summary': 'Módulo orientado a mejorar la seguridad con autenticación inteligente y detección de actividad sospechosa mediante IA',
    'description': 'Este módulo proporciona funcionalidades de autenticación inteligente y detección de actividad sospechosa mediante IA para mejorar la seguridad en el sistema.',
    'author': 'Securenet',
    'category': 'Custom',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/historial_accesos_view.xml',
        'views/perfil_usuarios_view.xml',
        'views/informe_usuarios_adaptado.xml',
        'views/informe_franjas_horarias.xml'
    ],
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['scikit-learn', 'pandas', 'numpy']
    }
}