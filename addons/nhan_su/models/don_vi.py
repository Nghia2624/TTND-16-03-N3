# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DonVi(models.Model):
    _name = 'don_vi'
    _description = 'Bảng chứa thông tin đơn vị'
    _rec_name = 'ten_don_vi'

    ma_don_vi = fields.Char("Mã đơn vị", required=True)
    ten_don_vi = fields.Char("Tên đơn vị", required=True)
    
    _sql_constraints = [
        ('ma_don_vi_unique', 'unique(ma_don_vi)', 'Mã đơn vị phải là duy nhất')
    ]