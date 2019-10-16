"""写配置信息"""
import redis

class Config():
    DEBUG = True

    SECRET_KEY = "XVDGEFDR+*DKMKNdDdXKsdD"

    #数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:root@127.0.0.1:3306/ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS =True

    #redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    #flask_session
    SESSION_TYPE = 'redis'               #session存放位置
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400   #session保存时间


class DevelopmentConfig(Config):
    """开发者配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生成应用配置"""

    pass


config_map = {
    'develop': DevelopmentConfig,
    'product': ProductionConfig,
}