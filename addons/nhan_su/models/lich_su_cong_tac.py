# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class LichSuCongTac(models.Model):
    _name = 'lich_su_cong_tac'
    _description = 'Bảng chứa thông tin lịch sử công tác'
    _order = 'ngay_bat_dau desc, ngay_ket_thuc desc'
    _rec_name = 'display_name'

    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên", required=True, ondelete='cascade')
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ", required=True, ondelete='restrict')
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị", ondelete='restrict')
    phong_ban_id = fields.Many2one("phong_ban", string="Phòng ban", ondelete='restrict')
    
    loai_chuc_vu = fields.Selection(
        [
            ("chinh", "Chính"), 
            ("kiem_nhiem", "Kiêm nhiệm")
        ], 
        string="Loại chức vụ", 
        default="chinh",
        required=True
    )
    
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True, default=fields.Date.today)
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    
    trang_thai = fields.Selection(
        [
            ('dang_lam', 'Đang làm'),
            ('ket_thuc', 'Kết thúc'),
            ('chuyen_cong_tac', 'Chuyển công tác')
        ],
        string="Trạng thái",
        default='dang_lam',
        required=True
    )
    
    luong = fields.Float("Lương", digits=(16, 0))
    ghi_chu = fields.Text("Ghi chú")
    
    # Tính số tháng công tác
    so_thang_cong_tac = fields.Integer("Số tháng công tác", compute="_compute_so_thang_cong_tac", store=True)
    
    display_name = fields.Char("Tên hiển thị", compute="_compute_display_name", store=True)
    
    @api.depends('nhan_vien_id', 'chuc_vu_id', 'ngay_bat_dau')
    def _compute_display_name(self):
        """Tạo tên hiển thị cho record"""
        for record in self:
            name_parts = []
            if record.nhan_vien_id:
                name_parts.append(record.nhan_vien_id.ho_va_ten or record.nhan_vien_id.ma_dinh_danh)
            if record.chuc_vu_id:
                name_parts.append(record.chuc_vu_id.ten_chuc_vu)
            if record.ngay_bat_dau:
                name_parts.append(str(record.ngay_bat_dau))
            record.display_name = ' - '.join(name_parts) if name_parts else 'Lịch sử công tác'
    
    @api.depends('ngay_bat_dau', 'ngay_ket_thuc', 'trang_thai')
    def _compute_so_thang_cong_tac(self):
        """Tính số tháng công tác"""
        for record in self:
            if record.ngay_bat_dau:
                # Nếu chưa có ngày kết thúc và đang làm, dùng ngày hiện tại
                end_date = record.ngay_ket_thuc if record.ngay_ket_thuc else fields.Date.today()
                if end_date < record.ngay_bat_dau:
                    record.so_thang_cong_tac = 0
                else:
                    # Tính số tháng chính xác
                    months = (end_date.year - record.ngay_bat_dau.year) * 12 + \
                             (end_date.month - record.ngay_bat_dau.month)
                    # Nếu ngày kết thúc nhỏ hơn ngày bắt đầu trong tháng, giảm 1 tháng
                    if end_date.day < record.ngay_bat_dau.day:
                        months -= 1
                    record.so_thang_cong_tac = max(0, months)
            else:
                record.so_thang_cong_tac = 0
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay(self):
        """Kiểm tra ngày kết thúc phải sau ngày bắt đầu"""
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau:
                if record.ngay_ket_thuc < record.ngay_bat_dau:
                    raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu")
    
    @api.model
    def create(self, vals):
        """Tự động cập nhật chức vụ hiện tại của nhân viên khi tạo lịch sử công tác mới"""
        res = super(LichSuCongTac, self).create(vals)
        # Nếu lịch sử công tác đang làm và là chức vụ chính, cập nhật chức vụ hiện tại
        if res.trang_thai == 'dang_lam' and res.loai_chuc_vu == 'chinh' and res.nhan_vien_id:
            # Kiểm tra xem có lịch sử công tác khác đang làm (chức vụ chính) không
            lich_su_khac = res.nhan_vien_id.lich_su_cong_tac_ids.filtered(
                lambda x: x.trang_thai == 'dang_lam' and 
                         x.loai_chuc_vu == 'chinh' and 
                         x.id != res.id
            )
            # Chỉ cập nhật nếu không có lịch sử khác hoặc lịch sử mới là mới nhất
            if not lich_su_khac or res.ngay_bat_dau >= max(lich_su_khac.mapped('ngay_bat_dau'), default=res.ngay_bat_dau):
                res.nhan_vien_id.write({
                    'chuc_vu_id': res.chuc_vu_id.id,
                    'don_vi_id': res.don_vi_id.id if res.don_vi_id else res.nhan_vien_id.don_vi_id.id,
                })
        return res
    
    def write(self, vals):
        """Cập nhật chức vụ khi thay đổi lịch sử công tác"""
        # Lưu trữ trạng thái cũ để so sánh
        old_trang_thai = {r.id: r.trang_thai for r in self}
        old_loai_chuc_vu = {r.id: r.loai_chuc_vu for r in self}
        
        res = super(LichSuCongTac, self).write(vals)
        
        # Nếu thay đổi trạng thái hoặc chức vụ
        if 'trang_thai' in vals or 'chuc_vu_id' in vals or 'loai_chuc_vu' in vals or 'ngay_bat_dau' in vals:
            for record in self:
                if record.nhan_vien_id:
                    # Nếu lịch sử đang làm và là chức vụ chính
                    if record.trang_thai == 'dang_lam' and record.loai_chuc_vu == 'chinh':
                        # Kiểm tra xem có lịch sử công tác khác đang làm (chức vụ chính) không
                        lich_su_khac = record.nhan_vien_id.lich_su_cong_tac_ids.filtered(
                            lambda x: x.trang_thai == 'dang_lam' and 
                                     x.loai_chuc_vu == 'chinh' and 
                                     x.id != record.id
                        )
                        # Chỉ cập nhật nếu không có lịch sử khác hoặc lịch sử này là mới nhất
                        if not lich_su_khac or record.ngay_bat_dau >= max(lich_su_khac.mapped('ngay_bat_dau'), default=record.ngay_bat_dau):
                            # Tránh vòng lặp: chỉ cập nhật nếu giá trị thực sự thay đổi
                            update_vals = {}
                            if record.nhan_vien_id.chuc_vu_id.id != record.chuc_vu_id.id:
                                update_vals['chuc_vu_id'] = record.chuc_vu_id.id
                            don_vi_id = record.don_vi_id.id if record.don_vi_id else False
                            if (record.nhan_vien_id.don_vi_id.id if record.nhan_vien_id.don_vi_id else False) != don_vi_id:
                                update_vals['don_vi_id'] = don_vi_id
                            
                            if update_vals:
                                record.nhan_vien_id.write(update_vals)
                    
                    # Nếu kết thúc lịch sử công tác (chức vụ chính)
                    elif (old_trang_thai.get(record.id) == 'dang_lam' and 
                          record.trang_thai == 'ket_thuc' and 
                          old_loai_chuc_vu.get(record.id) == 'chinh'):
                        # Tìm lịch sử công tác khác đang làm (chức vụ chính)
                        lich_su_khac = record.nhan_vien_id.lich_su_cong_tac_ids.filtered(
                            lambda x: x.trang_thai == 'dang_lam' and 
                                     x.loai_chuc_vu == 'chinh' and 
                                     x.id != record.id
                        )
                        if lich_su_khac:
                            # Cập nhật với lịch sử mới nhất
                            lich_su_moi_nhat = lich_su_khac.sorted('ngay_bat_dau', reverse=True)[0]
                            record.nhan_vien_id.write({
                                'chuc_vu_id': lich_su_moi_nhat.chuc_vu_id.id,
                                'don_vi_id': lich_su_moi_nhat.don_vi_id.id if lich_su_moi_nhat.don_vi_id else False,
                            })
                        else:
                            # Không còn lịch sử nào đang làm, xóa chức vụ hiện tại
                            record.nhan_vien_id.write({
                                'chuc_vu_id': False,
                                'don_vi_id': False,
                            })
        return res
    
    @api.constrains('nhan_vien_id', 'ngay_bat_dau', 'ngay_ket_thuc', 'trang_thai', 'loai_chuc_vu')
    def _check_trung_lap(self):
        """Kiểm tra không cho trùng lặp thời gian công tác"""
        for record in self:
            if record.trang_thai == 'dang_lam' and record.loai_chuc_vu == 'chinh':
                # Tìm các lịch sử công tác đang làm (chức vụ chính) của cùng nhân viên
                domain = [
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('trang_thai', '=', 'dang_lam'),
                    ('loai_chuc_vu', '=', 'chinh'),
                    ('id', '!=', record.id)
                ]
                
                # Kiểm tra trùng lặp thời gian
                overlapping = self.env['lich_su_cong_tac'].search(domain)
                for overlap in overlapping:
                    # Nếu một trong hai không có ngày kết thúc, coi như trùng (đang làm)
                    if not overlap.ngay_ket_thuc or not record.ngay_ket_thuc:
                        raise ValidationError(
                            f"Nhân viên này đã có lịch sử công tác đang hoạt động từ {overlap.ngay_bat_dau}. "
                            f"Vui lòng kết thúc lịch sử công tác trước đó trước khi tạo mới."
                        )
                    # Kiểm tra khoảng thời gian trùng nhau
                    today = fields.Date.today()
                    record_end = record.ngay_ket_thuc if record.ngay_ket_thuc else today
                    overlap_end = overlap.ngay_ket_thuc if overlap.ngay_ket_thuc else today
                    if (overlap.ngay_bat_dau <= record_end and overlap_end >= record.ngay_bat_dau):
                        raise ValidationError(
                            f"Nhân viên này đã có lịch sử công tác từ {overlap.ngay_bat_dau} "
                            f"đến {overlap.ngay_ket_thuc or 'hiện tại'}. Không thể tạo lịch sử công tác trùng lặp."
                        )
