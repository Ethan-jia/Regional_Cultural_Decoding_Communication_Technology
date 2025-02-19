<template>
    <view class="pay-wrap">
        <view class="pay-content1">
            <text style="font-size:14px;font-weight: bold;margin-top: 1vh;margin-left: 3vw;">商品名称</text>
            <text style="font-size:12px;font-weight: bold;margin-top: 1vh;margin-left: 3vw; color: #999999;">阆中视频</text>
        </view>
        <view class="pay-content2">
            <text style="font-size:14px;font-weight: bold;margin-top: 1vh;margin-left: 3vw;">订单编号</text>
            <text
                style="font-size:12px;font-weight: bold;margin-top: 1vh;margin-left: 3vw; color: #999999;">{{goods_order}}</text>
        </view>
        <view class="pay-content3">
            <text style="font-size:14px;font-weight: bold;margin-top: 1vh;margin-left: 3vw;">温馨提示</text>
            <text
                style="font-size:12px;font-weight: bold;margin-top: 1vh;margin-left: 3vw; color: #999999;">视频一经下载,不可退货。视频内涉及到的所有人物,景物，以及其他涉及到的法律问题均与本公司无关。</text>
        </view>
        <view class="bottom-content">
            <text style="color: red;margin-left: 2vw;margin-top: 2vh;">￥{{money}}</text>
            <button class="submit" @click="submitOrder">
                提交订单
            </button>
        </view>

    </view>
</template>

<script>

export default {
    data() {
        return {
            goods_order: "",
            timeStamp: "",
            nonceStr: "",
            package: "",
            paySign: "",
            url: "",
            secretKey: "",
            openId: "",
            money: ""
        }
    },
    onLoad(option) {
        this.goods_order = option.goods_order
        this.url = option.url
        this.secretKey = option.secretKey

        this.openId = uni.getStorageSync("openId")
        console.log(this.url);
        this.getPreOrder()

    },
    methods: {
        getPreOrder() {
            const that = this
            uni.request({
                url: that.baseUrl + "/get/prePay",
                method: "GET",
                header: that.header,
                timeout: 10000,
                data: {
                    "openId": that.openId,
                    "secretKey": that.secretKey,
                    "orderId": that.goods_order,
                    "description": "阆中游记视频",
                    "amount": 1,
                },
                success(res) {
                    console.log(res.data);
                    if (res.data.code === "OK") {
                        that.timeStamp = res.data.timeStamp,
                            that.nonceStr = res.data.nonceStr,
                            that.package = res.data.package,
                            that.paySign = res.data.paySign,
                            that.money = res.data.money
                    }

                },
                fail(e) {
                    console.log(e);
                }
            })
        },
        submitOrder() {
            const that = this
            uni.requestPayment({
                "timeStamp": that.timeStamp,
                "nonceStr": that.nonceStr,
                "package": that.package,
                "signType": "RSA",
                "paySign": that.paySign,
                success(res) {
                    console.log(res);
                    console.log("2222222");
                    console.log(that.url);
                    uni.request({
                        url: that.baseUrl + "/payStatus",
                        method: "GET",
                        header: that.header,
                        timeout: 10000,
                        data: {
                            "openId": that.openId,
                            "secretKey": that.secretKey,
                        },
                        success: (res) => {
                            if (res.data.code === "OK") {
                                uni.navigateTo({
                                    url: "/pages/videoPlay/index?url=" + that.url + "&status=1"
                                })
                            }

                        },
                        fail: (e) => {
                            console.log(e);
                        }
                    })

                },
                fail(e) {
                    console.log(e);
                    uni.navigateTo({
                        url: "/pages/saveStatus/index?id=0"
                    })
                }

            })
        }
    }


}

</script>


<style lang="scss">
.pay-wrap {
    width: 100vw;
    height: 100vh;
    background-color: #F0F0F0;
    display: flex;
    flex-direction: column;

    .pay-content1 {
        margin-top: 3vh;
        margin-left: 5vw;
        width: 90vw;
        height: 8vh;
        background-color: white;
        display: flex;
        flex-direction: column;

    }

    .pay-content2 {
        margin-top: 2vh;
        margin-left: 5vw;
        width: 90vw;
        height: 8vh;
        background-color: white;
        display: flex;
        flex-direction: column;
    }

    .pay-content3 {
        margin-top: 2vh;
        margin-left: 5vw;
        width: 90vw;
        height: 15vh;
        background-color: white;
        display: flex;
        flex-direction: column;
    }

    .bottom-content {
        width: 100vw;
        height: 7vh;
        background-color: white;
        position: fixed;
        bottom: 0;
        display: flex;
        flex-direction: row;

        .submit {
            background-color: #4cca78;
            margin-right: 0vw;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
        }
    }
}
</style>