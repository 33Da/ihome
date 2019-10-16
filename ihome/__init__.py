from config import config_map
from flask_sqlalchemy import SQLAlchemy
import redis
from flask import Flask
from flask_session import Session
from flask_wtf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
from ihome.utils.commons import ReConverter
import pymysql

pymysql.install_as_MySQLdb()

# 创建数据库实例
db = SQLAlchemy()

# 创建redis实例
redis_store = None

# 设置日志的记录等级  在flask DEBUG模式下这个等级没有用
logging.basicConfig(level=logging.DEBUG)
# 创建日志记录器，指明路径，最大日志大小，个数上线
file_log_handle = RotatingFileHandler('logs/log', maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录格式                   日志等级       文件名       行数       日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handle.setFormatter(formatter)
# 设置全局记录对象 添加日记记录器
logging.getLogger().addHandler(file_log_handle)


# 工厂模式
def create_app(config_name):
    """
    创建flask应用对象
    :param config_name: str 配置模式的模式名 ("develop", "product")
    :return:
    """

    app = Flask(__name__)

    # 根据配置模式名字获取配置参数
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 初始化db
    db.init_app(app)

    # 初始化redis
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # 利用flask-session,将session数据包保存到redis
    Session(app)

    # csrf全局保护, 验证
    CSRFProtect(app)

    # 为flask添加自定义转换器
    app.url_map.converters["re"] = ReConverter

    # 注册蓝图
    from . import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

    # 注册提供静态文件蓝图
    from ihome import web_html
    app.register_blueprint(web_html.html)

    return app
