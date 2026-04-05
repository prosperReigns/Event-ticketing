import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvent, registerForEvent } from "../services/eventService.js";

const RegisterPage = () => {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [formData, setFormData] = useState({ name: "", email: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [notPublic, setNotPublic] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchEvent = async () => {
      setIsLoading(true);
      setError("");
      setNotFound(false);
      setNotPublic(false);

      try {
        const data = await getEvent(eventId);
        if (!isMounted) return;

        if (data.registration_type !== "public") {
          setNotPublic(true);
        } else {
          setEvent(data);
        }
      } catch (err) {
        if (!isMounted) return;
        if (err?.response?.status === 404) {
          setNotFound(true);
        } else {
          setError(getErrorMessage(err, "Unable to load event details"));
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    if (eventId) {
      fetchEvent();
    } else {
      setNotFound(true);
      setIsLoading(false);
    }

    return () => {
      isMounted = false;
    };
  }, [eventId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!formData.name.trim()) {
      setError("Name is required.");
      return;
    }

    if (!formData.email.trim()) {
      setError("Email is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      await registerForEvent(eventId, {
        name: formData.name.trim(),
        email: formData.email.trim(),
      });
      setSuccessMessage(
        "Registration successful! Your QR code has been sent to your email."
      );
      setFormData({ name: "", email: "" });
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <section className="space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-slate-500">Loading event details...</p>
        </div>
      </section>
    );
  }

  if (notFound) {
    return (
      <section className="space-y-6">
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          Event not found.
        </div>
      </section>
    );
  }

  if (notPublic) {
    return (
      <section className="space-y-6">
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          This event is not open for public registration.
        </div>
      </section>
    );
  }

  const formattedDate = event?.start_datetime
    ? new Date(event.start_datetime).toLocaleString()
    : "Schedule pending";

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">
          Event Registration
        </h1>
        <p className="text-sm text-slate-500">
          Register for this event and receive your QR check-in code by email.
        </p>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        {event?.logo && (
          <img
            src={event.logo}
            alt={event.name}
            className="mb-4 h-16 w-16 rounded-2xl object-cover"
          />
        )}
        <h2 className="text-xl font-semibold text-slate-900">{event?.name}</h2>
        {event?.description && (
          <p className="mt-2 text-sm text-slate-600">{event.description}</p>
        )}
        <p className="mt-2 text-sm text-slate-500">{formattedDate}</p>
        {event?.location && (
          <p className="mt-1 text-sm text-slate-500">{event.location}</p>
        )}
      </div>

      <StatusAlert type="success" message={successMessage} />
      <StatusAlert type="error" message={error} />

      {!successMessage && (
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Your details
            </h2>
            <p className="text-sm text-slate-500">
              Enter your information to register for this event.
            </p>
          </div>

          <label className="block text-sm font-medium text-slate-700">
            Name
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="Your full name"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="you@example.com"
            />
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-slate-900 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Registering..." : "Register"}
          </button>
        </form>
      )}
    </section>
  );
};

export default RegisterPage;
