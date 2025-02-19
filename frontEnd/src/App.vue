
<script>
export default {
	onLaunch: function () {
		console.log('App Launch')
		uni.setStorageSync("status", 0)
		uni.setStorageSync("login_status", 0)
	},
	onShow: function () {
		console.log('App Show')
	},
	onHide: function () {
		console.log('App Hide')
	}

}
</script>

<style>
/*每个页面公共css */
html,
body {
	height: 100%;
	width: 100%;
}

page {
	height: 100%;
}
</style>
