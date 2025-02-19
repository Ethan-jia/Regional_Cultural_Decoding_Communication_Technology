<template>
  <view class="myVideo-wrap">
    <view class="myVideo-title">
      <text class="title">--每页显示生成的三条视频--</text>
    </view>
    <view v-for="(item, index) in current_list" :key="index" class="myVideo-content">
      <view class="myVideo">
        <view class="picture-content">
          <img :src="item.imgSrc" class="picture" @click="handleShow(item.videoSrc)" />
        </view>
        <view class="videoInfo">
          <view class="info1">
            <text class="createDate">{{ item.CreateDate }}</text>
            <text class="validDate">有效期至 {{ item.ValidDate }}</text>
          </view>
          <view class="info2">
            <button class="btn1" @click="handleShow(item.videoSrc)">预览</button>
            <button v-if="item.payStatus === 0" class="btn2" @click="handleDownload(index)">下载</button>
            <button v-else class="btn2" @click="handleDownload(index)">重新下载</button>
            <button class="btn3" @click="handleDelete(index)">删除</button>
          </view>

        </view>
      </view>
    </view>
    <uni-pagination :total="total" :current="current_page" prev-text="上一页" next-text="下一页" @change="handlePage"></uni-pagination>
    <view class="bottom-content">
      <img :src="bg_pic" class="bottom-pic" />
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      bg_pic: this.baseUrl + '/image/bg_pic.png/',
      video_list: [],  //总数据
      current_list: [],  //当前数据
      openId: "",
      total: "",
      current_page:""
    };
  },
  onShow() {
    this.openId = uni.getStorageSync("openId")
    this.getMyVideo(1)

  },
  methods: {
    getMyVideo(page) {
      const that = this
      uni.request({
        url: that.baseUrl + "/queryMyVideo",
        method: "GET",
        header: that.header,
        data: {
          openId: that.openId
        },
        success(res) {
          if (res.statusCode === 200) {
            that.video_list = res.data
            that.total = that.video_list.length / 3 * 10
            console.log(that.video_list);
            console.log(that.total);
            if(page === 1){
              that.current_page=1
              that.current_list = that.video_list.slice(0, 3)
            }
            else{
              that.current_page=page
              that.current_list = that.video_list.slice((that.current_page - 1) * 3, that.current_page * 3)
            }
          }
          else {
            console.log(res.statusCode);
          }
        },
        fail(error) {
          console.log(error);
        }
      });
    },
    handleShow(videoSrc) {
      console.log(videoSrc);
      uni.navigateTo({
        url: "/pages/videoPlay/index?url=" + videoSrc + "&status=2"
      })
    },
    handleDownload(index) {
      const that = this
      if (that.current_list[index].payStatus === 0) {
        setTimeout(() => {
          uni.request({
            url: that.baseUrl + "/get/orderId",
            method: "GET",
            header: that.header,
            timeout: 10000,
            data: {
              "secretKey": that.current_list[index].secretKey,
              "openId": that.openId,
            },
            success(res) {
              if (res.data.code == "OK") {
                let goods_order = res.data.orderId
                uni.navigateTo({
                  url: "/pages/payMoney/index?goods_order=" + goods_order + "&url=" + that.current_list[index].videoSrc + "&secretKey=" +
                    that.current_list[index].secretKey
                })
              }


            },
          })
        }, 100);
      }
      else {
        uni.navigateTo({
          url: "/pages/videoPlay/index?url=" + that.video_list[index].videoSrc + "&status=1"
        })
      }

    },
    handleDelete(index) {
      const that = this
      uni.showModal({
        title: '是否删除',
        success(res) {
          if (res.confirm) {
            uni.request({
              url: that.baseUrl + "/videos/remove",
              method: "GET",
              header: that.header,
              timeout: 10000,
              data: {
                "secretKey": that.current_list[index].secretKey,
                "openId": that.openId,
              },
              success(res) {
                console.log(res);
                if (res.data.code == "OK") {
                  console.log('2312312312');
                  console.log(that.current_page);
                  setTimeout(() => {
                    that.getMyVideo(that.current_page)
                  }, 1000);
                  uni.showToast({
                    title: "删除成功!",
                    duration: 1000,
                  })
                }
                else {
                  uni.showToast({
                    title: "删除失败!",
                    duration: 1500,
                    icon: "error",
                  })
                }
              },
            })
          }
          else if (res.cancel) {
            console.log("拒绝删除");
          }

        }
      })
    },
    handlePage(res) {
      console.log(res.current);
      this.current_page = res.current 
      this.current_list = this.video_list.slice((res.current - 1) * 3, res.current * 3)

    }


  },
};
</script>

<style lang="scss">
.myVideo-wrap {

  position: absolute;
  width: 100vw;
  height: 100vh;

  .myVideo-title {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 2vh;

    .title {
      font-size: 12px;
      color: #999999;
    }
  }

  .myVideo-content {

    width: 90vw;
    margin-left: 5vw;
    // height: 5vh;

    .myVideo {
      width: 100vw;
      display: flex;
      flex-direction: row;
      margin-top: 2vh;


      .picture-content {

        .picture {
          width: 30vw;
          height: 14vh;
        }
      }

      .videoInfo {
        display: flex;
        flex-direction: row;
        margin-left: 1vw;

        .info1 {
          display: flex;
          flex-direction: column;
          margin-left: 2.5vw;
          margin-top: 2vh;

          .createDate {
            font-size: 15px;
            font-weight: bold;
            margin-top: 0.5vh;

          }

          .validDate {
            font-size: 11px;
            color: #999999;
            margin-top: 2.5vh;

          }
        }

        .info2 {
          display: flex;
          flex-direction: column;


          .btn1 {
            font-size: 11px;
            color: #999999;
            background-color: white;
            position: absolute;
            right: 0;
            margin-right: 2vw;
          }

          .btn2 {
            font-size: 11px;
            color: #999999;
            background-color: white;
            position: absolute;
            right: 0;
            margin-right: 2vw;
            margin-top: 5vh;
          }

          .btn3 {
            font-size: 11px;
            color: #999999;
            background-color: white;
            position: absolute;
            right: 0;
            margin-right: 2vw;
            margin-top: 10vh;
          }




        }


      }
    }
  }

  .uni-pagination {
    width: 90vw;
    margin-left: 5vw;
    margin-top: 2vh;
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
