import api from "../api/axios.js";

export const getGuests = async (eventId) => {
  const response = await api.get(`events/${eventId}/guests/`);
  return response.data;
};

export const createGuest = async (eventId, payload) => {
  const response = await api.post(`events/${eventId}/guests/`, {
    guests: [payload],
  });

  if (Array.isArray(response.data?.created)) {
    return response.data.created[0] || null;
  }

  return response.data;
};

export const deleteGuest = async (eventId, guestId) => {
  const response = await api.delete(`events/${eventId}/guests/${guestId}/`);
  return response.data;
};

export const getGuest = async (eventId, guestId) => {
  const response = await api.get(`events/${eventId}/guests/${guestId}/`);
  return response.data;
};

export const updateGuest = async (eventId, guestId, payload) => {
  const response = await api.patch(`events/${eventId}/guests/${guestId}/`, payload);
  return response.data;
};
