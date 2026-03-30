import api from "../api/axios.js";

export const checkInGuest = async (token) => {
  let response;
  try {
    response = await api.post(`checkin/${token}/`);
  } catch (error) {
    // Fallback for environments still expecting GET check-in.
    if (error?.response?.status === 405) {
      response = await api.get(`checkin/${token}/`);
    } else {
      throw error;
    }
  }
  const data = response.data;

  return {
    name: data.guest_name,
    table_number: data.table_number,
    event_name: data.event_name,
    check_in_time: data.check_in_time,
    message: data.message,
  };
};
