import api from "../api/axios.js";

export const getEvents = async () => {
  const response = await api.get("events/");
  return response.data;
};

export const getEvent = async (eventId) => {
  const response = await api.get(`events/${eventId}/`);
  return response.data;
};

export const getPublicEvent = async (slug) => {
  const response = await api.get(`events/slug/${slug}/`);
  return response.data;
};

export const createEvent = async (payload) => {
  const response = await api.post("events/", payload);
  return response.data;
};

export const updateEvent = async (eventId, payload) => {
  const response = await api.patch(`events/${eventId}/`, payload);
  return response.data;
};

export const deleteEvent = async (eventId) => {
  const response = await api.delete(`events/${eventId}/`);
  return response.data;
};

export const registerForEvent = async (eventId, payload) => {
  const response = await api.post(`events/${eventId}/register/`, payload);
  return response.data;
};

export const registerForEventBySlug = async (slug, payload) => {
  const response = await api.post(`events/slug/${slug}/guests/`, payload);
  return response.data;
};
