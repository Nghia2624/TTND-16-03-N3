# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Bảng chứa thông tin chức vụ'
    _rec_name = 'ten_chuc_vu'
    _order = 'cap_do asc, ten_chuc_vu asc'

    ma_chuc_vu = fields.Char("Mã chức vụ", required=True)
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True)
    
    # Thông tin bổ sung
    mo_ta = fields.Text("Mô tả")
    
    # Mức lương
    muc_luong_toi_thieu = fields.Float("Mức lương tối thiểu", digits=(16, 0))
    muc_luong_toi_da = fields.Float("Mức lương tối đa", digits=(16, 0))
    
    # Cấp độ chức vụ
    cap_do = fields.Selection(
        [
            ('1', 'Cấp 1 - Nhân viên'),
            ('2', 'Cấp 2 - Chuyên viên'),
            ('3', 'Cấp 3 - Trưởng nhóm'),
            ('4', 'Cấp 4 - Trưởng phòng'),
            ('5', 'Cấp 5 - Giám đốc'),
        ],
        string="Cấp độ",
        default='1',
        required=True
    )
    
    # Trạng thái
    trang_thai = fields.Selection(
        [
            ('dang_su_dung', 'Đang sử dụng'),
            ('ngung_su_dung', 'Ngừng sử dụng')
        ],
        string="Trạng thái",
        default='dang_su_dung',
        required=True
    )
    
    # Mối quan hệ
    nhan_vien_ids = fields.One2many(
        'nhan_vien',
        'chuc_vu_id',
        string="Danh sách nhân viên"
    )
    
    so_luong_nhan_vien = fields.Integer(
        "Số lượng nhân viên",
        compute="_compute_so_luong_nhan_vien",
        store=True
    )
    
    lich_su_cong_tac_ids = fields.One2many(
        'lich_su_cong_tac',
        'chuc_vu_id',
        string="Lịch sử công tác"
    )
    
    @api.depends('nhan_vien_ids', 'nhan_vien_ids.trang_thai_lam_viec')
    def _compute_so_luong_nhan_vien(self):
        """Tính số lượng nhân viên có chức vụ này (đếm cả nhân viên đang làm việc và thử việc)"""
        for record in self:
            # Đếm nhân viên đang làm việc và thử việc
            nhan_vien_dang_lam = record.nhan_vien_ids.filtered(
                lambda x: x.trang_thai_lam_viec in ['dang_lam_viec', 'thu_viec']
            )
            record.so_luong_nhan_vien = len(nhan_vien_dang_lam)
    
    @api.constrains('muc_luong_toi_thieu', 'muc_luong_toi_da')
    def _check_muc_luong(self):
        """Kiểm tra mức lương tối đa phải lớn hơn tối thiểu"""
        for record in self:
            if record.muc_luong_toi_da and record.muc_luong_toi_thieu:
                if record.muc_luong_toi_da < record.muc_luong_toi_thieu:
                    raise ValidationError("Mức lương tối đa phải lớn hơn mức lương tối thiểu")
    
    _sql_constraints = [
        ('ma_chuc_vu_unique', 'unique(ma_chuc_vu)', 'Mã chức vụ phải là duy nhất')
    ]