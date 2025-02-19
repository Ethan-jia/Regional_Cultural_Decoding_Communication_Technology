<template>
    <view class="video-play">
        <view class="video-wrap">
            <video :src="url" class="video" :object-fit="mode" :autoplay=true></video>
            <button v-if="status==0 || status==2" @click="backHome" class="btn"><text>
                    返 回
                </text></button>
        </view>
    </view>
</template>

<script>


export default {
    data() {
        return {
            url: "",
            status: "", // 0:主页预览模式 1：保存模式 2:我的视频预览模式
            mode: ""
        }
    },
    onLoad(option) { //option为object类型，会序列化上个页面传递的参数

        this.url = option.url
        console.log(this.url)
        this.status = option.status
        console.log("---------------");
        console.log(this.status);
        if (this.status === "0") {
            this.mode = "fill"

        }
        else if (this.status === "1") {

            this.mode = "contain"
            this.saveVideo()


        }

        else if (this.status === "2") {
            this.mode = "contain"
        }


    },
    methods: {
        backHome() {
            uni.navigateBack({ delta: 1 })
        },
        saveVideo() {
            //打开loading等待
            uni.showLoading({ mask: true, title: "保存中..." })

            //先下载视频
            console.log(this.url);
            uni.downloadFile({
                url: this.url,
                success: (res1) => {
                    const that = this
                    if (res1.statusCode == 200) {

                        //保存视频到本地

                    }
                    console.log(res1.tempFilePath);
                    uni.compressVideo({
                        src: res1.tempFilePath,
                        // quality: "medium",
                        bitrate: "2000",
                        fps: "30",
                        resolution: "1",
                        success(res2) {
                            console.log("压缩成功！");
                            uni.saveVideoToPhotosAlbum({

                                filePath: res2.tempFilePath,
                                success() {
                                    console.log("save success!");
                                    uni.hideLoading()
                                    uni.showToast({
                                        title: "保存成功",
                                        duration: 1500,
                                    });
                                    setTimeout(() => {
                                        uni.navigateTo({
                                            url: "/pages/saveStatus/index?id=1"
                                        })
                                    }, 1500);


                                },
                                fail(error) {
                                    console.log(error);
                                    uni.hideLoading()


                                }
                            });

                        }
                    })


                }
            })
        }
    }
}
</script>


<style lang="scss">
.video-play {
    height: 100vh;
    background-color: black;
    position: relative;

    .video-wrap {
        display: flex;
        flex-direction: column;
        position: absolute;
        margin-top: 15%;
        margin-left: 10%;



        .video {
            height: 70vh;
            width: 80vw;
            border-radius: 10px;
        }

        .btn {
            margin-top: 10%;
            height: 5vh;
            width: 40vw;
            color: white;
            background-color: #4cca78;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 16px;



        }
    }
}
</style>
