from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from . import constants


class BaseModel():
    """模型基类，为每个模型补充创建时间和更新时间"""

    creat_time = db.Column(db.DateTime, default=datetime.now)  # 创建记录时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录更新时间


class User(BaseModel, db.Model):
    """用户"""

    __tablename__ = "ih_user_profile"

    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户姓名
    password = db.Column(db.String(128), nullable=False)  # 加密的密码
    mobile = db.Column(db.String(11), unique=True, nullable=False)  # 手机号
    real_name = db.Column(db.String(32))  # 真实姓名
    id_card = db.Column(db.String(20))  # 身份证号
    avatar_url = db.Column(db.String(128))  # 用户头像路径
    hourse = db.relationship("Hourse", backref="user")  # 用户发布的房屋
    orders = db.relationship("Order", backref="user")  # 用户下的订单

    @property
    def password_hash(self):
        """获取password时调用"""
        raise AttributeError("不可读")

    @password_hash.setter
    def password_hash(self, passwd):
        """
        set时调用
        :param passwd:
        :return:
        """
        self.password = generate_password_hash(passwd)

    def check_password(self, passwd):
        return check_password_hash(self.password, passwd)

    def userinfo_to_dict(self):
        """将个人信息转为字典"""
        auth_dict = {
            "user_id": self.id,
            "name": self.name,
            "avatar_url": self.avatar_url,
        }
        return auth_dict

    def auth_to_dict(self):
        """将实名认证信息转为字典"""
        auth_dict = {
            "user_id":self.id,
            "real_name":self.real_name,
            "id_card":self.id_card,
        }
        return auth_dict


class Area(BaseModel, db.Model):
    """房屋城区"""

    __tablename__ = "ih_area_info"

    id = db.Column(db.Integer, primary_key=True)  # 区域编号
    name = db.Column(db.String(32), nullable=False)  # 区域名
    hourse = db.relationship("Hourse", backref="area")  # 区域房屋

    def to_dict(self):
        """
        将对象转为字典
        :return: 字典
        """
        d = {
            "aid":self.id,
            "aname":self.name,
        }
        return d



# 房屋设施表，建立房屋与设施的多对多关系
hourse_facility = db.Table(
    "ih_hourse_facility",
    db.Column("hourse_id", db.Integer, db.ForeignKey("ih_hourse_info.id"), primary_key=True),  # 房屋编号
    db.Column("facility_id", db.Integer, db.ForeignKey("ih_facility_info.id"), primary_key=True),  # 设施
)


class Hourse(BaseModel, db.Model):
    """房屋信息"""

    __tablename__ = "ih_hourse_info"

    id = db.Column(db.Integer, primary_key=True)  # 房屋编号
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)  # 房屋主人编号
    area_id = db.Column(db.Integer, db.ForeignKey("ih_area_info.id"), nullable=False)  # 归属地
    title = db.Column(db.String(64), nullable=False)  # 标题
    price = db.Column(db.Integer, default=0)  # 单价，单位：分
    address = db.Column(db.String(512), default="")  # 地址
    room_count = db.Column(db.Integer, default=1)  # 房间数
    acreage = db.Column(db.Integer, default=0)  # 房屋面积
    unit = db.Column(db.String(32), default="")  # 房屋单元
    capacity = db.Column(db.Integer, default=1)  # 房屋容纳人数
    beds = db.Column(db.String(64), default="")  # 房屋床铺配置
    deposit = db.Column(db.Integer, default=0)  # 房屋押金
    min_days = db.Column(db.Integer, default=1)  # 最少入住时间
    max_days = db.Column(db.Integer, default=0)  # 最多入住天数  0表示不限制
    order_count = db.Column(db.Integer, default=0)  # 预定完成该房屋订单数
    index_image_url = db.Column(db.String(256), default="")  # 房屋主图片的路径
    facilities = db.relationship("Facility", secondary=hourse_facility)  # 房屋的设施
    image = db.relationship("HourseImage")  # 房屋的图片
    order = db.relationship("Order", backref="hourse")  # 房屋的订单

    def to_basic_dict(self):
        """将基本信息转换为字典数据"""
        house_dict = {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "area_name": self.area.name,
            "img_url": constants.QINIU_URL_DOMAIN + self.index_image_url if self.index_image_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "address": self.address,
            "user_avatar": constants.QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
            "ctime":self.creat_time.strftime("%Y-%m-%d")
        }
        return house_dict

    def to_full_dict(self):
        """将详细信息转换为字典数据"""
        house_dict ={
        "hid": self.id,
        "user_id": self.user_id,
        "user_name": self.user.name,
        "user_avatar": constants.QINIU_URL_DOMAIN + self.user.avatar_url if self.user.avatar_url else "",
        "title": self.title,
        "price": self.price,
        "address": self.address,
        "room_count": self.room_count,
        "acreage": self.acreage,
        "unit": self.unit,
        "capacity": self.capacity,
        "beds": self.beds,
        "deposit": self.deposit,
        "min_days": self.min_days,
        "max_days": self.max_days,
        }

        # 房屋图片
        img_urls = []
        for image in self.image:
            img_urls.append(constants.QINIU_URL_DOMAIN + image.url)
        house_dict["img_urls"] = img_urls

        # 房屋设施
        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        # 评论信息
        comments = []
        orders = Order.query.filter(Order.hourse_id == self.id, Order.status == "COMPLETE", Order.comment != None) \
            .order_by(Order.update_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
            "comment": order.comment,  # 评论的内容
            "user_name": order.user.name if order.user.name != order.user.mobile else "匿名用户",  # 发表评论的用户
            "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")  # 评价的时间

         }
            comments.append(comment)

        house_dict["comments"] = comments
        return house_dict






class Facility(BaseModel, db.Model):
    """设施信息"""
    __tablename__ = "ih_facility_info"

    id = db.Column(db.Integer, primary_key=True)  # 设施编号
    name = db.Column(db.String(32), nullable=False)  # 设施名字


class HourseImage(BaseModel, db.Model):
    """房屋图片"""

    __tablename__ = "ih_hourse_image"

    id = db.Column(db.Integer, primary_key=True)
    hourse_id = db.Column(db.Integer, db.ForeignKey("ih_hourse_info.id"), nullable=False)  # 房屋编号
    url = db.Column(db.String(256), nullable=False)  # 图片路径


class Order(BaseModel, db.Model):
    """订单"""

    __tablename__ = "ih_order_info"

    id = db.Column(db.Integer, primary_key=True)  # 订单编号
    user_id = db.Column(db.Integer, db.ForeignKey("ih_user_profile.id"), nullable=False)  # 订单的用户编号
    hourse_id = db.Column(db.Integer, db.ForeignKey("ih_hourse_info.id"), nullable=False)  # 订单的房间编号
    begin_date = db.Column(db.DateTime, nullable=False)  # 预定的起始时间
    end_date = db.Column(db.DateTime, nullable=False)  # 预定的结束时间
    days = db.Column(db.Integer, nullable=False)  # 预定的天数
    hourse_price = db.Column(db.Integer, nullable=False)  # 房屋的单价
    amount = db.Column(db.Integer, nullable=False)  # 订单的总金额
    status = db.Column(  # 订单的状态
        db.Enum(
            "WAIT_ACCEPT",  # 带接单
            "WAIT_PAYMENT",  # 带支付
            "PAID",  # 已支付
            "WAIT_COMMENT",  # 待评价
            "COMPLETE",  # 已完成
            "CANCELED",  # 已取消
            "REJECTED",  # 已拒单
        ),
        default="WAIT_ACCEPT", index=True)
    comment = db.Column(db.Text)  # 订单的评论信息或拒单理由

    def to_dict(self):
        """将订单信息转换为字典数据"""
        order_dict = {
            "order_id": self.id,
            "title": self.hourse.title,
            "img_url": constants.QINIU_URL_DOMAIN + self.hourse.index_image_url if self.hourse.index_image_url else "",
            "start_date": self.begin_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "ctime": self.creat_time.strftime("%Y-%m-%d"),
            "days": self.days,
            "amount": self.amount,
            "status": self.status,
            "comment": self.comment if self.comment else ""
        }
        return order_dict





