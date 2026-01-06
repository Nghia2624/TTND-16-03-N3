# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Faculty(models.Model):
    _name = 'student.faculty'
    _description = 'Faculty'
    _order = 'name'

    name = fields.Char(string='Tên khoa', required=True, tracking=True, index=True)
    code = fields.Char(string='Mã khoa', required=True, tracking=True, index=True)
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(string='Hoạt động', default=True)
    classroom_ids = fields.One2many('student.classroom', 'faculty_id', string='Lớp học')
    classroom_count = fields.Integer(string='Số lượng lớp', compute='_compute_classroom_count', store=False)
    student_count = fields.Integer(string='Số lượng sinh viên', compute='_compute_student_count', store=False)

    @api.depends('classroom_ids')
    def _compute_classroom_count(self):
        for record in self:
            record.classroom_count = len(record.classroom_ids)

    @api.depends('classroom_ids', 'classroom_ids.student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = sum(classroom.student_count for classroom in record.classroom_ids)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã khoa phải là duy nhất!'),
    ]

