import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import BackButton from "../components/BackButton.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getGuest, updateGuest } from "../services/guestService.js";

const normalizePhone = (value) => {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }
  if (trimmed.startsWith("+")) {
    return `+${trimmed.slice(1).replace(/\\D/g, "")}`;
  }
  if (trimmed.startsWith("00")) {
    return `+${trimmed.slice(2).replace(/\\D/g, "")}`;
  }
  const digits = trimmed.replace(/\\D/g, "");
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
  return /^\\+\\d{7,15}$/.test(normalized);
};

const UpdateGuest = () => {
  const { id, guestId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    table_number: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    const fetchGuest = async () => {
      setIsLoading(true);
      try {
        const data = await getGuest(id, guestId);
        if (!isMounted) {
          return;
        }
        setFormData({
          name: data?.name || "",
          email: data?.email || "",
          phone: data?.phone || "",
          table_number: data?.table_number || "",
        });
      } catch (err) {
        if (isMounted) {
          setError(getErrorMessage(err, "Unable to load guest"));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchGuest();

    return () => {
      isMounted = false;
    };
  }, [guestId, id]);

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

    if (!formData.email.trim() && !formData.phone.trim()) {
      setError("Please provide an email or phone number.");
      return;
    }

    if (!isValidPhone(formData.phone.trim())) {
      setError("Phone must be E.164 format, e.g. +2348012345678.");
      return;
    }

    setIsSubmitting(true);
    try {
      await updateGuest(id, guestId, {
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: normalizePhone(formData.phone),
        table_number: formData.table_number.trim(),
      });
      navigate(`/events/${id}/guests/view`);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to update guest"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="space-y-6">
      <BackButton />
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Update Guest</h1>
        <p className="text-sm text-slate-500">
          Edit guest details for this event.
        </p>
      </div>

      <StatusAlert type="error" message={error} />

      {isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          Loading guest...
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
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

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-full bg-slate-900 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isSubmitting ? "Saving..." : "Save changes"}
            </button>
            <button
              type="button"
              onClick={() => navigate(`/events/${id}/guests/view`)}
              className="rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </section>
  );
};

export default UpdateGuest;
