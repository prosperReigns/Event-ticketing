import api from "../api/axios.js";

export const getGuests = async (eventId) => {
  const response = await api.get(`events/${eventId}/guests/`);
  return response.data;
};

export const createGuest = async (eventId, payload) => {
  const response = await api.post(`events/${eventId}/guests/`, payload);
  return response.data;
};
