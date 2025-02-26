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
      <template v-for="(query, index) in userQueries" :key="index">
        <!-- User Query -->
        <div class="mb-4">
          <div class="flex items-start justify-end">
            <div class="rounded-xl p-4 max-w-3xl break-words bg-teal-600 text-white ml-4">
              <div class="break-words">{{ query }}</div>
            </div>
          </div>
        </div>

        <!-- User View: Display Text Response -->
        <div v-if="!devMode" class="mb-4">
          <div class="flex items-start">
            <div class="rounded-xl p-4 max-w-3xl break-words bg-gray-700 text-gray-200 mr-4">
              <div class="break-words">
                {{ index === userQueries.length - 1 ? streamingText : responses[index] }}
              </div>
            </div>
          </div>
        </div>

        <!-- Dev Mode: Display Chunks -->
        <div v-if="devMode && retrievedChunks[index]" class="mb-4 p-4 rounded-lg bg-gray-700 text-gray-200">
          <h3 class="text-teal-400 font-bold mb-2">Retrieved Chunks:</h3>
          <ul>
            <li v-for="(chunk, cIndex) in retrievedChunks[index]" :key="cIndex" class="mb-2">
              <strong>Chunk ID:</strong> {{ chunk.chunk_id }}<br>
              <strong>Score:</strong> {{ chunk.score }}<br>
              <strong>Text:</strong> {{ chunk.text }}
            </li>
          </ul>
        </div>
      </template>
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
      userQueries: [],
      responses: [], // responses from LLM
      retrievedChunks: [], // list of lists of dicts (chunks)
      streamingText: "",
      devMode: false,
      userRole: "normal",
    };
  },
  methods: {
    switchView() {
      this.devMode = !this.devMode;
      this.scrollDown();
    },

    async messageStreaming() {
      if (this.newMessage.trim() === "") return;

      this.userQueries.push(this.newMessage);
      this.scrollDown();

      const userMessage = this.newMessage;
      this.newMessage = "";
      let accumulatedText = "";
      this.streamingText = "...";

      try {
        const response = await fetch("http://localhost:8000/query",  {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: userMessage, rights: this.userRole }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let chunksStored = false;

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });

          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.trim()) {
              const parsedLine = JSON.parse(line);

              // check the first message for chunks
              if (!chunksStored && parsedLine.metadata && parsedLine.metadata.chunks) {
                this.retrievedChunks.push(parsedLine.metadata.chunks);
                chunksStored = true;
                continue; // start streaming LLM response
              }

              // accumulate and display LLM streaming response
              if (parsedLine.text) {
                accumulatedText += parsedLine.text;
                this.streamingText = accumulatedText;
                this.scrollDown();
              }
            }
          }
        }
        this.responses.push(accumulatedText);
        this.scrollDown();
      } catch (error) {
        console.error("Error in streaming:", error);
      }
    },
    scrollDown() {
      this.$nextTick(() => {
        const chat = this.$el.querySelector("#chatArea");
        chat.scrollTop = chat.scrollHeight;
      });
    },
  },
};
</script>
