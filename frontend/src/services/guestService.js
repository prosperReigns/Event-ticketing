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
