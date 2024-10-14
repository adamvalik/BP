<template>
  <div class="flex flex-col h-screen p-16">
    <!-- 2 buttons - user view and dev mode for switching the reply format -->
    <div class="flex justify-start">
      <button class="px-4 py-2 bg-blue-500 text-white rounded-t-xl hover:bg-blue-600" :class="{'bg-blue-600' : !devMode}" @click="switchView">User View</button>
      <button class="px-4 py-2 bg-blue-500 text-white rounded-t-xl hover:bg-blue-600" :class="{'bg-blue-600' : devMode}" @click="switchView">Dev Mode</button>
    </div>
    <div id="chatArea" class="flex-grow p-8 rounded-xl overflow-y-auto bg-gray-100">
      <div v-for="(message, index) in messages" :key="index" class="mb-4">
        <div class="flex items-start" :class="{'justify-end': message.isUser}">
          <div
            class="rounded-xl p-4 max-w-3xl"
            :class="message.isUser ? 'bg-blue-500 text-white ml-4' : 'bg-gray-300 text-gray-900 mr-4'"
          >
            <template v-if="!message.isUser && devMode">
              <div>{{ message.text }}</div>
              <div v-if="message.metadata" class="text-xs text-gray-500 mt-2">
                <div v-for="(value, key) in message.metadata" :key="key">
                  <strong>{{ key }}:</strong> {{ value }}
                </div>
              </div>
            </template>

            <template v-else-if="!message.isUser && !devMode">
              <div>{{ message.text }}</div>
              <div v-if="message.metadata" >Source: {{ message.metadata.link }}</div>
            </template>

            <template v-else>
              <div>{{ message.text }}</div>
            </template>  
          </div>
        </div>
      </div>
    </div>

    <div class="p-4 bg-white">
      <form @submit.prevent="sendMessage">
        <div class="flex">
          <input
            v-model="newMessage"
            type="text"
            placeholder="Enter your question..."
            class="flex-grow p-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" class="ml-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600">
            Send
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      newMessage: '',
      messages: [],
      devMode: false,
    };
  },
  methods: {
    switchView() {
      this.devMode = !this.devMode;
    },
    async sendMessage() {
      if (this.newMessage.trim() === '') return;

      // add the user's message to the chat
      this.messages.push({
        text: this.newMessage,
        isUser: true,
      });

      // save the message and clear the input field
      const userMessage = this.newMessage;
      this.newMessage = '';

      try {
        // send the message to the FastAPI backend and wait for the response
        const response = await axios.post('http://127.0.0.1:8000/send-message', {
          text: userMessage,
        });

        // add the reply to the chat
        this.receiveMessage(response.data);
      } catch (error) {
        console.error("Error sending message:", error);
        this.receiveMessage("Sorry, something went wrong.");
      }
    },
    receiveMessage(data) {
      this.messages.push({
        text: data.reply_msg,
        metadata: data.metadata,
        isUser: false,
      });

      // scroll to the bottom of the chat after the message is added
      this.$nextTick(() => {
        const chat = this.$el.querySelector('#chatArea');
        chat.scrollTop = chat.scrollHeight;
      });
    },
  },
};
</script>
