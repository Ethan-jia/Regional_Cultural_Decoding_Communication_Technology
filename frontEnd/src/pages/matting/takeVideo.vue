<template>
    <view class="video-wrap">
        <camera v-if="templateSrc == 1 " device-position="back" flash="off" @error="error" class="camera-content">
        </camera>
        <camera v-if="templateSrc == 2 " device-position="front" flash="off" @error="error" class="camera-content">
        </camera>
        <camera v-if="templateSrc > 2 " device-position="back" flash="off" @error="error" class="camera-content">
        </camera>

        <!-- <button type="primary" @click="takePhoto">拍照</button> -->

        <img src="/static/images/back.png" class="back-btn" @click="handleBack" />
        <img v-if="templateSrc == 1" :src="frame1_src" class="frame" />
        <img v-if="templateSrc == 2" :src="frame2_src" class="frame" />

        <uni-countdown v-if="status !== 0" :show-day="false" :second="14" color="red" class="countdown"></uni-countdown>
        <img v-if="status === 0" @tap="startRecord" class="btn" :src="src1" />
        <img v-else @tap="stopRecord" class="btn" :src="src2" />
        <!-- <uni-countdown :show-day="false" :hour="12" :minute="12" :second="12"></uni-countdown> -->



        <!-- <button type="default" @click="stopRecord" class="stop-btn">
            结束录像
        </button> -->
    </view>
</template>

<script>

export default {
    data() {
        return {
            status: 0,
            src1: "/static/images/record_btn1.png",
            src2: "/static/images/record_btn2.png",
            frame1_src: this.baseUrl + "/image/frame1.png/",
            frame2_src: this.baseUrl + "/image/frame2.png/",
            templateSrc: 0,
            camera: "",

        };
    },
    onLoad(option) {
        this.templateSrc = option.templateSrc - 0
        console.log("sssss");
        console.log(this.templateSrc);

        this.camera = uni.createCameraContext(); //创建照相机对象

    },
    methods: {
        handleBack() {
            uni.navigateBack({ delta: 1 })
        },
        startRecord() {

            this.camera.startRecord({
                success: (res) => {
                    console.log(res);
                    console.log("sdadssada");
                    this.status = 1;
                },
                fail: (err) => {
                    console.log(err);
                    this.camera = uni.createCameraContext(); //创建照相机对象
                    this.startRecord()
                },
            });
        },
        stopRecord() {

            let templateId = this.templateSrc + ""


            this.camera.stopRecord({
                // compressed: true,
                success: (res) => {
                    console.log(res);
                    console.log("ssssss3123131233");
                    // uni.showToast({
                    //     title: "保存成功",
                    //     duration: 500,
                    // });
                   


                    uni.navigateTo({
                        url: "/pages/matting/index?videoSrc=" + res.tempVideoPath + "&templateSrc=" + templateId,
                    });

                    uni.saveVideoToPhotosAlbum({
                        //保存视频到本地
                        filePath: res.tempVideoPath,
                        success() {
                            console.log("save success!");
                        },
                    });


                },
                fail: (err) => {
                    console.log(err);


                },
            });


        },
        error(e) {
            console.log(e.detail);
            uni.showModal({
                title: "请授权照相机权限，以便正常使用！",
                showCancel: false,
                success: () => {
                    uni.getSetting({
                        success(res) {
                            if (!res.authSetting['scope.camera']) {
                                console.log("111111");
                                uni.authorize({
                                    scope: 'scope.camera',
                                    success:(res)=> {
                                        console.log(res);
                                        uni.showToast({
                                            title: '授权成功!',
                                            icon: 'none',
                                        })
                                    },
                                    fail:()=>{
                                        uni.showModal({
                                            title:'是否重新授权',
                                            success(res){
                                                if(res.confirm){
                                                    uni.openSetting({
                                                        success(){
                                                            console.log("权限开启成功");
                                                        },
                                                        fail(){
                                                            console.log("权限开启失败");
                                                        }
                                            
                                                    })
                                                }
                                                else if(res.cancel){
                                                    console.log("拒绝开启权限");
                                                }

                                            }
                                        })
                                    }
    
                                })
                            }

                        }
                    })

                }


            })

        },

        // takePhoto() {
        //     const ctx = uni.createCameraContext();
        //     ctx.takePhoto({
        //         quality: 'high',
        //         success: (res) => {
        //             this.src = res.tempImagePath
        //         }
        //     });
        // },
    },
};
</script>

<style lang="scss">
.video-wrap {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    // justify-content: center;
    // align-items: center;
    position: relative;

    .camera-content {
        width: 100%;
        height: 100%;
        z-index: -1;
        position: absolute;
    }

    .back-btn {
        width: 30rpx;
        height: 50rpx;
        position: absolute;
        margin-top: 12%;
        margin-left: 5%;
    }

    .frame {
        width: 100vw;
        height: 100vh;
    }

    .countdown {
        margin-left: 40%;
        margin-top: 180%;
        position: absolute;
    }


    .btn {
        width: 160rpx;
        height: 160rpx;
        margin-left: 40%;
        margin-top: 190%;
        position: absolute;


    }


    // .stop-btn{}
}
</style>
