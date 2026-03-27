import api from "../api/axios.js";

export const getEvents = async () => {
  const response = await api.get("events/");
  return response.data;
};

export const getEvent = async (eventId) => {
  const response = await api.get(`events/${eventId}/`);
  return response.data;
};

export const createEvent = async (payload) => {
  const response = await api.post("events/", payload);
  return response.data;
};
