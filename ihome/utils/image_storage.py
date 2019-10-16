from qiniu import Auth, put_data


#需要填写你的 Access Key 和 Secret Key
access_key = 'R7QoCwlqwB47gqiRk5goFbHOD7UF-hz68kS1NHhN'
secret_key = 'WNKdEP1gNVzG323Uj9GghBN2SQi1_WdvvNd2VMUI'


def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'ihome'

    # 上传到七牛后保存的文件名
    # key = 'my-python-logo.png'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 要上传文件的本地路径
    # localfile = './sync/bbb.jpg'

    ret, info = put_data(token,None, file_data)

    if info.status_code == 200:
        """表示图片上传成功"""
        return ret.get("key")
    else:
        # 上传失败
        raise Exception("图片上传七牛云失败")

if __name__ == '__main__':
    with open("./1.jpg", "rb") as f:
        file_data = f.read()
        storage(file_data)

