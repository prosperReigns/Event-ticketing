import api from "../api/axios.js";

export const checkInGuest = async (token) => {
  const response = await api.get(`checkin/${token}/`);
  return response.data;
};
