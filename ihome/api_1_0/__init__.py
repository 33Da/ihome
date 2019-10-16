from flask import Blueprint

#创建蓝图
api = Blueprint("api_1_0",__name__)

#导入蓝图视图
from . import demo, verify_code,passport,profile,hourse,orders,pay