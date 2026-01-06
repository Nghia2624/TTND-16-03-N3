# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'
    _order = 'name'

    name = fields.Char(string='Họ và tên', required=True, index=True)
    code = fields.Char(string='Mã sinh viên', required=True, index=True)
    email = fields.Char(string='Email', index=True)
    phone = fields.Char(string='Số điện thoại')
    birthday = fields.Date(string='Ngày sinh')
    age = fields.Integer(string='Tuổi', compute='_compute_age', store=False)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', default='male', index=True)
    address = fields.Text(string='Địa chỉ')
    classroom_id = fields.Many2one('student.classroom', string='Lớp học', required=True, ondelete='restrict', index=True)
    faculty_id = fields.Many2one('student.faculty', string='Khoa', related='classroom_id.faculty_id', store=True, readonly=True, index=True)
    active = fields.Boolean(string='Hoạt động', default=True)
    image = fields.Binary(string='Ảnh đại diện')

    @api.depends('birthday')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.birthday:
                record.age = today.year - record.birthday.year - ((today.month, today.day) < (record.birthday.month, record.birthday.day))
            else:
                record.age = 0

    @api.constrains('email')
    def _check_email(self):
        import re
        for record in self:
            if record.email:
                # Kiểm tra format email cơ bản
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.email):
                    raise ValidationError('Email không hợp lệ! Vui lòng nhập đúng định dạng email (ví dụ: name@example.com)')

    @api.constrains('birthday')
    def _check_birthday(self):
        today = date.today()
        for record in self:
            if record.birthday:
                if record.birthday > today:
                    raise ValidationError('Ngày sinh không thể là ngày trong tương lai!')
                # Kiểm tra tuổi hợp lý (ít nhất 15 tuổi, không quá 100 tuổi)
                age = today.year - record.birthday.year - ((today.month, today.day) < (record.birthday.month, record.birthday.day))
                if age < 15:
                    raise ValidationError('Tuổi sinh viên phải ít nhất 15 tuổi!')
                if age > 100:
                    raise ValidationError('Ngày sinh không hợp lệ!')

    @api.constrains('classroom_id', 'active')
    def _check_classroom_capacity(self):
        for record in self:
            if record.classroom_id and record.active:
                # Đếm số sinh viên active trong lớp (bao gồm cả record hiện tại)
                active_students = record.classroom_id.student_ids.filtered(lambda s: s.active)
                if len(active_students) > record.classroom_id.capacity:
                    raise ValidationError('Lớp học đã đầy! Không thể thêm sinh viên mới. (Sức chứa: %d, Đã có: %d)' % (record.classroom_id.capacity, len(active_students) - 1))

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã sinh viên phải là duy nhất!'),
    ]

