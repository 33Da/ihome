function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    //  添加登录表单提交操作
    $(".form-login").submit(function(e){
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        }
        regix = /^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}$/;
        // 判断是否为空,校验
        if (!regix.exec(mobile)) {
            $('#mobile-err span').text('请填写正确手机号');
            $('#mobile-err').show()
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        var params={
            'mobile':mobile,
            'password':passwd
        };
        $.ajax({
                    url:'/api/v1.0/sessions',
                    type:'post',
                    data:JSON.stringify(params),
                    contentType:'application/json',
                    headers:{'X-CSRFToken':getCookie('csrf_token')},
                    success:function(response){
                        if(response.errno=='0'){
                            // 登录成功
                            location.href='/index.html'
                        }
                    }
                });
    });
});
