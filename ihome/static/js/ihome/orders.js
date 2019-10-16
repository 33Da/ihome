//模态框居中的控制
function centerModals(){
    $('.modal').each(function(i){   //遍历每一个模态框
        var $clone = $(this).clone().css('display', 'block').appendTo('body');    
        var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
        top = top > 0 ? top : 0;
        $clone.remove();
        $(this).find('.modal-content').css("margin-top", top-30);  //修正原先已经有的30个像素
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function(){
    $('.modal').on('show.bs.modal', centerModals);      //当模态框出现的时候
    $(window).on('resize', centerModals);

    var queryData = decodeQuery();
    var role = queryData["role"];
    // 查询房客订单
    $.get('/api/v1.0/orders?role='+role,function (res) {
        if(res.errno=='0'){
            render_template=template('orders-list-tmpl',{'orders':res.data.orders});
            $('.orders-list').html(render_template);
            // 添加支付
            $('.order-pay').on("click",function () {
                var order_id = $(this).parents("li").attr("order-id");
                $.ajax({
                    url:"/api/v1.0/orders/payment/"+order_id,
                    type:"post",
                    dataType:"json",
                    headers:{
                        "X-CSRFToken":getCookie("csrf_token"),
                    },
                    success:function (resp) {
                        if ("4101"==resp.errno){
                            location.href ="/login.html"
                        } else if ("0"==resp.errno){
                            location.href = resp.data.pay_url;
                        }

                    }
                });
            });
             查询成功之后需要设置评论的相关处理
            $(".order-comment").on("click", function(){
                var orderId = $(this).parents("li").attr("order-id");
                $(".modal-comment").attr("order-id", orderId);
            });
        }else if(res.errno=='4101'){
            location.href='/login.html'
        }else {
            alert(res.errmsg)
        }
    });

});
