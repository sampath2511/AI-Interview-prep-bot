import axios from "axios";

const apiClient = axios.create({
  baseURL: "https://ai-interview-prep-bot-1.onrender.com",
  headers: {
    "Content-Type": "application/json",
  },
});

export const prepareInterview = async (topic, level) => {
  try {
    const response = await apiClient.post("/prepare", { topic, level });
    return response.data;
  } catch (error) {
    console.error("API error:", error);
    throw error;
  }
};
