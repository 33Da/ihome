from flask import g,current_app,jsonify,request
from . import api
from ihome.utils.commons import login_required
from ihome.models import Order
from ihome.utils.response_code import RET
from alipay import AliPay
import os
from ihome import constants,db

@api.route("/orders/payment/<int:order_id>",methods=["POST"])
@login_required
def order_pay(order_id):
    """发起支付宝支付"""


    user_id = g.user_id
    # 判断订单状态
    try:
        order=Order.query.filter(Order.id==order_id,Order.user_id==user_id,Order.status=="WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库连接异常")

    if order is None:
        return jsonify(errno=RET.NODATA,errmsg="订单数据有误")


    #创建支付宝sdk工具对象
    app_client = AliPay(
        appid="2016101100658656",  # 沙箱的appid
        app_notify_url=None,  # 默认回调url
        app_private_key_string=os.path.join(os.path.dirname(__file__),"keys/app_private_key.pem"),  # 私钥
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=os.path.join(os.path.dirname(__file__),"keys/ailpay_public_key.pem"),
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    order_string = app_client.api_alipay_trade_wap_pay(
        out_trade_no=order.id,  # 订单编号
        total_amount=str(order.amount / 100.0),  # 总金额
        subject=u"爱家租房<%s>" % order.id,  # 订单标题
        return_url="http://127.0.0.1:5000/orders.html",
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    # 构造返回url
    pay_url = constants.ALIPAY_URL_PREFIX + order_string

    return jsonify(errno=RET.OK, errmsg="OK", data={"pay_url": pay_url})




@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
    """保存订单支付结果"""
    alipay_dict = request.form.to_dict()

    alipay_sign = alipay_dict.pop("sign")

    # 获取应用私钥
    app_private_key_path = os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")
    app_private_key_string = open(app_private_key_path).read()
    # 获取支付宝公钥
    alipay_public_key_path = os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")
    alipay_public_key_string = open(alipay_public_key_path).read()

    app_client = AliPay(
        appid="2016092400589177",  # 沙箱的appid
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,  # 应用私钥
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,  # 支付宝公钥
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    result = app_client.verify(alipay_dict, alipay_sign)

    if result:
        # 获取请求中的参数
        order_id = alipay_dict.get("out_trade_no")  # 订单号
        trade_no = alipay_dict.get("trade_no")  # 支付宝的流水号
        try:
            # 查询并修改该订单的状态以及在支付宝中的交易流水号
            Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="OK")







