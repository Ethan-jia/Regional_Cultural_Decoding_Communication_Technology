import Vue from 'vue'
import App from './App'

Vue.config.productionTip = false
Vue.prototype.baseUrl = "https://fina.nottingchain.com"
// http://60.190.42.226:5010
// http://10.190.190.76:8092
// https://fina.nottingchain.com
Vue.prototype.header =  {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-Requested-With': 'XMLHttpRequest'
},

App.mpType = 'app'

const app = new Vue({
  ...App
})
app.$mount()
