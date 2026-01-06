# -*- coding: utf-8 -*-
{
    'name': 'Student Management',
    'version': '15.0.1.0.0',
    'category': 'Education',
    'summary': 'Quản lý sinh viên, khoa và lớp học',
    'description': """
Student Management Module
=========================
Module quản lý:
- Sinh viên (Student)
- Khoa (Faculty)
- Lớp học (Classroom)
    """,
    'author': 'Business Internship',
    'website': 'https://www.example.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/student_views.xml',  # Load trước để định nghĩa action_student_student
        'views/classroom_views.xml',  # Load trước để định nghĩa action_student_classroom
        'views/faculty_views.xml',  # Sử dụng các action đã định nghĩa
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

