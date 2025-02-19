<template>
  <video
    id="myVideo"
    class="video"
    object-fit="fill"
    :control="false"
    :src="video"
    :loop="true"
    :autoplay="autoplay"
    controls
    @click="click"
  ></video>
</template>

<script>
export default {
  name: "videoPlayer",
  props: {
    video: String,
    index: Number,
  },
  data() {
    return {
      play: false,
      autoplay: false,
    };
  },
  mounted() {
    this.videoContext = uni.createVideoContext("myVideo", this);
    // console.log(this.videoContext);
  },
  // created() {
  //   this.auto();
  // },
  methods: {
    click() {
      if (this.play == false) {
        this.playThis();
      } else {
        this.pause();
      }
    },
    player() {
      //从头播放视频
      if (this.play == false) {
        this.videoContext.seek(0);
        this.videoContext.play();
        this.play = true;
      }
    },
    pause() {
      //暂停视频
      if (this.play == true) {
        this.videoContext.pause();
        this.play = false;
      }
    },
    playThis() {
      //播放当前视频
      if (this.play == false) {
        this.videoContext.play();
        this.play = true;
      }
    },
    // 首个视频自动播放
    auto() {
      if (this.index === 0) {
        this.autoplay = true;
      }
    },
  },
};
</script>

<style lang="scss">
.video {
  height: 70vh;
  width: 80vw;
  border-radius: 6px;
}
</style>
