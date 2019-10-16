from . import api
from flask import request,session,jsonify,current_app
import re
from ihome.models import User
from ihome.utils.response_code import RET
from ihome import redis_store,db
from sqlalchemy.exc import IntegrityError
from ihome import constants

@api.route("/users", methods=["POST"])
def register():
    """
    用户注册
    :return:
    """

    #获取参数
    req_dict =request.get_json()

    mobile = req_dict["mobile"]
    sms_code = req_dict["sms_code"]
    password = req_dict["password"]
    password2 = req_dict["password2"]


    #校验参数
    if not all([mobile,password,password2,sms_code]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    #判断手机号是否正确
    if not re.match(r"1[345789]\d{9}",mobile):
        #不及格
        return jsonify(errno=RET.PARAMERR,errmsg="手机号格式不正确")

    # 判断密码是否一致
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次输入密码不一致")


    #判断手机号验证码是否正确
    try:
        real_sms_code = redis_store.get("sms_code%s"%mobile).decode("utf-8")  #取出真实验证码
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR,errmsg="读取短信验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA,errmsg="短信验证码失效")


    # 判断短信验证码是否正确
    if real_sms_code != sms_code:
        return jsonify(errno=RET.NODATA,errmsg="短信验证码错误")

    #存储进sql
    user = User(mobile=mobile,name=mobile)
    user.password_hash = password

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:  #因为已经设置mobile为不唯一，所有有重复的话就会有这个异常
        db.session.rollback()
        #手机号重复
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST,errmsg="手机号存在")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库连接异常")

    #保存登陆状态
    session["name"] = mobile
    session["mobile"] = mobile
    session["id"] = user.id
    return jsonify(errno=RET.OK,errmsg="注册成功")


@api.route("/sessions",methods=["POST"])
def login():
    """
    用户登陆
    :param:手机号,密码
    :return:
    """

    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict["mobile"]   #手机号
    password = req_dict["password"]   #密码

    # 检验参数
    #检验参数完整
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    #检验手机号是否正确
    if not re.match(r"1[345789]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    #判断登陆是否超过限制,超过则返回
    user_ip = request.remote_addr #获取用户ip
    try:
        access_nums = redis_store.get("access_num_%s" % user_ip)
        print(access_nums)

    except Exception as e:
        current_app.logger.error(e)
    else:
        #请求次数超过五次
        if access_nums is not None and int(access_nums) >= 5:
            return jsonify(errno=RET.REQERR,errmsg="请求次数过多")


    # 查询sql
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户信息失败")


    # 检验是否存在该用户且密码是否正确
    if user is None or not user.check_password(password):
        #错误，将登陆次数再redis +1
        try:
            redis_store.incr("access_num_%s" % user_ip)
            redis_store.expire("access_num_%s" % user_ip,constants.LOGIN_ERROR_FOBID_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    # 保存进session
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id
    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/sessions",methods=["GET"])
def check_login():
    """
    检验登录状态
    :return:
    """
    #从session获取用户名
    name = session.get("name")
    #如果存在则登录，反之
    if name is not None:
        return jsonify(errno=RET.OK,errmsg="true",data={"name":name})
    else:
        return jsonify(errno=RET.SESSIONERR,errmsg="false")

@api.route("/sessions",methods=["DELETE"])
def logout():
    """登出"""
    #清除session数据
    csrf_token = session.get("csrf_token")
    session.clear()
    session["csrf_token"] = csrf_token
    return jsonify(errno=RET.OK,errmsg="OK")

