<template>
	<view class="travel-wrap">
		<view class="travel-picture">
			<uni-swiper-dot :info="info" :current="current" :mode="mode" :dots-styles="dotsStyles">
				<swiper class="swiper-box" autoplay="auto" @change="change1">
					<swiper-item v-for="(item, index) in info" :key="index">
						<view class="swiper-item">
							<img :src="item.image" class="picture" />
						</view>
					</swiper-item>
				</swiper>
			</uni-swiper-dot>
			<view class="myVideo-wrap">
				<img v-if="videoStatus !== 1" src="/static/images/mine1.png" class="myVideo" @click="handleGoMyVideo" />
				<img v-if="videoStatus === 1" src="/static/images/mine2.png" class="myVideo" @click="handleGoMyVideo" />
			</view>
		</view>
		<uni-popup ref="popup1" type="center" :is-mask-click="false">
			<view class="privacy-wrap">
				<view class="privacy-title">用户信息授权说明</view>
				<view class="privacy-content">
					<text style="text-indent: 2em;text-align: left;">授权后,小程序开发者将收集您的微信昵称、头像,为您提供相关服务。开发者严格按照</text>
					<text style="color:#4cca78" @click="handleGoPrivacy">《爱游记小程序隐私保护指引》</text>
					<text>处理您的个人信息,如您发现开发者不当处理您的个人信息,可进行投诉。</text>
				</view>
				<view class="button-wrap">
					<button class="button1" @click="unAccpet">暂不使用</button>
					<button class="button2" @click="close('privacy')">同意</button>
				</view>
			</view>
		</uni-popup>
		<uni-popup ref="popup2" type="center" :is-mask-click="false">
			<view class="guide-wrap">
				<swiper class="guide-swiper" :indicator-dots="true" indicator-color=rgba(199,237,211)
					indicator-active-color=rgba(76,201,120) @change="change2">
					<swiper-item v-for="(item, index) in guideInfo" :key="index">
						<img :src="item.image" class="picture" />
					</swiper-item>
				</swiper>
				<image v-if="guideCurrent === 3" src="/static/images/X.png" class="cancel" @click="close('guide')" />
			</view>
		</uni-popup>
		<view class="travel-content">
			<view class="content-matting">
				<img src="/static/images/btn1.png" class="picture-btn1" />
				<view class="btn1-content">
					<view class="btn1-title">
						<img src="/static/images/tu1.png" class="btn1-tu1" />
						<view class="btn1-text">视频同款生成</view>
					</view>
					<view class="btn1-temp">简单3步, 轻松生成趣味视频</view>
					<button class="btn1" @click="handleGoVideo(url1)">
						<img src="/static/images/play.png" style="width: 10px;height:10px;margin-top: 10px;" />
						<view style="letter-spacing: 1px;margin-left: 10px;">效果预览</view>
					</button>
					<button class="btn1-make" @click="doTest(1)">
						<view style="letter-spacing: 1px;">开始制作</view>
					</button>
				</view>
			</view>
			<view class="content-editing">
				<img src="/static/images/btn2.png" class="picture-btn2" />
				<view class="btn2-content">
					<view class="btn2-title">
						<img src="/static/images/tu2.png" class="btn2-tu2" />
						<view class="btn2-text">视频剪辑串编</view>
					</view>
					<view class="btn2-temp">无须剪辑, 上传视频, 一键生成</view>
					<button class="btn2" @click="handleGoVideo(url2)">
						<img src="/static/images/play.png" style="width: 10px;height:10px;margin-top: 10px;" />
						<view style="letter-spacing: 1px;margin-left: 10px;">效果预览</view>
					</button>
					<button class="btn2-make" @click="doTest(2)">
						<view style="letter-spacing: 1px;">开始制作</view>
					</button>
				</view>
			</view>
			<view class="content-aiediting">
				<img src="/static/images/btn3.png" class="picture-btn3" />
				<view class="btn3-content">
					<view class="btn3-title">
						<img src="/static/images/tu3.png" class="btn3-tu3" />
						<view class="btn3-text">AI融合剪辑</view>
					</view>
					<view class="btn3-temp">智能识别, 生成游记视频, 记录难忘瞬间</view>
					<button class="btn3" @click="handleGoVideo(url3)">
						<img src="/static/images/play.png" style="width: 10px;height:10px;margin-top: 10px;" />
						<view style="letter-spacing: 1px;margin-left: 10px;">效果预览</view>
					</button>
					<button class="btn3-make" @click="doTest(3)">
						<view style="letter-spacing: 1px;">开始制作</view>
					</button>
				</view>
			</view>
		</view>

	</view>


</template>

<script>




export default {
	components: {

	},

	data() {
		return {
			info: [],
			guideInfo: [{
				image: this.baseUrl + '/image/langzhong/guide1.png/'
			}, { image: this.baseUrl + '/image/langzhong/guide2.png/' },
			{ image: this.baseUrl + '/image/langzhong/guide3.png/' },
			{ image: this.baseUrl + '/image/langzhong/guide4.png/' }],
			current: 0,
			guideCurrent: 0,
			mode: 'dot',
			dotsStyles: {
				backgroundColor: 'rgba(200, 200, 200, .3)',
				border: '1px rgba(200, 200, 200, .3) solid',
				color: '#fff',
				bottom: 35,
				selectedBackgroundColor: 'rgba(240, 240, 240, .9)',
				selectedBorder: '1px rgba(240, 240, 240, .9) solid'
			},
			url1: this.baseUrl + "/templates/matting_1.mp4/",
			url2: this.baseUrl + "/templates/editing_1.mp4/",
			url3: this.baseUrl + "/templates/ai_1.mp4/",
			userCode: "",
			userInfo: "",
			openId: "",  //用户唯一标识
			secretKey: "",  //当前操作key
			videoStatus: "", // 0:已读 1:未读
		}
	},
	onLaunch() {

	},
	onShow() {

		if (uni.getStorageSync("styleId")) {
			uni.removeStorageSync("styleId")

		}


		let userInfo = uni.getStorageSync("userInfo")
		let userCode = uni.getStorageSync('userCode')
		let openId = uni.getStorageSync('openId')
		this.getSwipePic()

		console.log(userInfo);
		console.log(userCode);
		console.log("===========");


		console.log(uni.getStorageSync("status"));
		if (userCode && userInfo) {
			this.userInfo = userInfo
			this.userCode = userCode
			console.log("--------------");
			console.log(this.userInfo);
			console.log(this.userCode);
			if (uni.getLaunchOptionsSync() !== '' && uni.getStorageSync('status') === 0) {
				this.open('guide')
				uni.setStorageSync("status", 1)
			}
			console.log(uni.getStorageSync("status"));


		}
		else {
			this.open('privacy')

		}


		if (openId) {
			this.openId = openId
			//发送登录次数
			if (uni.getStorageSync('login_status') === 0) {
				uni.request({
					url: this.baseUrl + "/get/loginNum",
					method: "GET",
					header: this.header,
					data: {
						openId: this.openId,
					},
					success(res) {
						console.log(res);
						console.log('78798798798');
						uni.setStorageSync("login_status", 1)
					},
					fail(error) {
						console.log(error);

					}
				});
			}

			this.getVideoStauts() //获取视频读取状态

		}
		else if (userCode && userInfo && !openId) {
			uni.showModal({
				title: "登录信息已过期,请重新授权登录",
				content: "是否授权",
				showCancel: false,
				success: () => {
					this.getUserInfo()
				}
			})
		}






	},

	onLoad() {
		uni.showShareMenu({
			withShareTicket: true,
			menus: ["shareAppMessage", "shareTimeline"]

		})
	},
	//发送给朋友
	onShareAppMessage(res) {
		return {
			title: "爱游记",
			path: '/pages/travel/index',
			imageUrl: this.baseUrl + '/image/langzhong/1.jpg/'
		}
	},
	//分享到朋友圈
	onShareTimeline(res) {
		return {
			title: "爱游记",
			query: '/pages/travel/index',
			imageUrl: this.baseUrl + '/image/langzhong/1.jpg/'
		}
	},



	methods: {
		change1(e) {
			this.current = e.detail.current;
		},
		change2(e) {
			this.guideCurrent = e.detail.current;
		},

		//效果预览点击事件
		handleGoVideo(e) {
			uni.navigateTo({
				url: "/pages/videoPlay/index?url=" + e + "&status=0"
			})



		},
		async doTest(res) {
			if (!this.openId) {
				uni.showModal({
					title: "登录信息已过期,请重新授权登录",
					content: "是否授权",
					showCancel: false,
					success: () => {
						this.getUserInfo()
					}
				})
			}
			else {

				if (res === 1) {
					await this.handleGoMatting();
					uni.navigateTo({
						url: "/pages/matting/index"
					})
				}
				else if (res === 2) {
					await this.handleGoEditing();
					uni.navigateTo({
						url: "/pages/chooseStyle/index?type=editing"
					})
				}
				else {
					await this.handleGoAIEditing();
					uni.navigateTo({
						url: "/pages/chooseStyle/index?type=aiEditing"
					})
				}
			}

		},
		handleGoMatting() {

			const that = this;
			return new Promise((resolve, reject) => {
				uni.request({
					url: this.baseUrl + "/get/secretKey",
					method: "GET",
					header: this.header,
					data: {
						openId: that.openId,
						type: "matting"
					},
					success(res) {
						that.secretKey = res.data.secretKey
						uni.setStorageSync("secretKey", that.secretKey)
						console.log(that.secretKey);
						resolve("success")
					},
					fail(error) {
						console.log(error);
						reject("error")
					}
				});
			})

		},
		handleGoEditing() {
			const that = this;
			return new Promise((resolve, reject) => {
				uni.request({
					url: this.baseUrl + "/get/secretKey",
					method: "GET",
					header: this.header,
					data: {
						openId: that.openId,
						type: "editing"
					},
					success(res) {
						that.secretKey = res.data.secretKey
						uni.setStorageSync("secretKey", that.secretKey)
						console.log(that.secretKey);
						resolve("success")
					},
					fail(error) {
						console.log(error);
						reject("error")
					}
				});
			})

		},
		handleGoAIEditing() {
			const that = this;
			return new Promise((resolve, reject) => {
				uni.request({
					url: this.baseUrl + "/get/secretKey",
					method: "GET",
					header: this.header,
					data: {
						openId: that.openId,
						type: "aiEditing"
					},
					success(res) {
						that.secretKey = res.data.secretKey
						uni.setStorageSync("secretKey", that.secretKey)
						console.log(that.secretKey);
						resolve("success")
					},
					fail(error) {
						console.log(error);
						reject("error")
					}
				});
			})

		},
		getUserInfo() {
			const that = this;
			uni.getUserProfile({
				desc: "用以获取用户昵称、头像等",
				success(res) {
					that.userInfo = res.userInfo
					uni.setStorageSync("userInfo", that.userInfo)
					console.log(that.userInfo);
					uni.login({
						provider: "weixin",
						success: (result) => {
							that.userCode = result.code;
							uni.setStorageSync("userCode", that.userCode)
							console.log(that.userCode);
							uni.request({
								url: that.baseUrl + "/get/openId",
								method: "GET",
								header: that.header,
								data: {
									userInfo: that.userInfo,
									userCode: that.userCode,
								},
								success: (res) => {
									that.openId = res.data.openId
									console.log(that.openId);
									uni.setStorageSync("openId", that.openId)
									that.getVideoStauts()  //获取视频读取状态
									uni.showToast({
										title: "登录成功",
										duration: 1500,
									})

								},
								fail: (error) => {
									console.log(error);
								}
							})

						},
						fail: (error) => {
							console.log(error);
						}
					})
				},
				fail() {
					uni.showToast({
						title: "未授权",
						duration: 1500,
						icon: "error"
					})
				}

			})

		},
		open(res) {
			if (res === "privacy") {
				this.$refs.popup1.open('center')
			}
			else {
				this.$refs.popup2.open('center')
			}
		},
		close(res) {
			if (res === "privacy") {
				this.$refs.popup1.close()
				this.getUserInfo()
				setTimeout(() => {
					this.open("guide")   //打开指引页
				}, 2000);

			}
			else {
				this.$refs.popup2.close()
			}
		},
		handleGoPrivacy() {
			uni.navigateTo({
				url: "/pages/privacyContent/index"
			})
		},
		unAccpet() {
			uni.showToast({
				title: "须同意再使用",
				duration: 1500,
				icon: "error"
			})
		},
		handleGoMyVideo() {
			if (this.openId) {
				uni.navigateTo({
					url: "/pages/myVideo/index"
				})
			}
			else {
				uni.showModal({
					title: "未登录,请授权登录",
					content: "是否授权",
					showCancel: false,
					success: () => {
						this.getUserInfo()
					}
				})
			}
		},
		getVideoStauts() {
			const that = this
			uni.request({
				url: that.baseUrl + "/queryStatus",
				method: "GET",
				header: that.header,
				data: {
					openId: that.openId
				},
				success: (res) => {
					that.videoStatus = res.data.videoStatus
					console.log(typeof that.videoStatus);
				},
				fail: (error) => {
					console.log(error);
				}

			})
		},
		getSwipePic() {
			const that = this
			uni.request({
				url: that.baseUrl + "/swipePic",
				method: "GET",
				header: that.header,
				success: (res) => {
					that.info = res.data
					console.log(that.info);
				},
				fail: (error) => {
					console.log(error);
				}

			})
		}
	}
};
</script>

<style lang="scss">
.travel-wrap {

	.privacy-wrap {
		background-color: rgb(243, 243, 243);
		width: 60vw;
		height: 35vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		border-radius: 3%;

		.privacy-title {
			font-size: 18px;
			font-weight: bold;
			letter-spacing: 1px;
			margin-top: 2vh;


		}

		.privacy-content {
			width: 55vw;
			font-size: 14px;
			letter-spacing: 1px;
			margin-left: 3vw;
			margin-top: 2vh;
		}

		.button-wrap {

			display: flex;
			flex-direction: row;
			height: 4vh;
			position: absolute;
			bottom: 0;
			margin-bottom: 1.5vh;

			.button1 {
				width: 30vw;
				font-weight: bold;
				font-size: 15px;
				background-color: rgb(243, 243, 243);
			}

			.button1::after {
				border: none;
			}

			.button2 {
				width: 30vw;
				color: #4cca78;
				font-size: 15px;
				background-color: rgb(243, 243, 243);
			}

			.button2::after {
				border: none;
			}
		}

	}

	.guide-wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
		background-color: white;
		width: 70vw;
		height: 70vh;

		.guide-swiper {
			position: absolute;
			width: 70vw;
			height: 68vh;

			.picture {
				width: 70vw;
				height: 68vh;
			}

		}

		.cancel {
			height: 70rpx;
			width: 70rpx;
			margin-top: 74vh;
			position: absolute;
		}

	}

	.travel-picture {

		display: flex;
		flex-direction: column;
		z-index: -50;

		.myVideo-wrap {
			position: absolute;
			right: 0;
			margin-right: 2vw;
			top: 0;
			margin-top: 1.5vh;

			.myVideo {
				width: 80rpx;
				height: 80rpx;
			}
		}

		.swiper-box {
			height: 35vh;

			.swiper-item {
				/* #ifndef APP-NVUE */
				display: flex;
				/* #endif */
				flex-direction: column;
				justify-content: center;
				align-items: center;

				.picture {
					width: 100vw;
					height: 35vh;
				}
			}
		}

	}

	.travel-content {
		margin-top: -20px;
		background-color: #4cca78;
		width: 100vw;
		height: 70vh;
		border-top-left-radius: 5%;
		border-top-right-radius: 5%;
		position: absolute;

		.content-matting {
			display: flex;
			flex-direction: column;
			position: relative;
			margin-top: 5%;
			padding-left: 5%;
			padding-right: 5%;

			.picture-btn1 {
				height: 18vh;
				width: 90vw;

			}

			.btn1-content {
				position: absolute;
				display: flex;
				flex-direction: column;



				.btn1-title {
					display: flex;
					flex-direction: row;
					margin-top: 2vh;
					margin-left: 3vw;

					.btn1-tu1 {
						width: 20px;
						height: 20px;
					}

					.btn1-text {
						color: #111;
						margin-left: 3vw;
						font-weight: bold;
						letter-spacing: 1px;
					}
				}

				.btn1-temp {

					margin-left: 3vw;
					margin-top: 1.5vh;
					color: #999;
					font-size: 12px;

				}

				.btn1 {
					display: flex;
					flex-direction: row;
					position: absolute;
					margin-left: 3vw;
					margin-top: 12vh;
					color: #4cca78;
					font-size: 12px;
					border: 1px solid #4cca78;
				}

				.btn1-make {
					position: absolute;
					margin-left: 32vw;
					margin-top: 12vh;
					width: 25vw;
					color: #4cca78;
					font-size: 12px;
					border: 1px solid #4cca78;
					display: flex;
					justify-content: center;
					align-items: center;
				}

			}


		}

		.content-editing {
			display: flex;
			flex-direction: column;
			position: relative;
			margin-top: 5%;
			padding-left: 5%;
			padding-right: 5%;

			.picture-btn2 {
				height: 18vh;
				width: 90vw;

			}

			.btn2-content {
				position: absolute;
				display: flex;
				flex-direction: column;



				.btn2-title {
					display: flex;
					flex-direction: row;
					margin-top: 2vh;
					margin-left: 3vw;

					.btn2-tu2 {
						width: 20px;
						height: 20px;
					}

					.btn2-text {
						color: #111;
						margin-left: 3vw;
						font-weight: bold;
						letter-spacing: 1px;
					}
				}

				.btn2-temp {

					margin-left: 3vw;
					margin-top: 1.5vh;
					color: #999;
					font-size: 12px;

				}

				.btn2 {
					display: flex;
					flex-direction: row;
					position: absolute;
					margin-left: 3vw;
					margin-top: 12vh;
					color: #4cca78;
					font-size: 12px;
					border: 1px solid #4cca78;




				}

				.btn2-make {
					position: absolute;
					margin-left: 32vw;
					margin-top: 12vh;
					width: 25vw;
					color: #4cca78;
					font-size: 12px;
					border: 1px solid #4cca78;
					display: flex;
					justify-content: center;
					align-items: center;
				}

			}


		}

		.content-aiediting {
			display: flex;
			flex-direction: column;
			position: relative;
			margin-top: 5%;
			padding-left: 5%;
			padding-right: 5%;

			.picture-btn3 {
				height: 18vh;
				width: 90vw;

			}

			.btn3-content {
				position: absolute;
				display: flex;
				flex-direction: column;



				.btn3-title {
					display: flex;
					flex-direction: row;
					margin-top: 2vh;
					margin-left: 3vw;

					.btn3-tu3 {
						width: 20px;
						height: 20px;
					}

					.btn3-text {
						color: #111;
						margin-left: 3vw;
						font-weight: bold;
						letter-spacing: 1px;
					}
				}

				.btn3-temp {
					margin-left: 3vw;
					margin-top: 1.5vh;
					color: #999;
					font-size: 12px;

				}

				.btn3 {
					display: flex;
					flex-direction: row;
					position: absolute;
					margin-left: 3vw;
					margin-top: 12vh;
					color: #4cca78;
					font-size: 12px;
					border: 1px solid #4cca78;




				}

				.btn3-make {
					position: absolute;
					margin-left: 32vw;
					margin-top: 12vh;
					width: 25vw;
					color: #4cca78;
					font-size: 12px;
					border: 1px solid #4cca78;
					display: flex;
					justify-content: center;
					align-items: center;
				}

			}


		}

	}
}
</style>
