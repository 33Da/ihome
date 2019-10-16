from ihome.utils.commons import login_required
from flask import g,request,jsonify,current_app,session
from . import api
from ihome.models import User
from ihome.utils.response_code import RET
from ihome import db, constants
from ihome.utils.image_storage import storage


@api.route("/users/name",methods=["POST"])
@login_required
def update_name():
    #获取用户id
    user_id = g.user_id
    #获取用户名
    req_dict = request.get_json()
    name = req_dict["name"]

    #校验参数是否为空
    if name is None:
        return jsonify(errno=RET.DATAEXIST,errmsg="用户昵称不为空")

    #判断用户名是否存在
    try:
        user = User.query.filter_by(id=user_id).first()
        user_name = user.name
        if user_name is not None and user_name == name:
            return jsonify(errno=RET.DATAEXIST,errmsg="该用户名已存在")
    except Exception as e:
        current_app.logger.error(e)


    #用户名写入数据库
    try:
        User.query.filter_by(id=user_id).update({"name":name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="保存用户名失败")

    # 将session的名字改
    session["name"] = name

    return jsonify(errno=RET.OK,errmsg="修改成功",data={"name":name})

@api.route("/users/avatar",methods=["POST"])
@login_required
def set_avater():
    """
    上传头像图片
    :return:
    """
    #获取用户id
    user_id = g.user_id

    #获取头像图片
    image_file = request.files.get("avatar")

    #校验参数
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

    # 读取图片二进制数据
    image_data = image_file.read()

    # 上传头像
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

    #保存头像链接到sql
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    avatar_url = constants.QINIU_URL_DOMAIN + file_name

    return jsonify(errno=RET.OK, errmsg="保存成功", data={"avatar_url": avatar_url})




@api.route("/users/show_avatar")
@login_required
def show_avater():
    """显示头像"""
    #获取用户id
    user_id = g.user_id

    #从数据库中获取avatar_url
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取图片信息失败")

    # 拼接图片完整链接
    avatar_url = constants.QINIU_URL_DOMAIN + user.avatar_url

    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": avatar_url})





@api.route("/users/show_name-mobile")
@login_required
def show_name_mobile():
    """获取用户名和手机号"""
    #获取用户id
    user_id = g.user_id

    #从sql获取用户名和手机号
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户信息失败")

    #获取用户名
    user_name = user.name

    #获取手机号
    user_mobile = user.mobile

    #构造返回字典
    data={
        "user_name":user_name,
        "user_mobile":user_mobile,
    }

    return jsonify(errno=RET.OK,errmsg="OK",data=data)


@api.route("/users")
@login_required
def get_user_info():
    """获取个人基本信息"""
    user_id = g.user_id

    #在数据库查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA,errmsg="无效操作")

    #获取数据
    data = user.userinfo_to_dict()

    print(data)

    #拼接字符串
    data["avatar_url"] = constants.QINIU_URL_DOMAIN + data["avatar_url"]

    return jsonify(errno=RET.OK,errmsg="OK",data=data)


@api.route("/users/auth")
@login_required
def get_user_auth():
    """获取个人信息"""
    user_id = g.user_id

    #在数据库查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA,errmsg="无效操作")
    return jsonify(errno=RET.OK,errmsg="OK",data=user.auth_to_dict())



@api.route("/users/auth",methods=["POST"])
@login_required
def set_user_auth():
    """保存实名信息"""

    #获取用户id
    user_id = g.user_id

    #获取参数
    req_data = request.get_json()
    real_name = req_data["real_name"]
    id_card = req_data["id_card"]

    #校验参数
    if not all([real_name,id_card]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    #保存用户姓名和身份证
    try:
        User.query.filter_by(id=user_id,real_name=None,id_card=None).update({"real_name":real_name,"id_card":id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="保存用户真实姓名失败")

    return jsonify(errno=RET.OK,errmsg="OK")