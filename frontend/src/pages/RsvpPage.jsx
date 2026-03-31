import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import BackButton from "../components/BackButton.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getRsvpDetails, submitRsvp } from "../services/rsvpService.js";

const RSVP_RESPONSES = {
  attending: "attending",
  declined: "declined",
};
const RSVP_SUCCESS_MESSAGES = {
  attending: "Your QR code has been sent to your email.",
  declined: "Thank you for your response.",
};

const RsvpPage = () => {
  const { token } = useParams();
  const [rsvpDetails, setRsvpDetails] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [existingStatus, setExistingStatus] = useState("");
  const [invalidToken, setInvalidToken] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchRsvp = async () => {
      setIsLoading(true);
      setError("");
      setInvalidToken(false);

      try {
        const data = await getRsvpDetails(token);
        if (!isMounted) {
          return;
        }

        setRsvpDetails(data);
        const guestName = data?.guest_name || data?.name || "";
        const guestEmail = data?.email || "";
        const guestPhone = data?.phone || "";
        setFormData((prev) => ({
          ...prev,
          name: guestName || prev.name,
          email: guestEmail || prev.email,
          phone: guestPhone || prev.phone,
        }));

        const status = data?.rsvp_status || data?.status || "";
        setExistingStatus(status);
      } catch (err) {
        if (!isMounted) {
          return;
        }

        if (err?.response?.status === 404) {
          setInvalidToken(true);
        } else {
          setError(getErrorMessage(err, "Unable to load invitation"));
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    if (token) {
      fetchRsvp();
    } else {
      setInvalidToken(true);
      setIsLoading(false);
    }

    return () => {
      isMounted = false;
    };
  }, [token]);

  const currentStatus = useMemo(() => {
    return (existingStatus || "").toLowerCase();
  }, [existingStatus]);

  const hasResponded = useMemo(() => {
    return Object.values(RSVP_RESPONSES).includes(currentStatus);
  }, [currentStatus]);

  const eventName =
    rsvpDetails?.event_name || rsvpDetails?.event?.name || "Event";
  const eventLocation =
    rsvpDetails?.location || rsvpDetails?.event?.location || "Location pending";
  const eventStart =
    rsvpDetails?.start_datetime ||
    rsvpDetails?.event?.start_datetime ||
    rsvpDetails?.event_start_datetime;

  const formattedDate = eventStart
    ? new Date(eventStart).toLocaleString()
    : "Schedule pending";

  const statusMessage = currentStatus
    ? `Current status: ${
        currentStatus === RSVP_RESPONSES.attending
          ? "Attending"
          : "Declined"
      }`
    : "";

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (response) => {
    setError("");
    setSuccessMessage("");

    if (isSubmitting) {
      return;
    }

    if (!formData.name.trim()) {
      setError("Name is required.");
      return;
    }

    if (response === RSVP_RESPONSES.attending && !formData.email.trim()) {
      setError("Email is required to accept the invitation.");
      return;
    }

    setIsSubmitting(true);
    try {
      await submitRsvp(token, {
        name: formData.name.trim(),
        email: formData.email.trim() || null,
        phone: formData.phone.trim() || null,
        response,
      });

      setExistingStatus(response);
      setSuccessMessage(RSVP_SUCCESS_MESSAGES[response]);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to submit RSVP"));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <section className="space-y-6">
        <BackButton />
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-slate-500">Loading invitation...</p>
        </div>
      </section>
    );
  }

  if (invalidToken) {
    return (
      <section className="space-y-6">
        <BackButton />
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
          Invalid invitation link.
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-8">
      <BackButton />
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">
          RSVP Invitation
        </h1>
        <p className="text-sm text-slate-500">
          Confirm your attendance and receive your QR check-in code.
        </p>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">{eventName}</h2>
        <p className="mt-2 text-sm text-slate-600">{eventLocation}</p>
        <p className="mt-2 text-sm text-slate-500">{formattedDate}</p>
      </div>

      <StatusAlert type="success" message={successMessage} />
      <StatusAlert type="error" message={error} />

      {hasResponded ? (
        <div className="space-y-2 rounded-3xl border border-emerald-200 bg-emerald-50 p-6 text-sm text-emerald-700">
          <p>{statusMessage || "Thanks for your RSVP!"}</p>
          <p>
            {RSVP_SUCCESS_MESSAGES[currentStatus]}
          </p>
        </div>
      ) : (
        <form className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Confirm your details
            </h2>
            <p className="text-sm text-slate-500">
              Please verify your information to respond.
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
              placeholder="Guest name"
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
              placeholder="you@example.com"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Phone (optional)
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="+1 (555) 123-4567"
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => handleSubmit(RSVP_RESPONSES.attending)}
              disabled={isSubmitting}
              className="w-full rounded-full bg-emerald-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-300"
            >
              {isSubmitting ? "Submitting..." : "Accept Invitation"}
            </button>
            <button
              type="button"
              onClick={() => handleSubmit(RSVP_RESPONSES.declined)}
              disabled={isSubmitting}
              className="w-full rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900 disabled:cursor-not-allowed disabled:text-slate-400"
            >
              {isSubmitting ? "Submitting..." : "Decline"}
            </button>
          </div>
        </form>
      )}
    </section>
  );
};

export default RsvpPage;
