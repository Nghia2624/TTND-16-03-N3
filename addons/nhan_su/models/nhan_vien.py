# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    so_bhxh = fields.Char("Số BHXH")
    dia_chi = fields.Text("Địa chỉ")
    luong = fields.Float("Lương", digits=(16, 0))
    
    # Thông tin công việc
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ hiện tại")
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị hiện tại")
    ngay_vao_lam = fields.Date("Ngày vào làm")
    so_nam_cong_tac = fields.Integer("Số năm công tác", compute="_compute_so_nam_cong_tac", store=True)
    
    # Trạng thái làm việc
    trang_thai_lam_viec = fields.Selection(
        [
            ('dang_lam_viec', 'Đang làm việc'),
            ('nghi_viec', 'Nghỉ việc'),
            ('nghi_phep', 'Nghỉ phép'),
            ('thu_viec', 'Thử việc')
        ],
        string="Trạng thái làm việc",
        default='dang_lam_viec',
        required=True
    )
    
    # Mối quan hệ
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách lịch sử công tác")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách chứng chỉ bằng cấp")
    # Mối quan hệ nhiều-nhiều với phòng ban
    phong_ban_ids = fields.Many2many(
        'phong_ban',
        'phong_ban_nhan_vien_rel',
        'nhan_vien_id',
        'phong_ban_id',
        string="Danh sách phòng ban"
    )
    # Mối quan hệ với chấm công
    cham_cong_ids = fields.One2many(
        'cham_cong',
        'nhan_vien_id',
        string="Lịch sử chấm công"
    )
    
    so_nguoi_bang_tuoi = fields.Integer("Số người bằng tuổi", 
                                        compute="_compute_so_nguoi_bang_tuoi",
                                        store=True
                                        )
    
    # Thống kê chấm công
    tong_so_ngay_cham_cong = fields.Integer(
        "Tổng số ngày chấm công",
        compute="_compute_thong_ke_cham_cong",
        store=True
    )
    
    tong_so_gio_lam_viec = fields.Float(
        "Tổng số giờ làm việc",
        compute="_compute_thong_ke_cham_cong",
        store=True,
        digits=(16, 2)
    )
    
    so_ngay_nghi_phep = fields.Integer(
        "Số ngày nghỉ phép",
        compute="_compute_thong_ke_cham_cong",
        store=True
    )
    
    so_ngay_muon = fields.Integer(
        "Số ngày muộn",
        compute="_compute_thong_ke_cham_cong",
        store=True
    )
    
    # Lịch sử công tác hiện tại
    lich_su_cong_tac_hien_tai_id = fields.Many2one(
        'lich_su_cong_tac',
        string="Lịch sử công tác hiện tại",
        compute="_compute_lich_su_cong_tac_hien_tai",
        store=True
    )
    
    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['nhan_vien'].search(
                    [
                        ('tuoi', '=', record.tuoi),
                        ('ma_dinh_danh', '!=', record.ma_dinh_danh)
                    ]
                )
                record.so_nguoi_bang_tuoi = len(records)
            else:
                record.so_nguoi_bang_tuoi = 0
    _sql_constrains = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            parts = [part for part in [record.ho_ten_dem, record.ten] if part]
            record.ho_va_ten = ' '.join(parts) if parts else ''
    
    def _generate_ma_dinh_danh(self, ho_va_ten, ngay_sinh, exclude_id=None):
        """Helper method để tạo mã định danh từ họ tên và ngày sinh
        Nếu mã bị trùng, sẽ tự động thêm số thứ tự
        """
        if ho_va_ten and ngay_sinh:
            # Lấy chữ cái đầu của mỗi từ trong họ và tên (viết hoa)
            words = ho_va_ten.strip().split()
            chu_cai_dau = ''.join([word[0].upper() for word in words if word])
            
            # Format ngày sinh: DDMMYYYY
            if isinstance(ngay_sinh, str):
                ngay_sinh = fields.Date.from_string(ngay_sinh)
            ngay_sinh_str = ngay_sinh.strftime('%d%m%Y')
            
            base_ma = chu_cai_dau + ngay_sinh_str
        elif ho_va_ten:
            # Nếu chỉ có họ tên, chỉ lấy chữ cái đầu
            words = ho_va_ten.strip().split()
            chu_cai_dau = ''.join([word[0].upper() for word in words if word])
            base_ma = chu_cai_dau
        else:
            return ''
        
        # Kiểm tra trùng lặp và thêm số thứ tự nếu cần
        ma_dinh_danh = base_ma
        counter = 1
        while True:
            domain = [('ma_dinh_danh', '=', ma_dinh_danh)]
            if exclude_id:
                domain.append(('id', '!=', exclude_id))
            existing = self.env['nhan_vien'].search(domain, limit=1)
            if not existing:
                break
            # Nếu trùng, thêm số thứ tự
            ma_dinh_danh = f"{base_ma}{counter}"
            counter += 1
            # Giới hạn số lần thử để tránh vòng lặp vô hạn
            if counter > 999:
                # Nếu vẫn trùng sau 999 lần, thêm timestamp
                import time
                ma_dinh_danh = f"{base_ma}{int(time.time())}"
                break
        
        return ma_dinh_danh
    
    @api.onchange("ho_ten_dem", "ten", "ngay_sinh")
    def _onchange_ma_dinh_danh(self):
        """Tự động cập nhật mã định danh khi thay đổi họ tên hoặc ngày sinh"""
        for record in self:
            # Tính lại ho_va_ten để đảm bảo có giá trị mới nhất
            parts = [part for part in [record.ho_ten_dem, record.ten] if part]
            ho_va_ten = ' '.join(parts) if parts else ''
            
            if ho_va_ten or record.ngay_sinh:
                # Sử dụng exclude_id để tránh kiểm tra chính record hiện tại khi đang chỉnh sửa
                exclude_id = record.id if record.id else None
                record.ma_dinh_danh = self._generate_ma_dinh_danh(ho_va_ten, record.ngay_sinh, exclude_id)
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        """Tính tuổi chính xác dựa trên ngày sinh
        Tuổi được tính theo cách: năm hiện tại - năm sinh
        Nếu chưa đến sinh nhật trong năm nay, giảm 1 tuổi
        """
        for record in self:
            if record.ngay_sinh:
                today = fields.Date.today()
                # Kiểm tra ngày sinh không được là tương lai
                if record.ngay_sinh > today:
                    record.tuoi = 0
                    continue
                
                years = today.year - record.ngay_sinh.year
                # Nếu chưa đến sinh nhật trong năm nay, giảm 1 tuổi
                # Ví dụ: sinh ngày 15/03/2000, hôm nay là 10/03/2024 -> chưa đủ 24 tuổi
                if today.month < record.ngay_sinh.month or \
                   (today.month == record.ngay_sinh.month and today.day < record.ngay_sinh.day):
                    years -= 1
                record.tuoi = max(0, years)
            else:
                record.tuoi = 0

    @api.depends('ngay_vao_lam')
    def _compute_so_nam_cong_tac(self):
        """Tính số năm công tác"""
        for record in self:
            if record.ngay_vao_lam:
                today = fields.Date.today()
                years = today.year - record.ngay_vao_lam.year
                # Nếu chưa đến ngày kỷ niệm trong năm nay, giảm 1 năm
                if today.month < record.ngay_vao_lam.month or \
                   (today.month == record.ngay_vao_lam.month and today.day < record.ngay_vao_lam.day):
                    years -= 1
                record.so_nam_cong_tac = max(0, years)
            else:
                record.so_nam_cong_tac = 0
    
    @api.constrains('ngay_sinh')
    def _check_ngay_sinh(self):
        """Kiểm tra ngày sinh hợp lệ và tuổi đủ 18"""
        for record in self:
            if record.ngay_sinh:
                today = fields.Date.today()
                
                # Kiểm tra ngày sinh không được là tương lai
                if record.ngay_sinh > today:
                    raise ValidationError("Ngày sinh không thể là ngày trong tương lai")
                
                # Tính tuổi chính xác
                years = today.year - record.ngay_sinh.year
                if today.month < record.ngay_sinh.month or \
                   (today.month == record.ngay_sinh.month and today.day < record.ngay_sinh.day):
                    years -= 1
                
                # Kiểm tra tuổi tối thiểu (18 tuổi theo luật lao động Việt Nam)
                if years < 18:
                    raise ValidationError(
                        f"Tuổi của nhân viên phải đủ 18 tuổi. "
                        f"Ngày sinh {record.ngay_sinh} cho thấy tuổi hiện tại là {years} tuổi."
                    )
                
                # Kiểm tra tuổi hợp lý (không quá 100 tuổi)
                if years > 100:
                    raise ValidationError(
                        f"Ngày sinh không hợp lệ. Tuổi tính được là {years} tuổi, "
                        f"vượt quá giới hạn hợp lý (100 tuổi)."
                    )
    
    @api.constrains('tuoi')
    def _check_tuoi(self):
        """Kiểm tra tuổi (backup constraint nếu computed field chưa được tính)"""
        for record in self:
            if record.tuoi and record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")
    
    @api.depends('cham_cong_ids', 'cham_cong_ids.so_gio_lam_viec', 'cham_cong_ids.loai_cham_cong', 'cham_cong_ids.so_phut_muon', 'cham_cong_ids.trang_thai', 'cham_cong_ids.ngay_cham_cong')
    def _compute_thong_ke_cham_cong(self):
        """Tính toán thống kê chấm công"""
        for record in self:
            cham_cong_da_duyet = record.cham_cong_ids.filtered(
                lambda x: x.trang_thai == 'da_duyet'
            )
            
            # Tổng số ngày chấm công (điểm danh đã duyệt)
            diem_danh = cham_cong_da_duyet.filtered(
                lambda x: x.loai_cham_cong == 'diem_danh'
            )
            record.tong_so_ngay_cham_cong = len(diem_danh)
            
            # Tổng số giờ làm việc
            record.tong_so_gio_lam_viec = sum(diem_danh.mapped('so_gio_lam_viec'))
            
            # Số ngày nghỉ phép
            nghi_phep = cham_cong_da_duyet.filtered(
                lambda x: x.loai_cham_cong == 'nghi_phep'
            )
            record.so_ngay_nghi_phep = len(nghi_phep)
            
            # Số ngày muộn (có muộn > 0)
            ngay_muon = diem_danh.filtered(lambda x: x.so_phut_muon > 0)
            record.so_ngay_muon = len(ngay_muon)
    
    @api.depends('lich_su_cong_tac_ids', 'lich_su_cong_tac_ids.trang_thai', 'lich_su_cong_tac_ids.loai_chuc_vu', 'lich_su_cong_tac_ids.ngay_bat_dau')
    def _compute_lich_su_cong_tac_hien_tai(self):
        """Tìm lịch sử công tác hiện tại (chức vụ chính đang làm)"""
        for record in self:
            # Tìm lịch sử công tác đang làm và là chức vụ chính
            lich_su_hien_tai = record.lich_su_cong_tac_ids.filtered(
                lambda x: x.trang_thai == 'dang_lam' and x.loai_chuc_vu == 'chinh'
            )
            if lich_su_hien_tai:
                # Lấy lịch sử mới nhất (ngày bắt đầu gần nhất)
                record.lich_su_cong_tac_hien_tai_id = lich_su_hien_tai.sorted('ngay_bat_dau', reverse=True)[0]
            else:
                record.lich_su_cong_tac_hien_tai_id = False
    
    @api.model
    def create(self, vals):
        """Tự động tạo lịch sử công tác khi tạo nhân viên mới"""
        # Tự động tạo ma_dinh_danh nếu chưa có hoặc cần cập nhật
        if 'ma_dinh_danh' not in vals or not vals.get('ma_dinh_danh'):
            ho_ten_dem = vals.get('ho_ten_dem', '')
            ten = vals.get('ten', '')
            ngay_sinh = vals.get('ngay_sinh')
            
            if ho_ten_dem or ten:
                parts = [part for part in [ho_ten_dem, ten] if part]
                ho_va_ten = ' '.join(parts) if parts else ''
                if ngay_sinh:
                    ngay_sinh = fields.Date.from_string(ngay_sinh) if isinstance(ngay_sinh, str) else ngay_sinh
                # Khi create, không có exclude_id vì record chưa tồn tại
                ma_dinh_danh = self._generate_ma_dinh_danh(ho_va_ten, ngay_sinh, exclude_id=None)
                if ma_dinh_danh:
                    vals['ma_dinh_danh'] = ma_dinh_danh
        
        res = super(NhanVien, self).create(vals)
        # Nếu có chức vụ và ngày vào làm, tạo lịch sử công tác
        # Chỉ tạo nếu chưa có lịch sử công tác nào
        if res.chuc_vu_id and res.ngay_vao_lam and not res.lich_su_cong_tac_ids:
            self.env['lich_su_cong_tac'].create({
                'nhan_vien_id': res.id,
                'chuc_vu_id': res.chuc_vu_id.id,
                'don_vi_id': res.don_vi_id.id if res.don_vi_id else False,
                'ngay_bat_dau': res.ngay_vao_lam,
                'trang_thai': 'dang_lam',
                'loai_chuc_vu': 'chinh',
                'luong': res.luong if res.luong else False,
            })
        return res
    
    def write(self, vals):
        """Đồng bộ chức vụ và lịch sử công tác"""
        # Lưu trữ giá trị cũ trước khi write
        old_chuc_vu_ids = {r.id: r.chuc_vu_id.id if r.chuc_vu_id else False for r in self}
        old_don_vi_ids = {r.id: r.don_vi_id.id if r.don_vi_id else False for r in self}
        
        res = super(NhanVien, self).write(vals)
        
        # Tự động cập nhật truong_phong_id trong phòng ban khi gán chức vụ trưởng phòng
        if 'chuc_vu_id' in vals or 'phong_ban_ids' in vals:
            for record in self:
                if record.chuc_vu_id and record.chuc_vu_id.cap_do == '4' and record.phong_ban_ids:
                    # Nếu nhân viên có chức vụ trưởng phòng và thuộc phòng ban
                    for phong_ban in record.phong_ban_ids:
                        # Chỉ cập nhật nếu phòng ban chưa có trưởng phòng hoặc trưởng phòng hiện tại không phải là nhân viên này
                        if not phong_ban.truong_phong_id or phong_ban.truong_phong_id.id != record.id:
                            # Kiểm tra xem có trưởng phòng khác không
                            nhan_vien_khac = phong_ban.nhan_vien_ids.filtered(
                                lambda x: x.id != record.id and
                                x.chuc_vu_id and x.chuc_vu_id.cap_do == '4' and
                                x.trang_thai_lam_viec in ['dang_lam_viec', 'thu_viec']
                            )
                            if not nhan_vien_khac:
                                # Tự động gán làm trưởng phòng
                                phong_ban.write({'truong_phong_id': record.id})
        
        # Cập nhật ma_dinh_danh sau khi write nếu cần
        if ('ho_ten_dem' in vals or 'ten' in vals or 'ngay_sinh' in vals) and 'ma_dinh_danh' not in vals:
            records_to_update = []
            for record in self:
                # Lấy giá trị mới sau khi write
                ho_ten_dem = vals.get('ho_ten_dem', record.ho_ten_dem or '')
                ten = vals.get('ten', record.ten or '')
                ngay_sinh = vals.get('ngay_sinh', record.ngay_sinh)
                
                if ngay_sinh and isinstance(ngay_sinh, str):
                    ngay_sinh = fields.Date.from_string(ngay_sinh)
                
                if ho_ten_dem or ten:
                    parts = [part for part in [ho_ten_dem, ten] if part]
                    ho_va_ten = ' '.join(parts) if parts else ''
                    # Sử dụng exclude_id để tránh kiểm tra chính record hiện tại
                    ma_dinh_danh = self._generate_ma_dinh_danh(ho_va_ten, ngay_sinh, exclude_id=record.id)
                    if ma_dinh_danh and record.ma_dinh_danh != ma_dinh_danh:
                        records_to_update.append((record, ma_dinh_danh))
            
            # Cập nhật tất cả records cùng lúc để tránh gọi write nhiều lần
            if records_to_update:
                for record, ma_dinh_danh in records_to_update:
                    super(NhanVien, record).write({'ma_dinh_danh': ma_dinh_danh})
        
        for record in self:
            # Nếu thay đổi chức vụ, cập nhật lịch sử công tác hiện tại
            if 'chuc_vu_id' in vals:
                chuc_vu_moi = vals.get('chuc_vu_id')
                chuc_vu_cu = old_chuc_vu_ids.get(record.id)
                
                # Chỉ xử lý nếu chức vụ thực sự thay đổi và có chức vụ mới
                if chuc_vu_moi and chuc_vu_moi != chuc_vu_cu:
                    # Tìm lịch sử công tác đang làm (chức vụ chính)
                    lich_su_dang_lam = record.lich_su_cong_tac_ids.filtered(
                        lambda x: x.trang_thai == 'dang_lam' and x.loai_chuc_vu == 'chinh'
                    )
                    
                    if lich_su_dang_lam:
                        # Kết thúc lịch sử cũ (ngày hôm qua)
                        ngay_ket_thuc = fields.Date.today() - timedelta(days=1)
                        lich_su_dang_lam[0].write({
                            'trang_thai': 'ket_thuc',
                            'ngay_ket_thuc': ngay_ket_thuc
                        })
                    
                    # Tạo lịch sử mới với chức vụ mới (bắt đầu từ hôm nay)
                    ngay_bat_dau = fields.Date.today()
                    don_vi_id = vals.get('don_vi_id') if 'don_vi_id' in vals else (record.don_vi_id.id if record.don_vi_id else False)
                    self.env['lich_su_cong_tac'].create({
                        'nhan_vien_id': record.id,
                        'chuc_vu_id': chuc_vu_moi,
                        'don_vi_id': don_vi_id,
                        'ngay_bat_dau': ngay_bat_dau,
                        'trang_thai': 'dang_lam',
                        'loai_chuc_vu': 'chinh',
                        'luong': vals.get('luong', record.luong) if vals.get('luong') or record.luong else False,
                    })
            
            # Nếu chỉ thay đổi đơn vị (không thay đổi chức vụ), cập nhật lịch sử hiện tại
            elif 'don_vi_id' in vals and 'chuc_vu_id' not in vals:
                don_vi_moi = vals.get('don_vi_id')
                don_vi_cu = old_don_vi_ids.get(record.id)
                
                # Chỉ xử lý nếu đơn vị thực sự thay đổi
                if don_vi_moi != don_vi_cu:
                    # Tìm lịch sử công tác đang làm (chức vụ chính)
                    lich_su_dang_lam = record.lich_su_cong_tac_ids.filtered(
                        lambda x: x.trang_thai == 'dang_lam' and x.loai_chuc_vu == 'chinh'
                    )
                    
                    if lich_su_dang_lam:
                        # Cập nhật đơn vị cho lịch sử hiện tại
                        lich_su_dang_lam[0].write({
                            'don_vi_id': don_vi_moi if don_vi_moi else False
                        })
            
            # Nếu thay đổi ngày vào làm
            if 'ngay_vao_lam' in vals and vals.get('ngay_vao_lam'):
                if not record.lich_su_cong_tac_ids and record.chuc_vu_id:
                    # Chưa có lịch sử, tạo mới
                    self.env['lich_su_cong_tac'].create({
                        'nhan_vien_id': record.id,
                        'chuc_vu_id': record.chuc_vu_id.id,
                        'don_vi_id': record.don_vi_id.id if record.don_vi_id else False,
                        'ngay_bat_dau': vals.get('ngay_vao_lam'),
                        'trang_thai': 'dang_lam',
                        'loai_chuc_vu': 'chinh',
                        'luong': record.luong if record.luong else False,
                    })
                else:
                    # Đã có lịch sử, cập nhật lịch sử đầu tiên (lịch sử công tác ban đầu)
                    lich_su_dau_tien = record.lich_su_cong_tac_ids.sorted('ngay_bat_dau')[0] if record.lich_su_cong_tac_ids else False
                    if lich_su_dau_tien:
                        lich_su_dau_tien.write({
                            'ngay_bat_dau': vals.get('ngay_vao_lam')
                        })
            
            # Nếu thay đổi trạng thái làm việc
            if 'trang_thai_lam_viec' in vals:
                if vals['trang_thai_lam_viec'] == 'nghi_viec':
                    # Kết thúc tất cả lịch sử công tác đang làm
                    lich_su_dang_lam = record.lich_su_cong_tac_ids.filtered(
                        lambda x: x.trang_thai == 'dang_lam'
                    )
                    lich_su_dang_lam.write({
                        'trang_thai': 'ket_thuc',
                        'ngay_ket_thuc': fields.Date.today()
                    })
        
        return res
    
    @api.constrains('chuc_vu_id', 'phong_ban_ids')
    def _check_chuc_vu_phong_ban(self):
        """Kiểm tra ràng buộc chức vụ trong phòng ban:
        - Mỗi phòng ban chỉ có 1 trưởng phòng (chức vụ cấp 4)
        - Mỗi phòng ban chỉ có 1 phó phòng (nếu có chức vụ phó phòng)
        """
        for record in self:
            if not record.chuc_vu_id or not record.phong_ban_ids:
                continue
            
            # Chỉ kiểm tra với nhân viên đang làm việc hoặc thử việc
            if record.trang_thai_lam_viec not in ['dang_lam_viec', 'thu_viec']:
                continue
            
            # Kiểm tra chức vụ trưởng phòng (cấp 4)
            if record.chuc_vu_id.cap_do == '4':
                for phong_ban in record.phong_ban_ids:
                    # Tìm các nhân viên khác có chức vụ trưởng phòng trong cùng phòng ban
                    nhan_vien_khac = self.env['nhan_vien'].search([
                        ('phong_ban_ids', 'in', [phong_ban.id]),
                        ('chuc_vu_id.cap_do', '=', '4'),
                        ('trang_thai_lam_viec', 'in', ['dang_lam_viec', 'thu_viec']),
                        ('id', '!=', record.id)
                    ])
                    if nhan_vien_khac:
                        raise ValidationError(
                            f"Phòng ban {phong_ban.ten_phong_ban} đã có trưởng phòng là "
                            f"{nhan_vien_khac[0].ho_va_ten}. Mỗi phòng ban chỉ được có 1 trưởng phòng."
                        )
            
            # Kiểm tra chức vụ phó phòng (tên chức vụ chứa "Phó phòng" hoặc "Phó Phòng")
            ten_chuc_vu_lower = record.chuc_vu_id.ten_chuc_vu.lower() if record.chuc_vu_id.ten_chuc_vu else ''
            if 'phó phòng' in ten_chuc_vu_lower or 'pho phong' in ten_chuc_vu_lower:
                for phong_ban in record.phong_ban_ids:
                    # Tìm các nhân viên khác có chức vụ phó phòng trong cùng phòng ban
                    nhan_vien_khac = self.env['nhan_vien'].search([
                        ('phong_ban_ids', 'in', [phong_ban.id]),
                        ('chuc_vu_id.ten_chuc_vu', 'ilike', '%phó phòng%'),
                        ('trang_thai_lam_viec', 'in', ['dang_lam_viec', 'thu_viec']),
                        ('id', '!=', record.id)
                    ])
                    if nhan_vien_khac:
                        raise ValidationError(
                            f"Phòng ban {phong_ban.ten_phong_ban} đã có phó phòng là "
                            f"{nhan_vien_khac[0].ho_va_ten}. Mỗi phòng ban chỉ được có 1 phó phòng."
                        )
    
    @api.constrains('ngay_vao_lam', 'ngay_sinh')
    def _check_ngay_vao_lam(self):
        """Kiểm tra ngày vào làm phải sau ngày sinh"""
        for record in self:
            if record.ngay_vao_lam and record.ngay_sinh:
                if record.ngay_vao_lam < record.ngay_sinh:
                    raise ValidationError("Ngày vào làm không thể trước ngày sinh")
