<template>
    <view class="video-play">
        <view class="video-wrap">
            <video :src="url" class="video" :autoplay="true"></video>
        </view>
        <uni-popup ref="popup" type="center">
            <view class="loading-wrap">
                <img :src="loading_pic" class="loading-pic" />
                <button class="loading" @click="handleQuit">
                    生成有点慢,我先干点别的
                </button>
            </view>
        </uni-popup>
        <view class="btn">
            <button v-if="url" class="save-btn" @click="saveVideo">
                <text>支付并保存</text>
            </button>
            <button v-if="url" class="back-btn" @click="backHome">
                <text>返回主页</text>
            </button>
        </view>
    </view>
</template>

<script>
export default {
    data() {
        return {
            url: "",
            templateId: "", //1:抠图,2:串编,3:ai
            templateSrc: "", //模板编号
            styleId: "", //1:竖版 2:横板
            openId: "",
            secretKey: "",
            loading_pic: this.baseUrl + "/image/loading.gif/",
        };
    },

    onLoad(option) {
        this.templateSrc = option.templateSrc;
        this.templateId = option.templateId;

        this.styleId = uni.getStorageSync("styleId");
        this.openId = uni.getStorageSync("openId");
        this.secretKey = uni.getStorageSync("secretKey");

       
        this.getVideo();
    
       
        console.log("---------");
        console.log(this.styleId);
        console.log(this.templateSrc);
        console.log("Id");
        console.log(this.templateId);
    },
    methods: {
        open() {
            this.$refs.popup.open("center");
        },
        close() {
            this.$refs.popup.close();
        },
        getVideo() {
            //打开loading等待
            this.open();
            const that = this;
            if (that.templateId === "1") {
                //抠图

                uni.request({
                    url: that.baseUrl + "/process",
                    header: that.header,
                    timeout: 60000,
                    method: "GET",
                    data: {
                        secretKey: that.secretKey,
                        openId: that.openId,
                        template: that.templateSrc,
                        type: "matting",
                    },
                    success(res) {
                        if (res.data.code == "OK") {
                            that.url = res.data.videoPath;
                            console.log(that.url);
                            that.close();
                        }
                        else {
                            that.close();
                            uni.showToast({
                                title: "生成失败！",
                                duration: 1500,
                                icon: "error",
                            });
                            setTimeout(() => {
                                that.backHome();
                            }, 1500);
                        }


                    },
                    fail(error) {
                        console.log(error);
                        that.close();
                        uni.showToast({
                            title: "生成失败！",
                            duration: 1500,
                            icon: "error",
                        });
                        setTimeout(() => {
                            that.backHome();
                        }, 1500);

                    },
                });
            } else if (that.templateId === "2") {
                //串编
                
                if (that.styleId === "1") {
                    console.log("1111111");
                    setTimeout(() => {
                        uni.request({
                            url: that.baseUrl + "/process",
                            header: that.header,
                            timeout: 60000,
                            method: "GET",
                            data: {
                                secretKey: that.secretKey,
                                openId: that.openId,
                                template: that.templateSrc,
                                type: "editing_vertical",
                            },
                            success(res) {
                                console.log(res);
                                if (res.data.code == "OK") {
                                    that.url = res.data.videoPath;
                                    console.log(that.url);
                                    that.close();
                                }
                                else {
                                    that.close();
                                    uni.showToast({
                                        title: "生成失败！",
                                        duration: 1500,
                                        icon: "error",
                                    });
                                    setTimeout(() => {
                                        that.backHome();
                                    }, 1500);
                                }
                            },
                            fail(error) {
                                console.log(error);
                                that.close();
                                uni.showToast({
                                    title: "生成失败！",
                                    duration: 1500,
                                    icon: "error",
                                });
                                setTimeout(() => {
                                    that.backHome();
                                }, 1500);
                            },
                        });
                    }, 5000);
                }
                else if (that.styleId === "2") {
                    setTimeout(() => {
                        uni.request({
                            url: that.baseUrl + "/process",
                            header: that.header,
                            timeout: 60000,
                            method: "GET",
                            data: {
                                secretKey: that.secretKey,
                                openId: that.openId,
                                template: that.templateSrc,
                                type: "editing_horizontal",
                            },
                            success(res) {
                                if (res.data.code == "OK") {
                                    that.url = res.data.videoPath;
                                    console.log(that.url);
                                    that.close();
                                }
                                else {
                                    that.close();
                                    uni.showToast({
                                        title: "生成失败！",
                                        duration: 1500,
                                        icon: "error",
                                    });
                                    setTimeout(() => {
                                        that.backHome();
                                    }, 1500);
                                }
                            },
                            fail(error) {
                                console.log(error);
                                that.close();
                                uni.showToast({
                                    title: "生成失败！",
                                    duration: 1500,
                                    icon: "error",
                                });
                                setTimeout(() => {
                                    that.backHome();
                                }, 1500);
                            },
                        });
                    }, 5000);
                }

            } else if (that.templateId === "3") {
                if (that.styleId === "1") {
                    //ai_竖版
                    setTimeout(() => {
                        uni.request({
                            url: that.baseUrl + "/process",
                            method: "GET",
                            header: that.header,
                            timeout: 60000,
                            data: {
                                secretKey: that.secretKey,
                                openId: that.openId,
                                template: that.templateSrc,
                                type: "ai_vertical",
                            },
                            success(res) {
                                if (res.data.code == "OK") {
                                    that.url = res.data.videoPath;
                                    console.log(that.url);
                                    that.close();
                                }
                                else {
                                    that.close();
                                    uni.showToast({
                                        title: "生成失败！",
                                        duration: 1500,
                                        icon: "error",
                                    });
                                    setTimeout(() => {
                                        that.backHome();
                                    }, 1500);
                                }
                            },
                            fail(error) {
                                console.log(error);
                                that.close();
                                uni.showToast({
                                    title: "生成失败！",
                                    duration: 1500,
                                    icon: "error",
                                });
                                setTimeout(() => {
                                    that.backHome();
                                }, 1500);
                            },
                        });
                    }, 8000);
                } else if (that.styleId === "2") {
                    //ai_横板
                    setTimeout(() => {
                        uni.request({
                            url: that.baseUrl + "/process",
                            method: "GET",
                            header: that.header,
                            timeout: 60000,
                            data: {
                                secretKey: that.secretKey,
                                openId: that.openId,
                                template: that.templateSrc,
                                type: "ai_horizontal",
                            },
                            success(res) {
                                if (res.data.code === "OK") {
                                    that.url = res.data.videoPath;
                                    console.log(that.url);
                                    that.close();
                                }
                                else {
                                    that.close();
                                    uni.showToast({
                                        title: "生成失败！",
                                        duration: 1500,
                                        icon: "error",
                                    });
                                    setTimeout(() => {
                                        that.backHome();
                                    }, 1500);
                                }
                            },
                            fail(error) {
                                console.log(error);
                                that.close();
                                uni.showToast({
                                    title: "生成失败！",
                                    duration: 1500,
                                    icon: "error",
                                });
                                setTimeout(() => {
                                    that.backHome();
                                }, 1500);
                            },
                        });
                    }, 8000);
                }
            }
        },
        saveVideo() {
            const that = this;
            setTimeout(() => {
                uni.request({
                    url: that.baseUrl + "/get/orderId",
                    method: "GET",
                    header: that.header,
                    timeout: 10000,
                    data: {
                        secretKey: that.secretKey,
                        openId: that.openId,
                    },
                    success(res) {
                        if (res.data.code == "OK") {
                            let goods_order = res.data.orderId;
                            uni.navigateTo({
                                url:
                                    "/pages/payMoney/index?goods_order=" +
                                    goods_order +
                                    "&url=" +
                                    that.url + "&secretKey=" + that.secretKey
                            });
                        }
                    },
                });
            }, 100);
        },
        backHome() {
            uni.reLaunch({
                url: "/pages/travel/index",
            });
        },
        handleQuit() {
            const that = this
            uni.showModal({
                title: "请授权微信服务通知",
                content:
                    "由于后台生成,之后会回到主页,可自行选择关闭小程序,视频生成完成后会通知您",
                success: (res) => {
                    if (res.confirm) {
                        uni.requestSubscribeMessage({
                            tmplIds: ["w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE"],
                            success: (res) => {
                                console.log(res["w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE"]);
                                if (
                                    res["w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE"] === "reject"
                                ) {
                                    uni.showToast({
                                        title: "未授权",
                                        duration: 1500,
                                        icon: "error",
                                    });
                                } else if (
                                    res["w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE"] === "ban"
                                ) {
                                    uni.showToast({
                                        title: "消息已禁用",
                                        duration: 1500,
                                        icon: "error",
                                    });
                                } else if (
                                    res["w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE"] === "accept"
                                ) {
                                    console.log("success");
                                    uni.request({
                                        url: that.baseUrl + "/subscribe",
                                        method: "GET",
                                        header: that.header,
                                        timeout: 10000,
                                        data: {
                                            openId: that.openId,
                                            secretKey: that.secretKey
                                        },
                                        success: (res) => {
                                            console.log(res);
                                            if (res.data.code === "OK") {
                                                that.backHome()
                                            }
                                        },
                                        fail: (error) => {
                                            console.log(error);
                                        }
                                    });
                                }
                            },
                            fail: (error) => {
                                console.log(error);
                                uni.showToast({
                                    title: "未授权",
                                    duration: 1500,
                                    icon: "error",
                                });
                            },
                        });
                    }

                },
            });
        },
    },
};
</script>

<style lang="scss">
.video-play {
    width: 100vw;
    height: 100vh;
    background-color: black;
    display: flex;
    flex-direction: column;
    // position: relative;

    .video-wrap {
        position: absolute;
        margin-top: 20%;
        margin-left: 10%;

        .video {
            height: 70vh;
            width: 80vw;
            border-radius: 10px;
        }
    }

    .loading-wrap {
        width: 100vw;
        height: 100vh;
        background-color: #4cca78;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;

        .loading-pic {
            width: 80vw;
            height: 10vh;
        }

        .loading {
            width: 70vw;
            height: 5vh;
            position: absolute;
            bottom: 0;
            margin-bottom: 15vh;
            background-color: #4cca78;
            color: white;
            font-weight: bold;
            border-color: white;
            border-style: solid;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
    }

    .btn {
        display: flex;
        flex-direction: row;
        position: absolute;
        bottom: 0;
        margin-bottom: 5vh;

        .save-btn {
            color: white;
            background-color: #4cca78;
            width: 45vw;
            height: 5vh;
            font-size: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 16px;
            margin-left: 11%;
        }

        .back-btn {
            width: 45vw;
            height: 5vh;
            font-size: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 16px;
            margin-left: 10%;
        }
    }
}
</style>
