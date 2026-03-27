import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvents } from "../services/eventService.js";

const Dashboard = () => {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await getEvents();
        setEvents(Array.isArray(data) ? data : data?.results || []);
      } catch (err) {
        setError(getErrorMessage(err, "Unable to load events"));
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvents();
  }, []);

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Events</h1>
          <p className="text-sm text-slate-500">
            Manage upcoming events and guest experiences.
          </p>
        </div>
        <Link
          to="/events/create"
          className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
        >
          Create Event
        </Link>
      </div>

      <StatusAlert type="error" message={error} />

      {isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          Loading events...
        </div>
      ) : events.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500">
          No events found. Create your first event to get started.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {events.map((event) => (
            <Link
              key={event.id}
              to={`/events/${event.id}`}
              className="group rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">
                    {event.name}
                  </h2>
                  <p className="text-sm text-slate-500">{event.location}</p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  View
                </span>
              </div>
              <p className="mt-4 text-sm text-slate-600">
                {event.start_datetime
                  ? new Date(event.start_datetime).toLocaleString()
                  : "Schedule pending"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
};

export default Dashboard;
