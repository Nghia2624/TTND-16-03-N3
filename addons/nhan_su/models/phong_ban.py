# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PhongBan(models.Model):
    _name = 'phong_ban'
    _description = 'Bảng chứa thông tin phòng ban'
    _rec_name = 'ten_phong_ban'
    _order = 'ten_phong_ban asc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    ten_phong_ban = fields.Char("Tên phòng ban", required=True)
    
    # Mối quan hệ nhiều-nhiều với nhân viên
    nhan_vien_ids = fields.Many2many(
        'nhan_vien',
        'phong_ban_nhan_vien_rel',
        'phong_ban_id',
        'nhan_vien_id',
        string="Danh sách nhân viên"
    )
    
    # Mối quan hệ phân cấp (phòng ban có thể có phòng ban cha)
    phong_ban_id = fields.Many2one(
        'phong_ban',
        string="Phòng ban cha",
        ondelete='cascade'
    )
    
    phong_ban_con_ids = fields.One2many(
        'phong_ban',
        'phong_ban_id',
        string="Phòng ban con"
    )
    
    # Số lượng nhân viên trong phòng ban
    so_luong_nhan_vien = fields.Integer(
        "Số lượng nhân viên",
        compute="_compute_so_luong_nhan_vien",
        store=True
    )
    
    # Mô tả phòng ban
    mo_ta = fields.Text("Mô tả")
    
    # Trạng thái hoạt động
    trang_thai = fields.Selection(
        [
            ('dang_hoat_dong', 'Đang hoạt động'),
            ('tam_dung', 'Tạm dừng'),
            ('ngung_hoat_dong', 'Ngừng hoạt động')
        ],
        string="Trạng thái",
        default='dang_hoat_dong',
        required=True
    )
    
    # Ngày thành lập
    ngay_thanh_lap = fields.Date("Ngày thành lập")
    
    # Địa chỉ phòng ban
    dia_chi = fields.Text("Địa chỉ")
    
    # Số điện thoại phòng ban
    so_dien_thoai = fields.Char("Số điện thoại")
    
    # Email phòng ban
    email = fields.Char("Email")
    
    # Trưởng phòng (Many2one với nhân viên)
    truong_phong_id = fields.Many2one(
        'nhan_vien',
        string="Trưởng phòng"
    )
    
    @api.depends('nhan_vien_ids', 'nhan_vien_ids.trang_thai_lam_viec')
    def _compute_so_luong_nhan_vien(self):
        """Tính số lượng nhân viên trong phòng ban (đếm cả nhân viên đang làm việc và thử việc)"""
        for record in self:
            # Đếm nhân viên đang làm việc và thử việc
            nhan_vien_dang_lam = record.nhan_vien_ids.filtered(
                lambda x: x.trang_thai_lam_viec in ['dang_lam_viec', 'thu_viec']
            )
            record.so_luong_nhan_vien = len(nhan_vien_dang_lam)
    
    @api.constrains('phong_ban_id')
    def _check_phong_ban_id(self):
        """Kiểm tra không cho phép phòng ban cha là chính nó"""
        for record in self:
            if record.phong_ban_id and record.phong_ban_id.id == record.id:
                raise ValidationError("Phòng ban không thể là phòng ban cha của chính nó")
    
    @api.constrains('truong_phong_id', 'nhan_vien_ids')
    def _check_truong_phong(self):
        """Kiểm tra trưởng phòng phải thuộc danh sách nhân viên của phòng ban
        và đảm bảo chỉ có 1 trưởng phòng trong phòng ban
        """
        for record in self:
            if record.truong_phong_id and record.nhan_vien_ids:
                if record.truong_phong_id not in record.nhan_vien_ids:
                    raise ValidationError(
                        f"Trưởng phòng {record.truong_phong_id.ho_va_ten} phải thuộc danh sách nhân viên của phòng ban {record.ten_phong_ban}"
                    )
                # Kiểm tra trưởng phòng phải đang làm việc
                if record.truong_phong_id.trang_thai_lam_viec not in ['dang_lam_viec', 'thu_viec']:
                    raise ValidationError(
                        f"Trưởng phòng {record.truong_phong_id.ho_va_ten} phải đang làm việc hoặc thử việc"
                    )
                # Kiểm tra trưởng phòng phải có chức vụ trưởng phòng (cấp 4)
                if record.truong_phong_id.chuc_vu_id and record.truong_phong_id.chuc_vu_id.cap_do != '4':
                    raise ValidationError(
                        f"Trưởng phòng {record.truong_phong_id.ho_va_ten} phải có chức vụ cấp 4 (Trưởng phòng). "
                        f"Hiện tại chức vụ là: {record.truong_phong_id.chuc_vu_id.ten_chuc_vu}"
                    )
                # Kiểm tra không có trưởng phòng khác trong cùng phòng ban
                nhan_vien_khac = record.nhan_vien_ids.filtered(
                    lambda x: x.id != record.truong_phong_id.id and
                    x.chuc_vu_id and x.chuc_vu_id.cap_do == '4' and
                    x.trang_thai_lam_viec in ['dang_lam_viec', 'thu_viec']
                )
                if nhan_vien_khac:
                    raise ValidationError(
                        f"Phòng ban {record.ten_phong_ban} đã có trưởng phòng khác là "
                        f"{nhan_vien_khac[0].ho_va_ten}. Mỗi phòng ban chỉ được có 1 trưởng phòng."
                    )
    
    _sql_constraints = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]
    
    @api.model
    def name_get(self):
        """Hiển thị tên phòng ban kèm mã định danh"""
        result = []
        for record in self:
            name = record.ten_phong_ban
            if record.ma_dinh_danh:
                name = f"[{record.ma_dinh_danh}] {name}"
            result.append((record.id, name))
        return result

