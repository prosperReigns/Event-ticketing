import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import BackButton from "../components/BackButton.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { deleteEvent, getEvents } from "../services/eventService.js";

const Dashboard = () => {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingEventId, setDeletingEventId] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

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

  const handleDelete = async (eventId, eventName) => {
    if (deletingEventId) {
      return;
    }
    const confirmed = window.confirm(
      `Delete ${eventName || "this event"}? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }
    setDeletingEventId(eventId);
    setError("");
    try {
      await deleteEvent(eventId);
      setEvents((prev) => prev.filter((event) => event.id !== eventId));
    } catch (err) {
      setError(getErrorMessage(err, "Unable to delete event"));
    } finally {
      setDeletingEventId("");
    }
  };

  return (
    <section className="space-y-6">
      <BackButton />
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
            <div
              key={event.id}
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/events/${event.id}`)}
              onKeyDown={(eventKey) => {
                if (eventKey.key === "Enter" || eventKey.key === " ") {
                  eventKey.preventDefault();
                  navigate(`/events/${event.id}`);
                }
              }}
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
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  to={`/events/${event.id}/edit`}
                  onClick={(eventClick) => eventClick.stopPropagation()}
                  className="rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
                >
                  Update
                </Link>
                <button
                  type="button"
                  onClick={(eventClick) => {
                    eventClick.stopPropagation();
                    handleDelete(event.id, event.name);
                  }}
                  disabled={deletingEventId === event.id}
                  className="rounded-full border border-rose-200 px-4 py-2 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {deletingEventId === event.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default Dashboard;
