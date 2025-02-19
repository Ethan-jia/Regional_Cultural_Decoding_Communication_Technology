<template>
    <view class="matting-wrap">
        <view class="matting-step content1">
            <img v-if="!templateSrc" :src="step1" @click="handleGoChooseTemp" class="step1" />
            <img v-else :src="step1_success" @click="handleGoChooseTemp" class="step1" />
        </view>
        <view class="matting-step content2">
            <img v-if="!videoSrc" :src="step2" class="step2" @click="handlePopup" />
            <img v-else :src="step2_success" class="step2" @click="handlePopup" />
            <uni-popup ref="popup" background-color="rgb(243,243,243)" :is-mask-click="true">
                <view class="recording-content">
                    <button class="recording" @click="handleTakeVideo">录制</button>
                    <button class="selecting" @click="handleChooseVideo">从手机相册选择</button>
                    <button @click="close" class="canceling">取消</button>
                </view>
            </uni-popup>

        </view>
        <view class="matting-step content3">
            <img :src="step3" class="step3" @click="handleSrc" />
        </view>
        <view class="bottom-content">
            <img :src="bg_pic" class="bottom-pic" />
        </view>
    </view>
</template>

<script>


export default {
    data() {
        return {
            videoSrc: "",
            templateSrc: "",
            step1: this.baseUrl + '/image/matting/step1.png/',
            step1_success: this.baseUrl + '/image/matting/step1_success.png/',
            step2: this.baseUrl + '/image/matting/step2.png/',
            step2_success: this.baseUrl + '/image/matting/step2_success.png/',
            step3: this.baseUrl + '/image/matting/step3.png/',
            bg_pic: this.baseUrl + '/image/bg_pic.png/',
            openId:"",
            secretKey:"",
            platform:"",


        };
    },
    components: {},
    onLoad(option) {
        this.templateSrc = option.templateSrc;   
        this.videoSrc = option.videoSrc;

        this.openId = uni.getStorageSync("openId")
        this.secretKey = uni.getStorageSync("secretKey")
        this.platform = uni.getSystemInfoSync().platform
        console.log(this.platform);
    },

    methods: {
        handlePopup() {
            if(!this.templateSrc){
                uni.showToast({
                    title: "请先选择模板",
                    icon: "error",
                });
            }
            else if (this.templateSrc !=="2") {
                this.$refs.popup.open("bottom");
            } 
            else if (this.templateSrc ==="2"){
                this.handleTakeVideo()
            }
           

        },
        close() {
            this.$refs.popup.close();
        },
        handleGoChooseTemp() {
            uni.navigateTo({
                url: "/pages/chooseTemp/index?templateId=1",
            });
        },
        handleTakeVideo() {
            uni.navigateTo({
                url: "/pages/matting/takeVideo?templateSrc=" + this.templateSrc
            })
            // var self = this;
            // uni.chooseMedia({
            //     count:1,
            //     mediaType:['video'],
            //     sourceType: ["camera"],
            //     maxDuration: 15,
            //     success(res) {
            //         self.videoSrc = res.tempFiles[0].tempFilePath;
            //         self.height = res.tempFiles[0].height
            //         self.width = res .tempFiles[0].width
            //         console.log(self.videoSrc);
            //         self.close();

            //     },
            //     fail(res) {
            //         console.log(res);
            //     },
            // });

        },
        handleSrc() {
            if (!this.videoSrc && !this.templateSrc) {
                uni.showToast({
                    title: "请上传视频模板",
                    icon: "error",
                });
            } else if (!this.videoSrc) {
                uni.showToast({
                    title: "请上传视频",
                    icon: "error",
                });
            } else {
                //打开loading等待

                console.log(this.videoSrc);
                console.log("----------------");
                uni.showLoading({ mask: true, title: "上传中..." })               
                uni.uploadFile({
                    url: this.baseUrl + '/videos/upload/',
                    filePath: this.videoSrc,
                    header:this.header,
                    name: 'file',
                    formData: {
                        'openId': this.openId,
                        'secretKey': this.secretKey,
                        'videoName':this.videoSrc,
                        "template": this.templateSrc,
                        "type": "matting",
                        "platform" : this.platform

                    },
                    success: (uploadFileRes) => {
                        console.log(uploadFileRes.data);
                        console.log("success!");
                        if (JSON.parse(uploadFileRes.data).code == "OK") {
                            //关闭loading
                            uni.hideLoading()
                            uni.showToast({
                                title: "上传成功！",
                                duration: 1500,
                            });
                            setTimeout(() => {
                                    uni.navigateTo({
                                        url: "/pages/videoPlay/videoPreview?templateSrc="+this.templateSrc+"&templateId=1"
                                    })
                                }, 2000)
                           
                        }
                        else {
                            uni.hideLoading();
                            uni.showToast({
                                title: "上传失败！",
                                icon: "error",

                            });
                        }

                    },
                    fail: (e) => {
                        console.log(e);
                        uni.hideLoading()
                        uni.showToast({
                            title: "上传失败！",
                            icon: "error",

                        });
                    }
                });

            }
        },
        handleChooseVideo() {

            var self = this;
            uni.chooseVideo({
                sourceType: ["album"],
                // compressed: True,
                success(res) {
                    self.videoSrc = res.tempFilePath;
                    console.log(self.videoSrc);
                    self.close();
                },
                fail(res) {
                    console.log(res);
                },
            });


        },
    },
};
</script>

<style lang="scss">
.matting-wrap {
    width: 100vw;
    position: absolute;

    .matting-step {
        text-align: center;

        .uni-popup {
            border-top-left-radius: 10%;
            border-top-right-radius: 10%;
        }

        .recording-content {
            .recording {
                background-color: rgb(243, 243, 243);
            }

            .recording::after {
                border-bottom: none;
            }

            .selecting {
                background-color: rgb(243, 243, 243);
                border-top: none;
            }

            .canceling {
                background-color: rgb(243, 243, 243);
            }

            .canceling::after {
                border-bottom: none;
            }
        }

        .step1 {
            width: 90vw;
            height: 20vh;
            margin-top: 5%;
        }

        .step2 {
            width: 90vw;
            height: 20vh;
            margin-top: 2%;
        }

        .step3 {
            width: 90vw;
            height: 18vh;
            margin-top: 2%;
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
