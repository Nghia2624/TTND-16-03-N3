# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Classroom(models.Model):
    _name = 'student.classroom'
    _description = 'Classroom'
    _order = 'name'

    name = fields.Char(string='Tên lớp', required=True, tracking=True, index=True)
    code = fields.Char(string='Mã lớp', required=True, tracking=True, index=True)
    faculty_id = fields.Many2one('student.faculty', string='Khoa', required=True, tracking=True, ondelete='cascade')
    capacity = fields.Integer(string='Sức chứa', default=50, required=True)
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(string='Hoạt động', default=True)
    student_ids = fields.One2many('student.student', 'classroom_id', string='Sinh viên')
    student_count = fields.Integer(string='Số lượng sinh viên', compute='_compute_student_count', store=True)
    available_seats = fields.Integer(string='Chỗ trống', compute='_compute_available_seats', store=False)

    @api.depends('student_ids', 'capacity')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids.filtered(lambda s: s.active))

    @api.depends('student_count', 'capacity')
    def _compute_available_seats(self):
        for record in self:
            record.available_seats = record.capacity - record.student_count

    @api.constrains('capacity', 'student_ids')
    def _check_capacity(self):
        for record in self:
            if record.capacity <= 0:
                raise ValidationError('Sức chứa lớp học phải lớn hơn 0!')
            # Tính lại student_count để đảm bảo chính xác
            active_students = len(record.student_ids.filtered(lambda s: s.active))
            if active_students > record.capacity:
                raise ValidationError('Số lượng sinh viên (%d) không được vượt quá sức chứa lớp học (%d)!' % (active_students, record.capacity))

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã lớp phải là duy nhất!'),
    ]

