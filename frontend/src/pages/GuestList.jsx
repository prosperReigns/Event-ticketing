import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import BackButton from "../components/BackButton.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvent } from "../services/eventService.js";
import { createGuest } from "../services/guestService.js";

import api from "../api/axios.js";

const GuestList = () => {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    table_number: "",
  });
  const [bulkInput, setBulkInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBulkSubmitting, setIsBulkSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadEvent = useCallback(async () => {
    try {
      const eventData = await getEvent(id);
      setEvent(eventData);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to load event"));
    }
  }, [id]);

  useEffect(() => {
    loadEvent();
  }, [loadEvent]);

  const bulkGuests = useMemo(() => {
    return bulkInput
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split(",").map((value) => value.trim());
        const name = parts[0] || "";
        const email = parts[1] || "";
        let phone = "";
        let table_number = "";
        if (parts.length >= 4) {
          phone = parts[2] || "";
          table_number = parts[3] || "";
        } else {
          table_number = parts[2] || "";
        }
        return { name, email, phone, table_number };
      });
  }, [bulkInput]);

  const normalizePhone = (value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      return "";
    }
    if (trimmed.startsWith("+")) {
      return `+${trimmed.slice(1).replace(/\D/g, "")}`;
    }
    if (trimmed.startsWith("00")) {
      return `+${trimmed.slice(2).replace(/\D/g, "")}`;
    }
    const digits = trimmed.replace(/\D/g, "");
    if (!digits) {
      return "";
    }
    if (digits.startsWith("0")) {
      return digits;
    }
    if (digits.length >= 10 && digits.length <= 15) {
      return `+${digits}`;
    }
    return digits;
  };

  const isValidPhone = (value) => {
    if (!value) {
      return true;
    }
    const normalized = normalizePhone(value);
    return /^\+\d{7,15}$/.test(normalized);
  };

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

    if (!formData.email.trim() && !formData.phone.trim()) {
      setError("Please provide an email or phone number.");
      return;
    }

    const normalizedPhone = normalizePhone(formData.phone);
    if (!isValidPhone(formData.phone)) {
      setError("Phone must be E.164 format, e.g. +2348012345678.");
      return;
    }

    setIsSubmitting(true);
    try {
      await createGuest(id, {
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: normalizedPhone,
        table_number: formData.table_number.trim(),
      });
      setFormData({ name: "", email: "", phone: "", table_number: "" });
      setSuccessMessage("Guest added successfully.");
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
      (guest) => !guest.name || (!guest.email && !guest.phone),
    );

    if (invalidRow) {
      setError("Each row must include a name and either email or phone.");
      return;
    }

    const invalidPhone = bulkGuests.find(
      (guest) => guest.phone && !isValidPhone(guest.phone),
    );

    if (invalidPhone) {
      setError("Each phone number must be E.164 format, e.g. +2348012345678.");
      return;
    }

    setIsBulkSubmitting(true);
    try {
      const normalizedGuests = bulkGuests.map((guest) => ({
        ...guest,
        phone: normalizePhone(guest.phone || ""),
      }));
      await api.post(`events/${id}/guests/`, {
        guests: normalizedGuests,
      });
      setBulkInput("");
      setSuccessMessage("Bulk guests uploaded successfully.");
    } catch (err) {
      setError(getErrorMessage(err, "Bulk upload failed"));
    } finally {
      setIsBulkSubmitting(false);
    }
  };

  return (
    <section className="space-y-8">
      <BackButton />
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Guest List</h1>
        <p className="text-sm text-slate-500">
          {event?.name || "Event"} guests and check-in status.
        </p>
      </div>

      <StatusAlert type="success" message={successMessage} />
      <StatusAlert type="error" message={error} />

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
              Send them a QR code by email, or an RSVP link by SMS.
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
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="ada@example.com"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Phone number
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              onBlur={(event) =>
                setFormData((prev) => ({
                  ...prev,
                  phone: normalizePhone(event.target.value),
                }))
              }
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="+2348012345678"
            />
            <p className="mt-1 text-xs text-slate-500">
              Use E.164 format (country code + number).
            </p>
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
              Paste rows in this format: name,email,phone,table_number (use
              E.164 like +2348012345678; leave email blank like:
              Ada,,+2348012345678,12)
            </p>
          </div>

          <textarea
            value={bulkInput}
            onChange={(event) => setBulkInput(event.target.value)}
            rows={6}
            className="w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder={
              "Ada Lovelace,ada@example.com,+2348012345678,12\nAda,,+2348012345678,12"
            }
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
