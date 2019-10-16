from . import api
from flask import request, jsonify, current_app, g
from ihome.models import Hourse, Order
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.utils.commons import login_required
from datetime import datetime


@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    """保存订单"""

    # 获取参数
    order_data = request.get_json()

    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    hourse_id = order_data["house_id"]
    start_data_str = order_data["start_date"]
    end_data_str = order_data["end_date"]

    # 获取登录用户
    user_id = g.user_id

    # 参数校验
    if not all([hourse_id, start_data_str, end_data_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 日期格式检查
    try:
        # 将请求时间参数字符转换为datatime类型
        start_data = datetime.strptime(start_data_str, "%Y-%m-%d")
        end_data = datetime.strptime(end_data_str, "%Y-%m-%d")
        assert start_data <= end_data
        # 计算预定天数
        days = (end_data - start_data).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.PARAMERR, errmsg="日期格式错误")

    # 查询房屋是否存在
    try:
        hourse = Hourse.query.get(hourse_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg="获取房屋信息失败")
    if not hourse:
        return jsonify(errno=RET.NODATA, errmsg="房屋信息不存在")

    # 检查房主是否为下单用户
    if user_id == hourse.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="不能预定自己的房屋")

    # 确保订单没有被预定
    try:
        count = Order.query.filter(Order.hourse_id == hourse_id, Order.begin_date <= end_data,
                                   Order.end_date >= start_data).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="检查出错")
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋被预定")

    # 订单总额
    amount = days * hourse.price

    # 保存订单数据
    order = Order(
        hourse_id=hourse_id,
        user_id=user_id,
        begin_date=start_data,
        end_date=end_data,
        days=days,
        hourse_price=hourse.price,
        amount=amount,
    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")
    return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


@api.route("/orders")
@login_required
def get_user_order():
    """查询用户的订单信息"""
    user_id = g.user_id

    # 用户的身份，用户想要查的是自己发布的房子的订单，还是自己要预定别人房子的订单
    role = request.args.get("role", "")

    # 查询订单数据
    try:
        if "customer" == role:  # 房东的身份查询
            # 先查自己的房子有哪些
            hourse = Hourse.query.filter(Hourse.user_id == user_id).all()
            hourse_ids = [h.id for h in hourse]
            # 在查询下了单的房子
            orders = Order.query.filter(Order.hourse_id.in_(hourse_ids)).order_by(Order.creat_time.desc()).all()
        else:
            # 以房客的身份查询
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.creat_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")


    # 将订单对象转为字典数据
    order_dict_list = []
    if orders:
        for order in orders:
            order_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK, ermsg="OK", data={"orders": order_dict_list})


@api.route("/orders/comment/<int:order_id>", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """保存订单评论信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    comment = req_data.get("comment")

    # 检测参数
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 检查是否是自己下的单，只有自己下的单才能评论，且单子处于带评论状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_COMMENT", Order.user_id == user_id)
        hourse = order.hourse

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单信息")

    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    try:
        # 将订单状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单评价信息
        order.comment = comment
        # 将房屋完成单数+1
        hourse.order_count += 1
        db.session.add(order)
        db.session.add(hourse)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    # 把之前在redis中缓存的房屋信息删掉
    try:
        redis_store.delete("house_info_%s" % order.hourse_id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/status/<int:order_id>", methods=["PUT"])
@login_required
def save_reject_order(order_id):
    """接单 拒单"""
    # 获取参数
    user_id = g.user_id

    req_data = request.get_json()
    print(req_data)

    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")



    # action参数表面用户是接单还是拒单行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        hourse = order.hourse
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.REQERR, errmsg="无法获取订单数据")

    # 确保操作订单的是房东
    if not order or hourse.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    if action == "accept":
        # 接单，订单状态变为等待支付
        order.status = "WAIT_PAYMENT"

    elif action == "reject":
        # 拒单 要填写拒单原因
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="填写拒单原因")
        order.status = "REJECTED"
        order.comment = reason
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="订单提交失败")
    return jsonify(errno=RET.OK, errmsg="OK")
