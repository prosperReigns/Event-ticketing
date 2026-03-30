import api from "../api/axios.js";

export const getRsvpDetails = async (token) => {
  const response = await api.get(`rsvp/${token}/`);
  return response.data;
};

export const submitRsvp = async (token, payload) => {
  const response = await api.post(`rsvp/${token}/`, payload);
  return response.data;
};
