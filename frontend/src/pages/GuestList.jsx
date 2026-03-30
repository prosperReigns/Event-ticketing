import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import GuestTable from "../components/GuestTable.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvent } from "../services/eventService.js";
import { createGuest, getGuests } from "../services/guestService.js";

import api from "../api/axios.js";

const GuestList = () => {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [guests, setGuests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    table_number: "",
  });
  const [bulkInput, setBulkInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBulkSubmitting, setIsBulkSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadGuests = useCallback(async () => {
    try {
      const [eventData, guestData] = await Promise.all([
        getEvent(id),
        getGuests(id),
      ]);

      setEvent(eventData);
      setGuests(Array.isArray(guestData) ? guestData : guestData?.results || []);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to load guests"));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadGuests();
  }, [loadGuests]);

  const bulkGuests = useMemo(() => {
    return bulkInput
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [name, email, table_number] = line
          .split(",")
          .map((value) => value.trim());
        return { name, email, table_number };
      });
  }, [bulkInput]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");

    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      await createGuest(id, formData);
      setFormData({ name: "", email: "", table_number: "" });
      setSuccessMessage("Guest added successfully.");
      await loadGuests();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to add guest"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBulkSubmit = async () => {
    setError("");
    setSuccessMessage("");

    if (isBulkSubmitting || bulkGuests.length === 0) {
      return;
    }

    const invalidRow = bulkGuests.find(
      (guest) => !guest.name || !guest.email,
    );

    if (invalidRow) {
      setError("Each row must include name and email.");
      return;
    }

    setIsBulkSubmitting(true);
    try {
      await api.post(`events/${id}/guests/`, {
        guests: bulkGuests,
      });
      setBulkInput("");
      setSuccessMessage("Bulk guests uploaded successfully.");
      await loadGuests();
    } catch (err) {
      setError(getErrorMessage(err, "Bulk upload failed"));
    } finally {
      setIsBulkSubmitting(false);
    }
  };

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Guest List</h1>
        <p className="text-sm text-slate-500">
          {event?.name || "Event"} guests and check-in status.
        </p>
      </div>

      <StatusAlert type="success" message={successMessage} />
      <StatusAlert type="error" message={error} />

      {isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          Loading guests...
        </div>
      ) : (
        <GuestTable guests={guests} />
      )}

      <div id="add" className="grid gap-6 lg:grid-cols-2">
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Add a guest
            </h2>
            <p className="text-sm text-slate-500">
              Send them a QR code from the backend after saving.
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
              placeholder="Ada Lovelace"
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
              placeholder="ada@example.com"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Table number
            <input
              type="text"
              name="table_number"
              value={formData.table_number}
              onChange={handleChange}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="12"
            />
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-slate-900 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Adding..." : "Add guest"}
          </button>
        </form>

        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Bulk upload (CSV)
            </h2>
            <p className="text-sm text-slate-500">
              Paste rows in this format: name,email,table_number
            </p>
          </div>

          <textarea
            value={bulkInput}
            onChange={(event) => setBulkInput(event.target.value)}
            rows={6}
            className="w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder="Ada Lovelace,ada@example.com,12"
          />

          <button
            type="button"
            onClick={handleBulkSubmit}
            disabled={isBulkSubmitting || bulkGuests.length === 0}
            className="w-full rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900 disabled:cursor-not-allowed disabled:text-slate-400"
          >
            {isBulkSubmitting ? "Uploading..." : "Upload guests"}
          </button>
        </div>
      </div>
    </section>
  );
};

export default GuestList;
