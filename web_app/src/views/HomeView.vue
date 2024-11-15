<template>
  <div class="flex flex-col h-screen px-20 py-10 bg-gray-900 text-gray-200">
    <div class="flex justify-between items-center">
      <!-- modes -->
      <div class="flex pl-3">
        <button
          class="px-4 py-2 text-white rounded-t-xl hover:bg-teal-500"
          :class="[devMode ? 'bg-teal-600' : 'bg-teal-500']"
          @click="switchView"
        >
          User View
        </button>
        <button
          class="px-4 py-2 text-white rounded-t-xl hover:bg-teal-500"
          :class="[!devMode ? 'bg-teal-600' : 'bg-teal-500']"
          @click="switchView"
        >
          Dev Mode
        </button>
      </div>

      <!-- roles -->
      <div class="flex items-center space-x-4 pr-4">
        <label class="text-sm text-gray-300">User Role:</label>
        <!-- normal role -->
        <label
          class="flex items-center space-x-2 cursor-pointer"
          :class="{'text-teal-400': userRole === 'normal', 'text-gray-300': userRole !== 'normal'}"
        >
          <input
            type="radio"
            value="normal"
            v-model="userRole"
            class="hidden"
          />
          <div
            class="w-4 h-4 border-2 rounded-full"
            :class="userRole === 'normal' ? 'bg-teal-500 border-teal-500' : 'border-gray-400'"
          ></div>
          <span>Normal</span>
        </label>

        <!-- superior role -->
        <label
          class="flex items-center space-x-2 cursor-pointer"
          :class="{'text-teal-400': userRole === 'superior', 'text-gray-300': userRole !== 'superior'}"
        >
          <input
            type="radio"
            value="superior"
            v-model="userRole"
            class="hidden"
          />
          <div
            class="w-4 h-4 border-2 rounded-full"
            :class="userRole === 'superior' ? 'bg-teal-500 border-teal-500' : 'border-gray-400'"
          ></div>
          <span>Superior</span>
        </label>
      </div>
    </div>

    <!-- chat area -->
    <div id="chatArea" class="flex-grow p-8 rounded-xl overflow-y-auto bg-gray-800">
      <div v-for="(message, index) in messages" :key="index" class="mb-4">
        <div class="flex items-start" :class="{'justify-end': message.isUser}">
          <div
            class="rounded-xl p-4 max-w-3xl break-words"
            :class="[
              message.isUser ? 'bg-teal-600 text-white ml-4' : 'bg-gray-700 text-gray-200 mr-4',
              message === streamingMessage ? '' : ''
            ]"
          >
            <div class="break-words" >{{ message.text }}</div>
            <!-- metadata (if present) -->
            <div v-if="message.metadata && this.devMode" class="text-xs text-gray-400 mt-2">
              <div v-for="(value, key) in message.metadata" :key="key">
                <strong>{{ key }}:</strong>
                <template v-if="Array.isArray(value)">
                  <div v-for="item in value" :key="item">
                    <a :href="item" target="_blank" class="text-teal-400 underline">{{ item }}</a>
                  </div>
                </template>
                <template v-else>
                  {{ value }}
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- input area -->
    <div class="bg-gray-900 pt-4">
      <form @submit.prevent="messageStreaming">
        <div class="flex">
          <input
            v-model="newMessage"
            type="text"
            :placeholder="streamingMessage ? ' ' : 'Enter your question...'"
            class="flex-grow p-4 rounded-xl bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
            :disabled="streamingMessage"
          />
          <button type="submit" class="ml-2 px-4 py-2 bg-teal-600 text-white rounded-xl hover:bg-teal-500">
            Send
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      newMessage: "",
      messages: [],
      streamingMessage: null,
      devMode: false,
      userRole: "normal",
    };
  },
  methods: {
    switchView() {
      this.devMode = !this.devMode;
    },
    // async messageImmediate() {
    //   if (this.newMessage.trim() === "") return;

    //   this.messages.push({
    //     text: this.newMessage,
    //     isUser: true,
    //   });

    //   const userMessage = this.newMessage;
    //   this.newMessage = "";

    //   try {
    //     const response = await fetch("http://localhost:8000/message-immediate", {
    //       method: "POST",
    //       headers: { "Content-Type": "application/json" },
    //       body: JSON.stringify({ text: userMessage }),
    //     });

    //     const data = await response.json();
    //     this.receiveMessage(data);
    //   } catch (error) {
    //     console.error("Error sending message:", error);
    //     this.receiveMessage({
    //       reply_msg: "Sorry, something went wrong. Please try again.",
    //     });
    //   }
    // },
    // receiveMessage(data) {
    //   this.messages.push({
    //     text: data.reply_msg,
    //     metadata: data.metadata,
    //     isUser: false,
    //   });

    //   this.$nextTick(() => {
    //     const chat = this.$el.querySelector("#chatArea");
    //     chat.scrollTop = chat.scrollHeight;
    //   });
    // },

    async messageStreaming() {
      if (this.newMessage.trim() === "") return;

      this.messages.push({
        text: this.newMessage,
        isUser: true,
      });

      const userMessage = this.newMessage;
      this.newMessage = "";

      try {
        const response = await fetch("http://localhost:8000/message-streaming",  {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: userMessage }),
        });
        if (!response.body) throw new Error("No response body");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = "";

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });

          const { text, metadata } = JSON.parse(chunk);

          accumulatedText += text;
          this.updateStreamingMessage(accumulatedText, metadata);
        }

        this.updateStreamingMessage(accumulatedText, null, true);
      } catch (error) {
        console.error("Error in streaming simulation:", error);
      }
    },
    updateStreamingMessage(text, metadata = null, isComplete = false) {
      if (this.streamingMessage) {
        this.streamingMessage.text = text;

        if (metadata) {
          this.streamingMessage.metadata = metadata;
        }
      } else {
        this.streamingMessage = { text, metadata, isUser: false };
        this.messages.push(this.streamingMessage);
      }

      if (isComplete) {
        this.streamingMessage = null;
      }

      this.$nextTick(() => {
        const chat = this.$el.querySelector("#chatArea");
        chat.scrollTop = chat.scrollHeight;
      });
    },
  },
};
</script>
