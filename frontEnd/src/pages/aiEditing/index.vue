<template>
    <view class="aiEditing-wrap">
        <view class="aiEditing-step content1">
            <img v-if="!templateSrc" :src="step1" @click="handleGoChooseTemp" class="step1" />
            <img v-else :src="step1_success" @click="handleGoChooseTemp" class="step1" />
        </view>
        <view class="aiEditing-step content2">
            <img v-if="videoListNum === 0" :src="step2" class="step2" @click="handleGoChooseVideos" />
            <img v-else :src="step2_success" class="step2" @click="handleGoChooseVideos" />

        </view>
        <view class="aiEditing-step content3">
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
            templateSrc: "",
            step1: this.baseUrl + '/image/editing/step1.png/',
            step1_success: this.baseUrl + '/image/editing/step1_success.png/',
            step2: this.baseUrl + '/image/editing/step2.png/',
            step2_success: this.baseUrl + '/image/editing/step2_success.png/',
            step3: this.baseUrl + '/image/editing/step3.png/',
            bg_pic: this.baseUrl + '/image/bg_pic.png/',
            styleId: "",  // 1:竖版 2：横板
            videoListNum: 0,
        };
    },

    onLoad(option) {



        this.videoListNum = option.videoListNum
        this.templateSrc = option.templateSrc;

        this.styleId = uni.getStorageSync("styleId")
        console.log("AI模式");
        if (this.styleId === "1") {
            console.log("进入竖版");
        }
        else {
            console.log("进入横板");
        }

    },
    methods: {
        handleGoChooseTemp() {
            if (this.styleId === "1") {
                uni.navigateTo({
                    url: "/pages/chooseTemp/index?templateId=4",
                });
            }
            else {
                uni.navigateTo({
                    url: "/pages/chooseTemp/index?templateId=5",
                });
            }
        },
        handleGoChooseVideos() {
            if (this.templateSrc) {
                if (this.styleId === "1") {
                    uni.navigateTo({
                        url: "/pages/chooseVideos/index?templateSrc=" + this.templateSrc+"&type=ai_vertical",
                    });
                }
                else {
                    uni.navigateTo({
                        url: "/pages/chooseVideos/index?templateSrc=" + this.templateSrc+"&type=ai_horizontal",
                    });
                }
            }
            else {
                uni.showToast({
                    title: "请先选择模板",
                    icon: "error",
                });
            }
        },
        handleSrc() {
            if (!this.videoListNum && !this.templateSrc) {
                uni.showToast({
                    title: "请上传视频模板",
                    icon: "error",
                });
            } else if (!this.videoListNum) {
                uni.showToast({
                    title: "请上传视频",
                    icon: "error",
                });
            } else {
                console.log("跳转成功");
                console.log(this.styleId);
                uni.navigateTo({
                    url: "/pages/videoPlay/videoPreview?templateSrc=" + this.templateSrc + "&templateId=3"
                })
            }
        }
    }
}


</script>

<style lang="scss">
.aiEditing-wrap {
    width: 100vw;
    position: absolute;

    .aiEditing-step {
        text-align: center;


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