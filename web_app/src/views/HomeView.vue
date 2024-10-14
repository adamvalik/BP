<template>
  <div class="flex flex-col h-screen">
    <!-- Chat container -->
    <div id="chatArea" class="flex-grow p-6 overflow-y-auto bg-gray-100">
      <div v-for="(message, index) in messages" :key="index" class="mb-4">
        <div class="flex items-start" :class="{'justify-end': message.isUser}">
          <div
            class="rounded-lg p-4 max-w-xs"
            :class="message.isUser ? 'bg-blue-500 text-white ml-4' : 'bg-gray-300 text-gray-900 mr-4'"
          >
            {{ message.text }}
          </div>
        </div>
      </div>
    </div>

    <!-- Input container -->
    <div class="p-4 bg-white border-t">
      <form @submit.prevent="sendMessage">
        <div class="flex">
          <input
            v-model="newMessage"
            type="text"
            placeholder="Enter your message..."
            class="flex-grow p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" class="ml-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
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
      messages: [
        { text: 'Hello! How can I assist you today?', isUser: false },
      ],
    };
  },
  methods: {
    async sendMessage() {
      if (this.newMessage.trim() === '') return;

      // Add the user's message to the chat
      this.messages.push({
        text: this.newMessage,
        isUser: true,
      });

      // Save the message and clear the input field
      const userMessage = this.newMessage;
      this.newMessage = '';

      try {
        // Send the message to the FastAPI backend and wait for the response
        const response = await axios.post('http://127.0.0.1:8000/send-message', {
          text: userMessage,
        });

        // Add the bot's reply to the chat
        this.receiveMessage(response.data.reply);
      } catch (error) {
        console.error("Error sending message:", error);
        this.receiveMessage("Sorry, something went wrong.");
      }
    },
    receiveMessage(response) {
      this.messages.push({
        text: response,
        isUser: false,
      });

      // // Scroll to the bottom of the chat after the message is added
      // this.$nextTick(() => {
      //   const chat = this.$el.querySelector('.chat-container');
      //   chat.scrollTop = chat.scrollHeight;
      // });
    },
  },
};
</script>
