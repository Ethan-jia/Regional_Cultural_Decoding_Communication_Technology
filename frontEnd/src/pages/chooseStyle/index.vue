<template>
    <view class="choose-wrap">
        <view class="choose-title">
            <image src="/static/images/tu4.png" class="title-picture" />
            <text class="text-content">视频横纵项选择</text>
        </view>
        <view class="btn1-content">
            <image :src="vertical_pic" class="vertical" @click="handleGoStep1" />
        </view>
        <view class="btn2-content">
            <image :src="horizontal_pic" class="horizontal" @click="handleGoStep2" />
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
            vertical_pic: this.baseUrl + '/image/vertical.png/',
            horizontal_pic: this.baseUrl + '/image/horizontal.png/',
            bg_pic: this.baseUrl + '/image/bg_pic.png/',
            type: "",
        }
    },
    onLoad(option) {
        this.type = option.type
        console.log(this.type);
    },
    methods: {
        handleGoStep1() {

            uni.setStorageSync("styleId", "1")
            setTimeout(() => {
                if (this.type === "aiEditing") {
                    uni.navigateTo({
                        url: "/pages/aiEditing/index"
                    })
                }
                else if (this.type === "editing") {
                   
                    uni.navigateTo({
                        url: "/pages/editing/index"
                    })
                }

            }, 100)

        },
        handleGoStep2() {

            uni.setStorageSync("styleId", "2")
            setTimeout(() => {
                if (this.type === "aiEditing") {
                    uni.navigateTo({
                        url: "/pages/aiEditing/index"
                    })
                }
                else if (this.type === "editing") {
                    uni.navigateTo({
                        url: "/pages/editing/index"
                    })
                }

            }, 100)
        },
    }

}
</script>

<style lang="scss">
.choose-wrap {
    width: 100vw;

    .choose-title {
        display: flex;
        flex-direction: row;
        margin-left: 5vw;
        margin-top: 3vh;

        .title-picture {
            width: 20px;
            height: 20px;
        }

        .text-content {
            margin-left: 3vw;
            font-weight: bold;
            letter-spacing: 0.5px;

        }
    }

    .btn1-content {
        margin-top: 2vh;


        .vertical {
            margin-left: 5vw;
            width: 90vw;
            height: 19vh;
        }


    }

    .btn2-content {
        margin-top: 2vh;

        .horizontal {
            margin-left: 5vw;
            width: 90vw;
            height: 19vh;
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