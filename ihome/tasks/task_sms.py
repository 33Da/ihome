from celery import Celery
import ihome.libs.email_code.zhenzismsclient as smsclient


# 定义celery对象
celery_app = Celery("ihome",broker="redis//127.0.0.1:6379/1")

@celery_app.task
def send_sms(to,datas):
    """发送短信异步任务"""
    # 初始化ZhenziSmsClient
    client = smsclient.ZhenziSmsClient("https://sms_developer.zhenzikj.com", "101919",
                                       "8ce1b3b4-2adb-48ef-a1fc-6ba78006d533")

    result = client.send(to, '您的验证码为{},五分钟内有效'.format(datas))
