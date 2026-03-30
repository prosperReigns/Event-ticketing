import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvent } from "../services/eventService.js";

const EventDetails = () => {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const data = await getEvent(id);
        setEvent(data);
      } catch (err) {
        setError(getErrorMessage(err, "Unable to load event"));
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvent();
  }, [id]);

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Event Details</h1>
        <p className="text-sm text-slate-500">
          Review the event details and manage guest lists.
        </p>
      </div>

      <StatusAlert type="error" message={error} />

      {isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          Loading event details...
        </div>
      ) : event ? (
        <div className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">
              {event.name}
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              {event.location}
            </p>
            <p className="mt-2 text-sm text-slate-500">
              {event.start_datetime
                ? new Date(event.start_datetime).toLocaleString()
                : "Schedule pending"}
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              to={`/events/${id}/guests`}
              className="rounded-full bg-slate-900 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              View Guests
            </Link>
            <Link
              to={`/events/${id}/guests/view`}
              className="rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
            >
              Guest Check-in List
            </Link>
            <Link
              to={`/events/${id}/guests#add`}
              className="rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
            >
              Add Guests
            </Link>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500">
          Event not found.
        </div>
      )}
    </section>
  );
};

export default EventDetails;
