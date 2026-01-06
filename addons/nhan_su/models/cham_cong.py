# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta


class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Bảng chấm công nhân viên'
    _order = 'ngay_cham_cong desc, nhan_vien_id'
    _rec_name = 'display_name'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên",
        required=True,
        ondelete='cascade'
    )
    
    ngay_cham_cong = fields.Date(
        "Ngày chấm công",
        required=True,
        default=fields.Date.today
    )
    
    gio_vao = fields.Datetime("Giờ vào")
    gio_ra = fields.Datetime("Giờ ra")
    
    # Tính toán thời gian
    so_gio_lam_viec = fields.Float(
        "Số giờ làm việc",
        compute="_compute_so_gio_lam_viec",
        store=True,
        digits=(16, 2)
    )
    
    so_phut_muon = fields.Integer(
        "Số phút muộn",
        compute="_compute_so_phut_muon",
        store=True
    )
    
    so_phut_som = fields.Integer(
        "Số phút về sớm",
        compute="_compute_so_phut_som",
        store=True
    )
    
    # Loại chấm công
    loai_cham_cong = fields.Selection(
        [
            ('diem_danh', 'Điểm danh'),
            ('nghi_phep', 'Nghỉ phép'),
            ('nghi_om', 'Nghỉ ốm'),
            ('nghi_khong_phep', 'Nghỉ không phép'),
            ('cong_tac', 'Công tác'),
            ('nghi_le', 'Nghỉ lễ')
        ],
        string="Loại chấm công",
        default='diem_danh',
        required=True
    )
    
    # Giờ làm việc chuẩn (có thể cấu hình)
    gio_lam_viec_chuan = fields.Float(
        "Giờ làm việc chuẩn (giờ)",
        default=8.0,
        help="Số giờ làm việc chuẩn trong ngày"
    )
    
    gio_vao_chuan = fields.Float(
        "Giờ vào chuẩn",
        default=8.0,
        help="Giờ vào làm việc chuẩn (ví dụ: 8.0 = 8:00 AM)"
    )
    
    gio_ra_chuan = fields.Float(
        "Giờ ra chuẩn",
        default=17.0,
        help="Giờ ra làm việc chuẩn (ví dụ: 17.0 = 5:00 PM)"
    )
    
    # Trạng thái
    trang_thai = fields.Selection(
        [
            ('chua_duyet', 'Chưa duyệt'),
            ('da_duyet', 'Đã duyệt'),
            ('tu_choi', 'Từ chối')
        ],
        string="Trạng thái",
        default='chua_duyet',
        required=True
    )
    
    nguoi_duyet_id = fields.Many2one(
        'res.users',
        string="Người duyệt",
        readonly=True
    )
    
    ngay_duyet = fields.Datetime("Ngày duyệt", readonly=True)
    
    ghi_chu = fields.Text("Ghi chú")
    
    # Tính toán
    display_name = fields.Char(
        "Tên hiển thị",
        compute="_compute_display_name",
        store=True
    )
    
    # Tổng hợp
    tong_so_gio_lam_viec = fields.Float(
        "Tổng số giờ làm việc",
        compute="_compute_tong_so_gio",
        store=True
    )
    
    @api.depends('nhan_vien_id', 'ngay_cham_cong', 'loai_cham_cong')
    def _compute_display_name(self):
        """Tạo tên hiển thị"""
        for record in self:
            name_parts = []
            if record.nhan_vien_id:
                name_parts.append(record.nhan_vien_id.ho_va_ten or record.nhan_vien_id.ma_dinh_danh)
            if record.ngay_cham_cong:
                name_parts.append(str(record.ngay_cham_cong))
            if record.loai_cham_cong:
                loai_dict = dict(record._fields['loai_cham_cong'].selection)
                name_parts.append(loai_dict.get(record.loai_cham_cong, ''))
            record.display_name = ' - '.join(name_parts) if name_parts else 'Chấm công'
    
    @api.depends('gio_vao', 'gio_ra', 'loai_cham_cong', 'ngay_cham_cong')
    def _compute_so_gio_lam_viec(self):
        """Tính số giờ làm việc (chỉ tính khi giờ vào/ra cùng ngày với ngày chấm công)"""
        for record in self:
            if record.loai_cham_cong != 'diem_danh' or not record.gio_vao or not record.gio_ra or not record.ngay_cham_cong:
                record.so_gio_lam_viec = 0.0
            else:
                # Kiểm tra giờ vào và giờ ra phải cùng ngày với ngày chấm công
                if (record.gio_vao.date() == record.ngay_cham_cong and 
                    record.gio_ra.date() == record.ngay_cham_cong):
                    if record.gio_ra > record.gio_vao:
                        delta = record.gio_ra - record.gio_vao
                        record.so_gio_lam_viec = round(delta.total_seconds() / 3600.0, 2)
                    else:
                        record.so_gio_lam_viec = 0.0
                else:
                    # Nếu không cùng ngày, không tính giờ làm việc
                    record.so_gio_lam_viec = 0.0
    
    @api.depends('gio_vao', 'ngay_cham_cong', 'gio_vao_chuan')
    def _compute_so_phut_muon(self):
        """Tính số phút muộn (chỉ tính khi giờ vào cùng ngày với ngày chấm công)"""
        for record in self:
            if record.loai_cham_cong != 'diem_danh' or not record.gio_vao or not record.ngay_cham_cong:
                record.so_phut_muon = 0
            else:
                # Chỉ tính nếu giờ vào cùng ngày với ngày chấm công
                if record.gio_vao.date() == record.ngay_cham_cong:
                    # Tạo datetime chuẩn cho giờ vào (cùng ngày với ngày chấm công)
                    gio_vao_chuan_dt = datetime.combine(
                        record.ngay_cham_cong,
                        datetime.min.time()
                    ) + timedelta(hours=record.gio_vao_chuan)
                    
                    if record.gio_vao > gio_vao_chuan_dt:
                        delta = record.gio_vao - gio_vao_chuan_dt
                        record.so_phut_muon = int(delta.total_seconds() / 60)
                    else:
                        record.so_phut_muon = 0
                else:
                    record.so_phut_muon = 0
    
    @api.depends('gio_ra', 'ngay_cham_cong', 'gio_ra_chuan')
    def _compute_so_phut_som(self):
        """Tính số phút về sớm (chỉ tính khi giờ ra cùng ngày với ngày chấm công)"""
        for record in self:
            if record.loai_cham_cong != 'diem_danh' or not record.gio_ra or not record.ngay_cham_cong:
                record.so_phut_som = 0
            else:
                # Chỉ tính nếu giờ ra cùng ngày với ngày chấm công
                if record.gio_ra.date() == record.ngay_cham_cong:
                    # Tạo datetime chuẩn cho giờ ra (cùng ngày với ngày chấm công)
                    gio_ra_chuan_dt = datetime.combine(
                        record.ngay_cham_cong,
                        datetime.min.time()
                    ) + timedelta(hours=record.gio_ra_chuan)
                    
                    if record.gio_ra < gio_ra_chuan_dt:
                        delta = gio_ra_chuan_dt - record.gio_ra
                        record.so_phut_som = int(delta.total_seconds() / 60)
                    else:
                        record.so_phut_som = 0
                else:
                    record.so_phut_som = 0
    
    @api.depends('so_gio_lam_viec', 'loai_cham_cong')
    def _compute_tong_so_gio(self):
        """Tính tổng số giờ làm việc"""
        for record in self:
            # Chỉ tính cho điểm danh
            if record.loai_cham_cong == 'diem_danh':
                record.tong_so_gio_lam_viec = record.so_gio_lam_viec
            else:
                record.tong_so_gio_lam_viec = 0.0
    
    @api.constrains('gio_vao', 'gio_ra', 'ngay_cham_cong', 'loai_cham_cong')
    def _check_gio(self):
        """Kiểm tra giờ vào và giờ ra"""
        for record in self:
            if record.loai_cham_cong == 'diem_danh':
                if not record.gio_vao:
                    raise ValidationError("Vui lòng nhập giờ vào khi điểm danh")
                if record.gio_ra:
                    if record.gio_ra <= record.gio_vao:
                        raise ValidationError("Giờ ra phải sau giờ vào")
                    if record.gio_ra.date() != record.ngay_cham_cong:
                        raise ValidationError("Giờ ra phải cùng ngày với ngày chấm công")
                if record.gio_vao.date() != record.ngay_cham_cong:
                    raise ValidationError("Giờ vào phải cùng ngày với ngày chấm công")
    
    @api.constrains('nhan_vien_id', 'ngay_cham_cong', 'loai_cham_cong')
    def _check_trung_lap(self):
        """Kiểm tra không cho trùng lặp chấm công trong cùng ngày"""
        for record in self:
            if record.loai_cham_cong == 'diem_danh':
                domain = [
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_cham_cong', '=', record.ngay_cham_cong),
                    ('loai_cham_cong', '=', 'diem_danh'),
                    ('id', '!=', record.id)
                ]
                existing = self.env['cham_cong'].search(domain)
                if existing:
                    raise ValidationError(
                        "Nhân viên này đã được chấm công điểm danh trong ngày này"
                    )
    
    @api.constrains('nhan_vien_id', 'ngay_cham_cong')
    def _check_nhan_vien_dang_lam_viec(self):
        """Kiểm tra nhân viên phải đang làm việc mới được chấm công"""
        for record in self:
            if record.nhan_vien_id:
                if record.nhan_vien_id.trang_thai_lam_viec not in ['dang_lam_viec', 'thu_viec']:
                    raise ValidationError(
                        f"Nhân viên {record.nhan_vien_id.ho_va_ten} đang ở trạng thái "
                        f"{dict(record.nhan_vien_id._fields['trang_thai_lam_viec'].selection).get(record.nhan_vien_id.trang_thai_lam_viec)}. "
                        f"Chỉ nhân viên đang làm việc hoặc thử việc mới được chấm công."
                    )
    
    def action_duyet(self):
        """Duyệt chấm công"""
        for record in self:
            if record.trang_thai != 'chua_duyet':
                raise ValidationError("Chỉ có thể duyệt chấm công ở trạng thái chưa duyệt")
            record.write({
                'trang_thai': 'da_duyet',
                'nguoi_duyet_id': self.env.user.id,
                'ngay_duyet': fields.Datetime.now()
            })
        return True
    
    def action_tu_choi(self):
        """Từ chối chấm công"""
        for record in self:
            if record.trang_thai != 'chua_duyet':
                raise ValidationError("Chỉ có thể từ chối chấm công ở trạng thái chưa duyệt")
            record.write({
                'trang_thai': 'tu_choi',
                'nguoi_duyet_id': self.env.user.id,
                'ngay_duyet': fields.Datetime.now()
            })
        return True
    
    # Note: SQL constraint được xử lý trong _check_trung_lap

