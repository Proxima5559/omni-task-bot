import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'bulma/css/bulma.min.css'
import './styles/theme.css'
import './styles/app.css'
import App from './App.vue'

createApp(App).use(createPinia()).mount('#app')
