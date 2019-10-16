from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from ihome import constants, db
from flask import current_app
from flask import jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.models import User
import random
import ihome.libs.email_code.zhenzismsclient as smsclient
from ihome.tasks.task_sms import send_sms


@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id: 图片验证码编号
    :return:验证码图片
    """

    # 生成图片验证码
    # 验证码名字，文本内容，图片二进制数据
    name, text, image_data = captcha.generate_captcha()

    # 将验证码真实值和编号保存到redis
    # 直接使用字符串的方式来存验证码     redis存储格式有：str，list，hash，set
    try:
        # 编号                              有效期                     文本
        redis_store.setex(image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 将异常记录到日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="save image code failed")

    # 返回图片给前端
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


@api.route("/sms_codes/<re(r'1[34879]\d{9}'):mobile>")
def get_sms_code(mobile):
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")



    # 校验参数
    if not all([image_code_id, image_code]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    print(image_code_id)
    # 从redis取图片验证码
    try:
        real_image_code = redis_store.get(image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 表示错误或过期
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    #删除redis验证码，防止多次验证
    try:
        redis_store.delete(image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 进行图片验证对比
    if real_image_code.lower().decode("utf-8") != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")


    #判断60s有没有用这个手机发过短信
    try:
        send_flag =redis_store.get("send_sms_time%s" %mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR,errmsg="请求过于频繁,60s后再操作")

    # 判断手机号是否存在，不存在生成短信验证码
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示手机号存在
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号存在")

    # 生成短信验证码
    sms_code = ''  # 验证码

    for num in range(1, 5):
        sms_code = sms_code + str(random.randint(0, 9))

    # 保存短信验证码，redis
    try:
        redis_store.setex("sms_code%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        #保存发送给手机号的记录，防止60s后再次触发
        redis_store.setex("send_sms_time%s" % mobile,constants.SEND_SMS_COOE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="短信验证码异常")


    # 发送短信
    try:
        # 初始化ZhenziSmsClient
        client = smsclient.ZhenziSmsClient("https://sms_developer.zhenzikj.com", "101919",
                                           "8ce1b3b4-2adb-48ef-a1fc-6ba78006d533")

        result = client.send(mobile, '您的验证码为{},五分钟内有效'.format(sms_code))

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="发送失败")

    #字符串转字典
    result=eval(result)

    if result["code"] == 0:
        return jsonify(errno=RET.OK, errmsg="发送成功")
    else:
        current_app.logger.error(result)
        return jsonify(errno=RET.THIRDERR, errmsg="发送失败")




# @api.route("/sms_codes/<re(r'1[34879]\d{9}'):mobile>")
# def get_sms_code(mobile):
#     image_code = request.args.get("image_code")
#     image_code_id = request.args.get("image_code_id")
#
#
#
#     # 校验参数
#     if not all([image_code_id, image_code]):
#         return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
#
#     print(image_code_id)
#     # 从redis取图片验证码
#     try:
#         real_image_code = redis_store.get(image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')
#
#     # 判断图片验证码是否过期
#     if real_image_code is None:
#         # 表示错误或过期
#         return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")
#
#     #删除redis验证码，防止多次验证
#     try:
#         redis_store.delete(image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 进行图片验证对比
#     if real_image_code.lower().decode("utf-8") != image_code.lower():
#         return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")
#
#
#     #判断60s有没有用这个手机发过短信
#     try:
#         send_flag =redis_store.get("send_sms_time%s" %mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             return jsonify(errno=RET.REQERR,errmsg="请求过于频繁,60s后再操作")
#
#     # 判断手机号是否存在，不存在生成短信验证码
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 表示手机号存在
#             return jsonify(errno=RET.DATAEXIST, errmsg="手机号存在")
#
#     # 生成短信验证码
#     sms_code = ''  # 验证码
#
#     for num in range(1, 5):
#         sms_code = sms_code + str(random.randint(0, 9))
#
#     # 保存短信验证码，redis
#     try:
#         redis_store.setex("sms_code%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#         #保存发送给手机号的记录，防止60s后再次触发
#         redis_store.setex("send_sms_time%s" % mobile,constants.SEND_SMS_COOE_INTERVAL, 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg="短信验证码异常")
#
#
#     # 发送短信
#     #使用celery异步发送短信
#     send_sms.delay(mobile,sms_code)
#
#
#     return jsonify(errno=RET.OK, errmsg="发送成功")


