import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getPublicEvent, registerForEventBySlug } from "../services/eventService.js";

const DEFAULT_FIELDS = [
  { name: "full_name", type: "text", required: true, label: "Full Name" },
  { name: "email", type: "email", required: true, label: "Email" },
];

const inputClass =
  "mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none";
const errorClass = "mt-1 text-xs text-red-600";

const initFormData = (fields) => {
  const data = {};
  fields.forEach((f) => {
    data[f.name] = f.type === "checkbox" ? [] : "";
  });
  return data;
};

const DynamicField = ({ field, value, onChange, fieldError }) => {
  const { name, type, label, required, options = [] } = field;
  const displayLabel = label || name;

  const handleCheckboxChange = (e) => {
    const { value: optVal, checked } = e.target;
    const current = Array.isArray(value) ? value : [];
    const updated = checked
      ? [...current, optVal]
      : current.filter((v) => v !== optVal);
    onChange(name, updated);
  };

  if (type === "textarea") {
    return (
      <div>
        <label className="block text-sm font-medium text-slate-700">
          {displayLabel}
          {required && <span className="ml-1 text-red-500">*</span>}
          <textarea
            name={name}
            value={value}
            onChange={(e) => onChange(name, e.target.value)}
            required={required}
            rows={3}
            className={`${inputClass} resize-y`}
            placeholder={`Enter ${displayLabel.toLowerCase()}`}
          />
        </label>
        {fieldError && <p className={errorClass}>{fieldError}</p>}
      </div>
    );
  }

  if (type === "select") {
    return (
      <div>
        <label className="block text-sm font-medium text-slate-700">
          {displayLabel}
          {required && <span className="ml-1 text-red-500">*</span>}
          <select
            name={name}
            value={value}
            onChange={(e) => onChange(name, e.target.value)}
            required={required}
            className={inputClass}
          >
            <option value="">Select an option</option>
            {options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </label>
        {fieldError && <p className={errorClass}>{fieldError}</p>}
      </div>
    );
  }

  if (type === "radio") {
    return (
      <div>
        <p className="text-sm font-medium text-slate-700">
          {displayLabel}
          {required && <span className="ml-1 text-red-500">*</span>}
        </p>
        <div className="mt-2 flex flex-wrap gap-4">
          {options.map((opt) => (
            <label
              key={opt}
              className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
            >
              <input
                type="radio"
                name={name}
                value={opt}
                checked={value === opt}
                onChange={(e) => onChange(name, e.target.value)}
                required={required && !value}
                className="accent-slate-900"
              />
              {opt}
            </label>
          ))}
        </div>
        {fieldError && <p className={errorClass}>{fieldError}</p>}
      </div>
    );
  }

  if (type === "checkbox") {
    const checked = Array.isArray(value) ? value : [];
    return (
      <div>
        <p className="text-sm font-medium text-slate-700">
          {displayLabel}
          {required && <span className="ml-1 text-red-500">*</span>}
        </p>
        <div className="mt-2 flex flex-wrap gap-4">
          {options.map((opt) => (
            <label
              key={opt}
              className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
            >
              <input
                type="checkbox"
                value={opt}
                checked={checked.includes(opt)}
                onChange={handleCheckboxChange}
                className="accent-slate-900"
              />
              {opt}
            </label>
          ))}
        </div>
        {fieldError && <p className={errorClass}>{fieldError}</p>}
      </div>
    );
  }

  const inputType =
    type === "email" ? "email" : type === "number" ? "number" : "text";

  return (
    <div>
      <label className="block text-sm font-medium text-slate-700">
        {displayLabel}
        {required && <span className="ml-1 text-red-500">*</span>}
        <input
          type={inputType}
          name={name}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          required={required}
          className={inputClass}
          placeholder={`Enter ${displayLabel.toLowerCase()}`}
        />
      </label>
      {fieldError && <p className={errorClass}>{fieldError}</p>}
    </div>
  );
};

const RegisterPage = () => {
  const { slug } = useParams();
  const [event, setEvent] = useState(null);
  const [fields, setFields] = useState(DEFAULT_FIELDS);
  const [formData, setFormData] = useState(initFormData(DEFAULT_FIELDS));
  const [fieldErrors, setFieldErrors] = useState({});
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
        const data = await getPublicEvent(slug);
        if (!isMounted) return;
        setEvent(data);
        const effectiveFields =
          data.registration_fields && data.registration_fields.length > 0
            ? data.registration_fields
            : DEFAULT_FIELDS;
        setFields(effectiveFields);
        setFormData(initFormData(effectiveFields));
      } catch (err) {
        if (!isMounted) return;
        if (err?.response?.status === 404) {
          setNotFound(true);
        } else if (err?.response?.status === 403) {
          setNotPublic(true);
        } else {
          setError(getErrorMessage(err, "Unable to load event details"));
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    if (slug) {
      fetchEvent();
    } else {
      setNotFound(true);
      setIsLoading(false);
    }

    return () => {
      isMounted = false;
    };
  }, [slug]);

  const handleFieldChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setFieldErrors({});
    setSuccessMessage("");

    setIsSubmitting(true);
    try {
      await registerForEventBySlug(slug, formData);
      setSuccessMessage(
        "Registration successful! Your QR code has been sent to your email."
      );
      setFormData(initFormData(fields));
    } catch (err) {
      if (err?.response?.status === 400) {
        const data = err.response.data;
        if (data && typeof data === "object" && !data.detail) {
          setFieldErrors(data);
        } else {
          setError(
            data?.detail ||
              getErrorMessage(err, "Registration failed. Please try again.")
          );
        }
      } else {
        setError(getErrorMessage(err, "Registration failed. Please try again."));
      }
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

          {fields.map((field) => (
            <DynamicField
              key={field.name}
              field={field}
              value={formData[field.name] ?? (field.type === "checkbox" ? [] : "")}
              onChange={handleFieldChange}
              fieldError={fieldErrors[field.name] || ""}
            />
          ))}

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
