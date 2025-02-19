<template>
    <view class="videos-wrap">
        <view class="videos-title">
            <image src="/static/images/upload.png" class="upload-pic" />
            <text class="title-content1">请添加本地视频</text>
            <text class="title-content2">(建议上传6~9个视频,每个时长大于{{ minTime }}s)</text>
        </view>
        <view class="up-page">
            <view class="videos-box" v-for="(item, index) in videoList" :key="index">
                <video class="full" :src="item"></video>
                <view class="delete-icon" @tap="deleteVideo(index)">
                    <image class="full" src="/static/images/delete.png" />
                </view>
            </view>
            <view v-if="videoShow" @tap="chooseVideo" class="box-mode">
                <image class="full" src="/static/images/add.png" />
            </view>
        </view>
        <view class="videos-btn"><button class="btn" @tap="handleGoPage">
                <text class="btn-content">确认选择</text>
            </button></view>
        <view class="bottom-content">
            <img :src="bg_pic" class="bottom-pic" />
        </view>
    </view>

</template>

<script>
export default {
    data() {
        return {
            templateSrc: "",
            bg_pic: this.baseUrl + '/image/bg_pic.png/',
            videoList: [],//视频存放的地址
            videoShow: true,
            maxCount: 9,
            openId: "",
            secretKey: "",
            styleId: "",//仅针对ai, 1代表竖版, 2代表横板
            minTime: "",
            type: ""

        }
    },

    onLoad(option) {

        // let currentWebview = this.$mp.page.$getAppWebview()
        // currentWebview.setStyle({popGesture:"none"})

        this.templateSrc = option.templateSrc;
        this.type = option.type
        // console.log("templateSrc");
        // console.log(this.templateSrc);
        console.log("ssdadsada");
        console.log(this.type);

        this.minTime = uni.getStorageSync("minTime")
        this.styleId = uni.getStorageSync("styleId")
        this.openId = uni.getStorageSync("openId")
        this.secretKey = uni.getStorageSync("secretKey")
        this.videoClear() //清理之前的视频，重新选择
    },
    onBackPress() {
        return true
    },

    methods: {
        chooseVideo() {
            var that = this;
            uni.chooseVideo({
                sourceType: ["album"],
                compressed: true,
                success(res) {
                    if (res.duration >= that.minTime && res.duration <= 60) {
                        let tempFilePath = res.tempFilePath
                        uni.uploadFile({
                            url: that.baseUrl + '/videos/upload/',
                            header: that.header,
                            filePath: tempFilePath,
                            name: 'file',
                            formData: {
                                'openId': that.openId,
                                'secretKey': that.secretKey,
                                "videoName": tempFilePath,
                                "type": that.type

                            },
                            success: (uploadFileRes) => {
                                console.log(JSON.parse(uploadFileRes.data).code);
                            },
                            fail: (error) => {
                                console.log(error);
                            }
                        })
                        that.videoList = that.videoList.concat(tempFilePath)
                        console.log(that.videoList);
                        if (that.videoList.length == that.maxCount) {
                            that.videoShow = false
                        }
                    }



                    else {
                        uni.showModal({
                            title: "提示",
                            content: "请上传" + that.minTime + "s~60s的视频！",
                            showCancel: false,
                            success(res) {
                                console.log(res);
                            }
                        })
                    }

                },
                fail(error) {
                    console.log(error);
                },
            });
        },
        deleteVideo(index) {
            var that = this
            uni.showModal({
                title: '提示',
                content: '是否要删除此视频',
                success(res) {
                    if (res.confirm) {
                        setTimeout(() => {
                            uni.request({
                                url: that.baseUrl + "/videos/delete",
                                header: that.header,
                                method: "GET",
                                data: {
                                    'openId': that.openId,
                                    'secretKey': that.secretKey,
                                    "videoName": that.videoList[index],
                                },
                                success(res) {
                                    console.log(res.data);
                                    if (res.data.code === "OK") {
                                        setTimeout(() => {
                                            that.videoList.splice(index, 1)
                                        }, 100)
                                        uni.showToast({
                                            title: "删除成功!",
                                            duration: 500,
                                        })
                                    }
                                    else {
                                        uni.showToast({
                                            title: "删除失败!",
                                            duration: 500,
                                            icon: "error"
                                        })
                                    }
                                },
                                fail(error) {
                                    console.log(error);
                                }
                            });
                        }, 10)
                    }
                    setTimeout(() => {
                        if (that.videoList.length > that.maxCount) {
                            that.videoShow = false
                        }
                        else {
                            that.videoShow = true
                        }
                    }, 200);

                }

            })
        },
        handleGoPage() {
            if (this.videoList.length >= 3) {
                if (this.type==="editing_vertical" || this.type==="editing_horizontal") {
                    uni.navigateTo({
                        url: '/pages/editing/index?videoListNum=' + this.videoList.length + "&templateSrc=" + this.templateSrc
                    })
                }
                else {
                    uni.navigateTo({
                        url: '/pages/aiEditing/index?videoListNum=' + this.videoList.length + "&templateSrc=" + this.templateSrc
                    })
                }
            }
            else {
                uni.showModal({
                    title: "提示",
                    content: "请至少上传三个视频!",
                    showCancel: false,
                    success(res) {
                        console.log(res);
                    }
                })
            }
        },
        videoClear() {
            uni.request({
                url: this.baseUrl + "/videos/clear",
                method: "GET",
                data: {
                    'openId': this.openId,
                    'secretKey': this.secretKey,
                },
                success(res) {
                    console.log(res.data);
                }
            })
        }
    }

}
</script>

<style lang="scss">
.box-mode {
    width: 25vw;
    height: 25vw;
    border-radius: 8rpx;
    overflow: hidden;
    margin-top: 2vh;
    margin-left: 4vw;
}

.full {
    width: 100%;
    height: 100%;
}

.videos-wrap {
    width: 100vw;
    margin-top: 3vh;


    .videos-title {
        display: flex;
        flex-direction: row;
        margin-left: 5vw;
        margin-top: 3vh;

        .upload-pic {
            width: 20px;
            height: 18px;
            margin-top: 0.2vh;
        }

        .title-content1 {
            margin-left: 2vw;
            font-weight: bold;

            letter-spacing: 0.1px;

        }

        .title-content2 {
            margin-left: 1vw;
            margin-top: 0.8vh;
            font-size: 11px;
            color: #969696;
        }

    }

    .up-page {
        display: flex;
        flex-wrap: wrap;
        width: 100%;

        .show-box:nth-child(3n) {
            margin-right: 0rpx;
        }

        .videos-box {
            position: relative;
            margin-bottom: 4vw;
            margin-right: 4vw;
            @extend .box-mode;

            .delete-icon {
                height: 30rpx;
                width: 30rpx;
                position: absolute;
                right: 5rpx;
                top: 3rpx;
                z-index: 1000;
            }

        }
    }

    .videos-btn {
        margin-top: 2vh;

        .btn {
            width: 80vw;
            height: 6vh;
            background-color: #4cca78;
            border-radius: 30px;
            display: flex;
            justify-content: center;
            align-items: center;

            .btn-content {
                font-size: 16px;
                color: #ffffff;
                letter-spacing: 2px;



            }

        }
    }


    .bottom-content {
        .bottom-pic {
            width: 100vw;
            height: 35vh;
            position: fixed;
            bottom: 0;
        }
    }
}
</style>