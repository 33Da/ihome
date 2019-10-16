function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function generateUUID() {
    var d = new Date().getTime();
    if (window.performance && typeof window.performance.now === "function") {
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

var uuid = "";
var last_uuid = '';
var imageCodeID = "";

// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
function generateImageCode() {
    //向后端发送请求：/imageCode?uuid=uuid&last_uuid=last_uuid
    imageCodeID = generateUUID();  //生成UUID
    var url = '/api/v1.0/image_codes/' + imageCodeID;   //拼接请求地址
    $('.image-code img').attr('src', url);  //设置img的src属性
    last_uuid = uuid   //设置上一个UUID
}

function sendSMSCode() {
    // 校验参数，保证输入框有数据填写
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }


    if (!(/^1[3456789]\d{9}$/.test(mobile))) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    // TODO: 通过ajax方式向后端接口发送请求，让后端发送短信验证码
    var phone_num = $('#mobile').val(),
        image_code = $('#imagecode').val();


    var params = {
        'image_code_id': imageCodeID,  //图片验证码id
        'image_code': image_code        //图片验证码值
    };
    $.get('/api/v1.0/sms_codes/' + phone_num, params, function (resp) {
        if (resp.errno == "0") {
            var num = 60;
            //表示发送成功
            var timer = setInterval(function () {
                if (num > 1) {
                    // 修改倒计时文本
                    $(".phonecode-a").html(num + "秒");
                    num -= 1;

                } else {
                    $(".phonecode-a").html("获取验证码")
                    $(".phonecode-a").attr("onclick", "sendSMSCode();");
                    clearInterval(timer)
                }
            }, 1000, 60)
        } else {
            alert(resp.errmsg)
            $(".phonecode-a").attr("onclick", "sendSMSCode();")
        }
    });

}

$(document).ready(function () {
    generateImageCode();  // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
    $("#mobile").focus(function () {
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function () {
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function () {
        $("#phone-code-err").hide();
    });
    $("#password").focus(function () {
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function () {
        $("#password2-err").hide();
    });

    // TODO: 注册的提交(判断参数是否为空)
    $('.form-register').submit(function (event) {
        // 阻止自己默认的提交表单事件
        event.preventDefault();
        // 获取后端需要的数据，电话号，密码，短信验证码
        var phone_num = $('#mobile').val(),
            phonecode = $('#phonecode').val(),
            password = $('#password').val(),
            password2 = $('#password2').val(),

            regix = /^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}$/;
        // 判断是否为空,校验
        if (!regix.exec(phone_num)) {
            $('#mobile-err span').text('手机号错误');
            $('#mobile-err').show()
        }
        if (!phonecode) {
            $('#phone-code-err span').text('手机验证码不能为空！');
            $('#phone-code-err').show();
        }
        if (!password) {
            $('#password-err span').text('密码不能为空!');
            $('#password-err').show()
        }
         if (!password2) {
            $('#password2-err span').text('确认密码不能为空!');
            $('#password2-err').show()
        }
        //组织参数
        var params = {
            'mobile': phone_num,
            'sms_code': phonecode,
            'password': password,
            'password2':password2,
        };
        // 提交表单
        $.ajax({
            url: '/api/v1.0/users',
            type: 'post',
            data: JSON.stringify(params),
            contentType: 'application/json',
            headers: {'X-CSRFToken': getCookie('csrf_token')},
            success: function (response) {
                if (response.re_code == '0') {
                    // 成功跳转到首页
                    alert(response.msg);
                    location.href = '/'
                } else {
                    alert(response.msg)
                }
            }
        });
    });
});
