<template>
  <div class="flex flex-col h-screen px-20 py-10 bg-gray-900 text-gray-200">
    <div class="flex justify-between items-center">
      <!-- modes -->
      <div class="flex pl-3">
        <!-- user view button -->
        <button
          class="px-4 py-2 text-white rounded-t-xl hover:bg-teal-500"
          :class="[devMode ? 'bg-teal-600' : 'bg-teal-500']"
          @click="switchView"
        >
          User View
        </button>
        <!-- dev mode button -->
        <button
          class="px-4 py-2 text-white rounded-t-xl hover:bg-teal-500"
          :class="[!devMode ? 'bg-teal-600' : 'bg-teal-500']"
          @click="switchView"
        >
          Dev Mode
        </button>
      </div>

      <!-- button to open modal -->
      <div v-if="userRole === 'superior'">
        <button
            class="px-4 py-2 bg-teal-600 text-white rounded-t-xl hover:bg-teal-500"
            @click="openModal"
        >
            Google Drive Integration
        </button>
      </div>

      <!-- roles -->
      <div class="flex items-center space-x-4 pr-4">
        <label class="text-sm text-gray-300">Role:</label>
        <!-- user role -->
        <label
          class="flex items-center space-x-2 cursor-pointer"
          :class="{'text-teal-400': userRole === 'user', 'text-gray-300': userRole !== 'user'}"
        >
          <input
            type="radio"
            value="user"
            v-model="userRole"
            class="hidden"
          />
          <div
            class="w-4 h-4 border-2 rounded-full"
            :class="userRole === 'user' ? 'bg-teal-500 border-teal-500' : 'border-gray-400'"
          ></div>
          <span>User</span>
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
        <!-- user query -->
        <div class="mb-4">
          <div class="flex items-start justify-end">
            <div class="rounded-xl p-4 max-w-3xl break-words bg-teal-600 text-white ml-4">
              <div class="break-words">{{ query }}</div>
            </div>
          </div>
        </div>

        <!-- user view: display text response -->
        <div v-if="!devMode" class="mb-4">
          <div class="flex items-start">
            <div class="rounded-xl p-4 max-w-3xl break-words bg-gray-700 text-gray-200 mr-4">
              <div class="break-words" v-html="renderMarkdown(index === userQueries.length - 1 ? streamingText : responses[index])"></div>
            </div>
          </div>
        </div>

        <!-- dev mode: display chunks -->
        <div v-if="devMode && retrievedChunks[index]" class="mb-4 p-4 rounded-lg bg-gray-700 text-gray-200">
          <h3 class="text-teal-400 font-bold mb-2">Retrieved Chunks:</h3>
          <ul>
            <li v-for="(chunk, cIndex) in retrievedChunks[index]" :key="cIndex" class="mb-4">
              <span class="font-bold">File:</span> {{ chunk.filename }}<br>
              <span class="font-bold">Score:</span> {{ chunk.score.toFixed(3) }} ({{ chunk.explain_score }})<br>
              <span class="font-bold">Reranked Score:</span> {{ chunk.reranked_score.toFixed(3) }}<br>
              <span class="font-bold">Title:</span> {{ chunk.title }}<br>
              <span class="font-bold">Text:</span> {{ chunk.text }}
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
            :placeholder="isStreaming ? ' ' : 'Enter your question...'"
            class="flex-grow p-4 rounded-xl bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
            :disabled="isStreaming"
          />
          <button type="submit" class="ml-2 px-4 py-2 bg-teal-600 text-white rounded-xl hover:bg-teal-500">
            Send
          </button>
        </div>
      </form>
    </div>

    <!-- modal overlay -->
    <div
      v-if="showModal"
      class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50"
      @click="closeModal"
    >
      <!-- modal content -->
      <div 
        class="relative bg-gray-800 w-full max-w-xl p-6 rounded-xl"
        @click.stop
      >
        <!-- close button -->
        <button
          class="absolute top-2 right-2 text-white hover:text-gray-300"
          @click="closeModal"
        >
          X
        </button>

        <h2 class="text-xl font-bold mb-4 text-white">Google Drive Integration</h2>

        <!-- url input -->
        <label class="block text-gray-300 mb-2" for="driveURL">
          Google Drive Folder URL:
        </label>
        <input
          v-model="driveURL"
          type="text"
          id="driveURL"
          placeholder="e.g. https://drive.google.com/drive/folders/..."
          class="w-full mb-4 p-2 rounded-md bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
          :disabled="isIngesting"
        />
        <!-- show stored url -->
        <p v-if="storedDriveURL" class="text-sm text-gray-200 mb-4 text-opacity-50">
            Stored URL: {{ storedDriveURL }}
        </p>

        <div class="flex justify-between items-center mt-4">
          <!-- delete db -->
          <button
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500"
            @click="deleteSchema"
            :disabled="isIngesting"
          >
            Delete DB
          </button>
          
          <div>
            <!-- ingest -->
            <button
              class="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-500"
              @click="bulkIngest"
              :disabled="isIngesting"
            >
              Ingest
            </button>
          </div>
        </div>

        <!-- loading spinner and messages -->
        <div v-if="isIngesting" class="mt-4 flex items-center">
          <svg
            class="animate-spin h-5 w-5 text-white mr-2"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            ></path>
          </svg>
          <span class="text-gray-200">Ingesting, please wait...</span>
        </div>

        <div v-if="successMessage" class="mt-4 text-green-400">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="mt-4 text-red-400">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked';

export default {
  data() {
    return {
      newMessage: "",
      userQueries: [],
      responses: [], // responses from LLM
      retrievedChunks: [], // list of lists of dicts (chunks)
      streamingText: "",
      devMode: false,
      userRole: "user",
      isStreaming: false,

      showModal: false,
      driveURL: "",
      storedDriveURL: "",
      isIngesting: false,
      successMessage: "",
      errorMessage: "",
    };
  },
  async mounted() {
    await this.fetchDriveURL();
  },

  methods: {

    renderMarkdown(text) {
      if (!text) return "";
      
      const citationRegex = /\[(.*?)\]/g;
      const formattedText = text.replace(citationRegex, '<span class="italic text-sm text-gray-300">[$1]</span>');

      return marked.parse(formattedText);
    },

    switchView() {
      this.devMode = !this.devMode;
      this.scrollDown();
    },
    async openModal() {
      await this.fetchDriveURL();
      this.showModal = true;
      this.successMessage = "";
      this.errorMessage = "";
    },
    closeModal() {
      if (this.isIngesting) return;
      this.showModal = false;
    },

    async fetchDriveURL() {
      try {
        const response = await fetch("http://localhost:8000/driveurl", {
          method: "GET",
        });

        if (!response.ok) {
            console.error("Failed to fetch drive URL");
            return;
          }

          const data = await response.json();
          if (data.url) {
              this.storedDriveURL = data.url;
          }
      } catch (error) {
        console.error("Error fetching drive URL:", error);
      }
    },

    async bulkIngest() {
      const url = this.driveURL.trim() || this.storedDriveURL;
      if (!url) {
        this.errorMessage = "Please provide a valid Google Drive URL.";
        return;
      }

      try {
        this.isIngesting = true;
        this.successMessage = "";
        this.errorMessage = "";

        const response = await fetch("http://localhost:8000/ingest_folder", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ driveURL: url }),
        });

        if (!response.ok) {
          const errText = await response.text();
          console.error("Ingestion failed:", errText);
          this.errorMessage = "Ingestion failed:", errText;
          return;
        }

        this.successMessage = "Ingestion completed successfully!";
        await this.fetchDriveURL();
      } catch (error) {
        console.error("Error ingesting folder:", error);
        this.errorMessage = "Error occurred during ingestion.";
      } finally {
        this.isIngesting = false;
      }
    },

    async deleteSchema() {
      alert("Are you sure you want to delete the database?");
      try {
        this.isIngesting = true;
        this.successMessage = "";
        this.errorMessage = "";
        const response = await fetch("http://localhost:8000/delete_schema", {
            method: "POST",
        });

        if (!response.ok) {
          const errText = await response.text();
          console.error("Schema deleting failed:", errText);
          this.errorMessage = "Schema deleting failed:", errText;
          return;
        }

      } catch (error) {
        console.error("Error deleting schema:", error);
        this.errorMessage = "Error deleting database.";
      } finally {
        this.isIngesting = false;
      }
    },

    async messageStreaming() {
      if (this.newMessage.trim() === "") return;
      this.isStreaming = true;

      this.userQueries.push(this.newMessage);
      this.scrollDown();

      const userMessage = this.newMessage;
      this.newMessage = "";
      let accumulatedText = "";
      this.streamingText = "...";
      
      // format history as Q&A
      const formattedHistory = this.userQueries
          .slice(0, this.responses.length)
          .map((q, i) => `Q: ${q}\nA: ${this.responses[i]}`);

      try {
          const response = await fetch("http://localhost:8000/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
              query: userMessage,
              rights: this.userRole,
              history: formattedHistory
          }),
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
      this.isStreaming = false;
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
