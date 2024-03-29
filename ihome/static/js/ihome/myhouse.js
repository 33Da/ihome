$(document).ready(function(){
    // 对于发布房源，只有认证后的用户才可以，所以先判断用户的实名认证状态
    $.get('/api/v1.0/users/auth',function (res) {
        if(res.errno=='0'){
            //判断是否实名认证
            if(!res.user_auth.real_name || !res.user_auth.id_card){
                $(".auth-warn").show();
            }else {
                // 查询所有该用户发布的房源
                render_template=template('houses-list-tmpl',{'houses':''});
                $('#houses-list').html(render_template);
            }
        }else if(res.errno=='4101'){
            location.href='/login.html'
        }else {
            alert(res.errmsg)
        }
    });
    //  如果用户已实名认证,那么就去请求之前发布的房源
    $.get('/api/v1.0/user/hourse',function (res) {
        if(res.errno='0'){
            render_template=template('houses-list-tmpl',{'houses':res.data.hourse});
            $('#houses-list').html(render_template);
        }else if(res.errno=='4101'){
            location.href='/login.html'
        }else{
            alert(res.errmsg)
        }
    });
});
