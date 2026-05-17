import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000",
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
