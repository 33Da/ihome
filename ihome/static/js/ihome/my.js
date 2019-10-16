function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

//点击退出按钮时执行的函数
function logout() {
    $.ajax({
        url:'/api/v1.0/sessions',
        type:'delete',
        headers:{'X-CSRFToken':getCookie('csrf_token')
        },
        dataType:"json",
        success:function (res) {
            if(res.errno=='0'){
                location.href='/index.html'
            }
        }
    });
}

$(document).ready(function(){

    //  在页面加载完毕之后去加载个人信息
    $.get('/api/v1.0/users/show_avatar',function (res) {
        if(res.errno=='0'){

            // 加载头像
            $('#user-avatar').attr('src',res.data.avatar_url);
        }else if (res.errno=='4101'){
            // 未登录，跳转到首页
            location.href='/login.html'
        }else {
            alert(res.msg)
        }
    });

    $.get('/api/v1.0/users/show_name-mobile',function (res) {
        if(res.errno =='0'){
            $('#user-name').text(res.data.user_name);
            $('#user-mobile').text(res.data.user_mobile);

        }else {
            alert(res.msg)
        }
    })
});
