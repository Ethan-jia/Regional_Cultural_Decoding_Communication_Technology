<template>

    <view class="template-wrap">
        <swiper class="template-swiper" circular :indicator-dots="indicatorDots" :autoplay="autoplay"
            :previous-margin="25" :next-margin="25" :circular="false" @change="change">
            <swiper-item v-for="(item, index) in src_list" :key="index">
                <view class="swiper-item">
                    <video-player ref="player" :video="item.video_path" :index="index"></video-player>
                </view>
                <view class="template-title">
                    <text class="item-title">{{ item.title }}</text>
                </view>
                <view class="template-content">
                    <text class="item-content">{{ item.content }}</text>
                </view>
            </swiper-item>

        </swiper>
        <view class="template-btn">
            <button class="btn" @click="handleTemplate"><text class="btn-content">下一步</text></button>
        </view>
    </view>


</template>

<script>
import videoPlayer from '@/components/videoPlayer'


export default {
    data() {
        return {
            indicatorDots: false,
            autoplay: false,
            src_list: "",
            templateSrc: "",
            pageEndX: 0,
            page: 0,
            current: 0,
            videoNum: 0,
            templateId: "", //1:抠图 2：串接_竖版 3：串接_横板 4：ai_竖版 5：ai_横板
            minTime:"",//每个模板要求的最小时长

        };
    },
    components: {
        videoPlayer
    },
    onLoad(option) {
        this.templateId = option.templateId

        this.$nextTick(function () {
            this.getTemplate()
        })

    },
    methods: {
        //滑动发生事件
        change(e) {
            this.page = e.detail.current;
            console.log(this.page);

            if (this.current === 0) {
                if (this.page === this.videoNum - 1) {
                    console.log("向左滑动");
                    setTimeout(() => {
                        this.$refs.player[this.page].player()
                    }, 1)
                    this.$refs.player[this.current].pause()
                    this.current = this.page
                }
                else {
                    console.log("向右滑动");
                    setTimeout(() => {
                        this.$refs.player[this.page].player()
                    }, 1)
                    this.$refs.player[this.page - 1].pause()
                    this.current = this.page
                }

            }
            else if (this.current === this.videoNum - 1) {
                if (this.page === 0) {
                    console.log("向右滑动");
                    setTimeout(() => {
                        this.$refs.player[this.page].player()
                    }, 1)
                    this.$refs.player[this.videoNum - 1].pause()
                    this.current = this.page
                }
                else {
                    console.log("向左滑动");
                    setTimeout(() => {
                        this.$refs.player[this.page].player()
                    }, 1)
                    this.$refs.player[this.page + 1].pause()
                    this.current = this.page
                }

            } else {
                if (this.page > this.current) {
                    console.log("向右滑动");
                    setTimeout(() => {
                        this.$refs.player[this.page].player()
                    }, 1)
                    this.$refs.player[this.page - 1].pause()
                    this.current = this.page
                }
                else {
                    console.log("向左滑动");
                    setTimeout(() => {
                        this.$refs.player[this.page].player()
                    }, 1)
                    this.$refs.player[this.page + 1].pause()
                    this.current = this.page
                }
            }


        },
        getTemplate() {
            const that = this;
            if (that.templateId === "1") {
                uni.request({
                    url: this.baseUrl + "/templates",
                    method: "GET",
                    header:this.header,
                    data: {
                       type:"matting"
                    },
                    success(res) {
                        that.src_list = res.data;
                        that.videoNum = res.data.length

                        console.log(that.src_list);
                        console.log("====================");


                    },
                    fail(error) {
                        console.log(error);
                    }
                });
            }
            else if (that.templateId === "2") {
                uni.request({
                    url: this.baseUrl + "/templates",
                    method: "GET",
                    header:this.header,
                    data: {
                        type:"editing_vertical"
                    },
                    success(res) {
                        that.src_list = res.data;
                        that.videoNum = res.data.length
                        console.log(that.src_list);


                    },
                    fail(error) {
                        console.log(error);
                    }
                });


            }
            else if (that.templateId === "3") {
                uni.request({
                    url: this.baseUrl + "/templates",
                    method: "GET",
                    header:this.header,
                    data: {
                        type:"editing_horizontal"
                    },
                    success(res) {
                        that.src_list = res.data;
                        that.videoNum = res.data.length
                        console.log(that.src_list);


                    },
                    fail(error) {
                        console.log(error);
                    }
                });


            }
            else if (that.templateId === "4") {
                uni.request({
                    url: this.baseUrl + "/templates",
                    method: "GET",
                    header:this.header,
                    data: {
                        type: "ai_vertical"
                    },
                    success(res) {
                        that.src_list = res.data;
                        that.videoNum = res.data.length
                        console.log(that.src_list);
                    },
                    fail(error) {
                        console.log(error);
                    }
                });
            }
            else if (that.templateId === "5"){
                uni.request({
                    url: this.baseUrl + "/templates",
                    method: "GET",
                    header:this.header,
                    data: {
                        type: "ai_horizontal"
                    },
                    success(res) {
                        that.src_list = res.data;
                        that.videoNum = res.data.length
                        console.log(that.src_list);
                    },
                    fail(error) {
                        console.log(error);
                    }
                });
            }

        },

        handleTemplate() {
            this.templateSrc = this.src_list[this.page].id;
            this.minTime = this.src_list[this.page].minTime;
            console.log(this.templateSrc);
            console.log("要求最小时长：");
            console.log(this.minTime);
            uni.setStorageSync("minTime", this.minTime)

            if (this.templateId === "1") {
                uni.navigateTo({
                    url: "/pages/matting/index?templateSrc=" + this.templateSrc
                });
            }
            else if (this.templateId === "2") {
                uni.navigateTo({
                    url: "/pages/editing/index?templateSrc=" + this.templateSrc
                });
            }
            else if (this.templateId === "3") {
                uni.navigateTo({
                    url: "/pages/editing/index?templateSrc=" + this.templateSrc 
                });
            }
            else if (this.templateId === "4"){
                uni.navigateTo({
                    url: "/pages/aiEditing/index?templateSrc=" + this.templateSrc 
                });
            }
            else if (this.templateId === "5"){
                uni.navigateTo({
                    url: "/pages/aiEditing/index?templateSrc=" + this.templateSrc 
                });
            }

        },

    },
};
</script>

<style lang="scss">
.template-wrap {
    display: flex;
    flex-direction: column;
    width: 100%;
    background-color: black;

    .template-swiper {
        height: 100vh;
        background-color: black;

        .swiper-item {
            display: block;
            margin-top: 20px;
            line-height: 100rpx;
            text-align: center;

            .swiper-video {
                height: 70vh;
                width: 80vw;
                border-radius: 6px;
            }

        }

        .template-title {
            color: #ffffff;
            margin-left: 25px;
            margin-right: 25px;
            line-height: 50px;
            .item-title{
                letter-spacing: 1px;
            }
        }

        .template-content {
            color: #ffffff;
            margin-left: 25px;
            margin-right: 25px;
            .item-content{
                font-size: 12px;
                color:#969696 ;
            }
        }
    }

    .template-btn {
        margin-top: -20%;
        width: 100vw;
        background-color: black;

        .btn {
            width: 80vw;
            height: 4vh;
            background-color: #4cca78;
            border-radius: 15px;
            display: flex;
            justify-content: center;
            align-items: center;

            .btn-content {
                font-size: 14px;
                color: #ffffff;
                letter-spacing: 2px;



            }

        }
    }
}
</style>
