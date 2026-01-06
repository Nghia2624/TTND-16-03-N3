# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ChungChiBangCap(models.Model):
    _name = 'chung_chi_bang_cap'
    _description = 'Bảng chứa thông tin chứng chỉ bằng cấp'
    _rec_name = 'ten_chung_chi_bang_cap'

    ma_chung_chi_bang_cap = fields.Char("Mã chứng chỉ, bằng cấp", required=True)
    ten_chung_chi_bang_cap = fields.Char("Tên chứng chỉ, bằng cấp", required=True)
    
    _sql_constraints = [
        ('ma_chung_chi_bang_cap_unique', 'unique(ma_chung_chi_bang_cap)', 'Mã chứng chỉ bằng cấp phải là duy nhất')
    ]