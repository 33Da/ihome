from . import api
from flask import request, session, jsonify, current_app, g
from ihome.models import Area, Hourse, Facility, HourseImage, User, Order
from ihome.utils.image_storage import storage
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome import constants
import json
from ihome.utils.commons import login_required
from datetime import datetime


@api.route("/areas")
def get_area_info():
    """获取城区信息"""

    # 尝试从redis取缓存数据
    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # redis有缓存数据
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库，读取信息
    try:
        area_list = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库连接异常")

    area_dict_list = []
    # 将对象转化为字典
    for area in area_list:
        area_dict_list.append(area.to_dict())

    # 将数据转换为json字符串
    resp_dict = dict(errno=RET.OK, errmsg="OK", data=area_dict_list)
    resp_json = json.dumps(resp_dict)

    # 将数据缓存到redis
    try:
        redis_store.setex("area_info", constants.AREA_INFO_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {"Content-Type": "application/json"}


@api.route("/hourse/info", methods=["POST"])
@login_required
def save_hourse():
    """
    保存房屋
    :return:
    """
    user_id = g.user_id

    # 获取参数
    hourse_dict = request.get_json()

    title = hourse_dict.get("title")  # 房屋名称标题
    price = hourse_dict.get("price")  # 房屋单价
    area_id = hourse_dict.get("area_id")  # 房屋所属编号
    address = hourse_dict.get("address")  # 房屋地址
    room_count = hourse_dict.get("room_count")  # 房屋所包含的房间数
    acreage = hourse_dict.get("acreage")  # 房屋面积
    unit = hourse_dict.get("unit")  # 房屋布局（几厅几室）
    capacity = hourse_dict.get("capacity")  # 房屋容纳人数
    beds = hourse_dict.get("beds")  # 房屋卧床数
    deposit = hourse_dict.get("deposit")  # 押金
    min_days = hourse_dict.get("min_days")  # 最小入住天数
    max_days = hourse_dict.get("max_days")  # 最大入住天数

    # 校验参数
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断金额是否正确，以分为单位
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断城区是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据异常")

    if area is None:
        # 城区不存在
        return jsonify(errno=RET.NODATA, errmsg="城区信息有误")

    # 保存房屋信息
    hourse = Hourse(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days,
    )

    # 处理房屋设施信息
    facility_ids = hourse_dict.get("facility")

    # 校验数据,如果用户勾选了设施信息，在保存数据
    if facility_ids:
        try:
            # select * from in_facility_info where id in []
            facilityies = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        if facilityies:
            # 保存已有合法数据
            # 保存设施数据
            hourse.facilities = facilityies

    try:
        db.session.add(hourse)
        db.session.commit()
    except Exception as e:
        db.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    return jsonify(errno=RET.OK, errmsg="OK", data={"hourse_id": hourse.id})


@api.route("/houres/images", methods=["POST"])
def save_hourse_image():
    """保存房屋图片"""
    # 获取参数
    image_file = request.files.get("house_image")
    hourse_id = request.form.get("house_id")

    print(image_file)

    if not all([image_file, hourse_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断hourse_id存在
    try:
        hourse = Hourse.query.get(hourse_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if hourse is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    image_data = image_file.read()
    # 保存图片到七牛中
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存图片失败")

    # 保存图片链接到数据库
    hourse_image = HourseImage(hourse_id=hourse_id, url=file_name)
    db.session.add(hourse_image)

    # 处理房屋主图片
    if not hourse.index_image_url:
        hourse.index_image_url = file_name
        db.session.add(hourse)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error.logger(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片数据异常")

    # 拼接url返回
    image_url = constants.QINIU_URL_DOMAIN + file_name

    return jsonify(errno=RET.OK, data=({"image_url": image_url}))


@api.route("/user/hourse", methods=["GET"])
@login_required
def get_user_hourse():
    """获取房东发布的房源信息"""

    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        hourse = user.hourse
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据获取失败")

    # 将查询的房屋信息转换为字典存到列表
    hourse_list = []
    if hourse:
        for h in hourse:
            hourse_list.append(h.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"hourse": hourse_list})


@api.route("/hourse/index", methods=["GET"])
@login_required
def get_hourse_index():
    """主页幻灯片展示房屋信息"""

    # 从缓存中尝试获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        # redis有缓存，直接取
        current_app.logger.info("hit hourse index info in redis")
        ret = ret.decode("utf-8")
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        # 从sql中查询获取
        try:
            # 倒叙查询订单数目最多5条
            hourses = Hourse.query.order_by(Hourse.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBrERR, errmsg="查询数据失败")

    if not hourses:
        return jsonify(errno=RET.NODATA, errmsg="无相关数据")

    hourses_list = []
    for house in hourses:
        if not house.index_image_url:
            continue
        hourses_list.append(house.to_basic_dict())

    try:
        # 将房屋信息缓存到redis中
        json_houses = json.dumps(hourses_list)
        redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
    except Exception as e:
        current_app.logger.error(e)

    return '{"errno":"0", "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/hourse/<int:hourse_id>", methods=["GET"])
def get_house_detail(hourse_id):
    """
    获取房屋详情
    :param hourse_id:
    :return:
    """

    # 从session中尝试获取用户id, 没有则赋值 - 1
    user_id = session.get("user_id", "-1")

    # 校验house_id, 不存在则返回错误信息提示
    if not hourse_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 尝试从redis中取得缓存数据
    try:
        ret = redis_store.get("house_info_%s" % hourse_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    # 如果有数据就返回
    if ret:
        current_app.logger.info("house info from redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {
            "Content-Type": "application/json"}

    # 通过house_id查询数据库获取房屋对象
    try:
        hourse = Hourse.query.get(hourse_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    # 判断对象是否存在
    if not hourse:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    try:
        hourse_data = hourse.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据错误")

    # 将房屋详情数据转换成json格式的数据，并存到redis数据库中
    json_hourse = json.dumps(hourse_data)
    try:
        redis_store.setex("house_info_%s" % hourse_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_hourse)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_hourse), 200, {
        "Content-Type": "application/json"}

    return resp


@api.route("/hourse")
def get_hourse_list():
    """获取房屋列表信息，搜索页面"""

    # 获取参数
    start_time = request.args.get("sd")  # 起始时间
    end_time = request.args.get("ed")  # 结束时间
    area_id = request.args.get("aid")  # 区域编号
    sort_key = request.args.get("sk", "new")  # 排序关键字, 默认按新旧排
    page = request.args.get("p")  # 当前页数



    # 处理时间
    try:
        if start_time:
            # 处理时间格式
            start_time = datetime.strftime(start_time, "%Y-%m-%d")

        if start_time:
            # 处理时间格式
            start_time = datetime.strftime(start_time, "%Y-%m-%d")

        if start_time and end_time:
            assert start_time <= end_time

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期参数有误")

    # 判断区域
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="区域参数有误")

    # 处理页面
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 过滤条件构造参数
    filter_params = []

    # 填充过滤参数
    # 时间条件
    conflict_orders = None

    # 如果两个时间条件都有
    try:
        if start_time and end_time:
            # 查询order表冲突订单
            conflict_orders = Order.query.filter(Order.begin_date <= end_time, Order.end_date >= start_time).all()
            # 只有start_time
        elif start_time:
            conflict_orders = Order.query_filter(Order.end_date >= start_time).all()
            # 只有end_time
        elif end_time:
            conflict_orders = Order.query_filter(Order.begin_date <= end_time).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库异常")


    #从冲突订单获取id，并在hourse表中排除
    if conflict_orders:
        conflict_hourse_ids = [order.hourse_id for order in conflict_orders]

        #如果冲突id不为空,执行排除
        if conflict_hourse_ids:
            filter_params.append(Hourse.id.notin_(conflict_hourse_ids))


    #区域条件
    if area_id:
        filter_params.append(Hourse.area_id==area_id)

    #排序条件 分页
    if sort_key =="booking":   #入住多
        hourse_query = Hourse.query.filter(*filter_params).order_by(Hourse.order_count.desc())
    elif sort_key == "price-inc": # 价格顺序
        hourse_query = Hourse.query.filter(*filter_params).order_by(Hourse.price.asc())
    elif sort_key == "price-des": # 价格倒序
        hourse_query = Hourse.query.filter(*filter_params).order_by(Hourse.price.des())
    else:  # 发布时间顺序
        hourse_query = Hourse.query.filter(*filter_params).order_by(Hourse.creat_time.desc())

    try:
        # 处理分页数据                         #当前页数         每页数                                 错误输出
        hourse_page = hourse_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库异常")

    # 获取页面数据
    hourse_list = hourse_page.items
    hourse = []
    for h in hourse_list:
        hourse.append(h.to_basic_dict())

    #获取总页数
    total = hourse_page.pages

    return jsonify(errno=RET.OK,errmsg="OK",data={"total":total,"hourse":hourse,"current_page":page})




