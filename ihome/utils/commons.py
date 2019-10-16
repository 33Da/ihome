#定义正则转换器

from werkzeug.routing import BaseConverter
from flask import session,jsonify,g
from ihome.utils.response_code import RET
import functools

class ReConverter(BaseConverter):
    """正则转换器"""

    def __init__(self,url_map,regex):
        #调用父类初始话方法
        super(ReConverter,self).__init__(url_map)
        self.regex = regex


def login_required(view_func):
    """
    登录验证装饰器
    :param view_func:
    :return:
    """
    @functools.wraps(view_func)    #不改变被装饰函数
    def wrapper(*args,**kwargs):
        user_id = session.get("user_id")

        if user_id is not None:
            g.user_id = user_id
            return view_func(*args,**kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR,errmsg="用户未登录")

    return wrapper