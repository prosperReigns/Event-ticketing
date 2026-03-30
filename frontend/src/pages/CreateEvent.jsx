import { useState } from "react";
import { useNavigate } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { createEvent } from "../services/eventService.js";

const CreateEvent = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    start_datetime: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      await createEvent(formData);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err, "Unable to create event"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Create Event</h1>
        <p className="text-sm text-slate-500">
          Add a new event and begin inviting guests.
        </p>
      </div>

      <StatusAlert type="error" message={error} />

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <label className="block text-sm font-medium text-slate-700">
          Event name
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder="Gala Night 2026"
          />
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Location
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            required
            className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder="Grand Hall, Lagos"
          />
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Start date & time
          <input
            type="datetime-local"
            name="start_datetime"
            value={formData.start_datetime}
            onChange={handleChange}
            required
            className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder="dd/mm/yyy hh:mm"
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-full bg-slate-900 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Creating..." : "Create event"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
};

export default CreateEvent;
