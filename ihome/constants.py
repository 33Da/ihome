#图片验证码redis有效期
IMAGE_CODE_REDIS_EXPIRES = 300

#短信验证码redis有效期
SMS_CODE_REDIS_EXPIRES = 300


#发送短信验证码间隔
SEND_SMS_COOE_INTERVAL = 60

# 登陆超过限制时间
LOGIN_ERROR_FOBID_TIME = 300

# 城区信息缓存时间
AREA_INFO_CACHE_EXPIRES = 7200


# 头像域名
QINIU_URL_DOMAIN = "http://ptu8si4vn.bkt.clouddn.com/"

# 首页幻灯片显示房屋条数
HOME_PAGE_MAX_HOUSES = 5

# 幻灯片缓存时间，一天
HOME_PAGE_DATA_REDIS_EXPIRES = 86400

# 显示房屋评论数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 5


# 房屋一页显示条数
HOUSE_LIST_PAGE_CAPACITY = 5

# 支付宝网关
ALIPAY_URL_PREFIX = "https://openapi.alipaydev.com/gateway.do?"