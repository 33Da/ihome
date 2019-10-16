from flask import Blueprint, current_app, make_response
from flask_wtf import csrf



# 提供静态文件蓝图
html = Blueprint("web_html", __name__)


@html.route("/<re(r'.*'):html_file_name>")
def gethtml(html_file_name=None):
    """提供html文件"""
    # 如果为空，则是主页
    if not html_file_name:
        html_file_name = "index.html"

    # 如果资源名不是favicon.ico
    if html_file_name != "favicon.ico":
        html_file_name = "html/" + html_file_name


    #创建csrf_token值
    csrf_token = csrf.generate_csrf()


    # flask提供的返回静态文件方法
    resp = make_response(current_app.send_static_file(html_file_name))

    #设置cookie值
    resp.set_cookie("csrf_token", csrf_token)

    return resp
