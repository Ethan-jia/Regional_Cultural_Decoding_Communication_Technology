<template>
  <view class="status-wrap">
    <img v-if="id === '1'" :src="success_pic" class="status" />
    <img v-else :src="fail_pic" class="status" />
    <button v-if="id === '1'" @click="backHome" class="back-home">
      <text>返回主页</text>
    </button>
    <button v-else @click="back" class="back"><text>返回</text></button>
    <img :src="bg_pic" class="bottom-pic" />
  </view>
</template>

<script>
export default {
  data() {
    return {
      id: "", //1：成功，0：失败
      success_pic: this.baseUrl + "/image/save_success.jpg/",
      fail_pic: this.baseUrl + "/image/save_fail.jpg/",
      bg_pic: this.baseUrl + '/image/bg_pic.png/'
    };
  },
  onLoad(option) {
    this.id = option.id;
    console.log(this.id);
  },
  methods: {
    backHome() {
      uni.reLaunch({
        url: "/pages/travel/index",
      });
    },
    back() {
      uni.navigateBack({
        delta: 2,
      });
    },
  },
};
</script>

<style lang="scss">
.status-wrap {
  width: 100vw;

  .status {
    width: 100vw;
    height: 45vh;
  }

  .back-home {
    height: 5vh;
    width: 40vw;
    color: white;
    background-color: #4cca78;
    font-size: 16px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 16px;
  }

  .back {
    height: 5vh;
    width: 40vw;
    color: white;
    background-color: #4cca78;
    font-size: 16px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 16px;
  }

  .bottom-pic {
    width: 100vw;
    height: 35vh;
    position: fixed;
    bottom: 0;
  }
}
</style>
