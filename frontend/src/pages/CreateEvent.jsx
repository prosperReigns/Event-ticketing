import { useState } from "react";
import { useNavigate } from "react-router-dom";

import BackButton from "../components/BackButton.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { createEvent } from "../services/eventService.js";

const CreateEvent = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    start_datetime: "",
    qr_color: "#0f172a",
    qr_caption: "Scan to check in",
    registration_type: "private",
  });
  const [fieldErrors, setFieldErrors] = useState({
    qr_color: "",
    qr_caption: "",
  });
  const [logoFile, setLogoFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const isValidHexColor = (value) =>
    /^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$/.test(value.trim());

  const validateField = (name, value) => {
    if (name === "qr_color") {
      return isValidHexColor(value) ? "" : "Use a valid hex color like #0f172a.";
    }
    if (name === "qr_caption") {
      return value.length > 120
        ? "Caption must be 120 characters or fewer."
        : "";
    }
    return "";
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (name === "qr_color" || name === "qr_caption") {
      setFieldErrors((prev) => ({
        ...prev,
        [name]: validateField(name, value),
      }));
    }
  };

  const handleLogoChange = (event) => {
    const file = event.target.files && event.target.files[0];
    setLogoFile(file || null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      const qrColorError = validateField("qr_color", formData.qr_color);
      const qrCaptionError = validateField("qr_caption", formData.qr_caption);
      if (qrColorError || qrCaptionError) {
        setFieldErrors((prev) => ({
          ...prev,
          qr_color: qrColorError,
          qr_caption: qrCaptionError,
        }));
        return;
      }

      const dateValue = new Date(formData.start_datetime);
      const startDateTime = Number.isNaN(dateValue.getTime())
        ? formData.start_datetime
        : dateValue.toISOString();

      const payload = new FormData();
      payload.append("name", formData.name.trim());
      payload.append("location", formData.location.trim());
      payload.append("start_datetime", startDateTime);
      payload.append("qr_color", formData.qr_color.trim());
      payload.append("qr_caption", formData.qr_caption.trim());
      payload.append("registration_type", formData.registration_type);
      if (logoFile) {
        payload.append("logo", logoFile);
      }
      await createEvent(payload);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err, "Unable to create event"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="space-y-6">
      <BackButton />
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
            placeholder="dd/mm/yyyy hh:mm"
          />
          <p className="mt-1 text-xs text-slate-500">
            Use 24-hour time, e.g. 31/12/2026 18:30.
          </p>
        </label>

        <label className="block text-sm font-medium text-slate-700">
          QR code color
          <div className="mt-1 flex items-center gap-3">
            <input
              type="color"
              name="qr_color"
              value={formData.qr_color}
              onChange={handleChange}
              className="h-10 w-16 rounded-xl border border-slate-200"
              aria-label="QR code color"
            />
            <input
              type="text"
              name="qr_color"
              value={formData.qr_color}
              onChange={handleChange}
              className="flex-1 rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
              placeholder="#0f172a"
            />
          </div>
          {fieldErrors.qr_color ? (
            <p className="mt-1 text-xs text-red-600">
              {fieldErrors.qr_color}
            </p>
          ) : (
          <p className="mt-1 text-xs text-slate-500">
            This color is used for the QR code and event branding.
          </p>
          )}
        </label>

        <label className="block text-sm font-medium text-slate-700">
          QR caption
          <input
            type="text"
            name="qr_caption"
            value={formData.qr_caption}
            onChange={handleChange}
            className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder="Scan to check in"
          />
          <div className="mt-1 flex items-center justify-between text-xs">
            {fieldErrors.qr_caption ? (
              <span className="text-red-600">{fieldErrors.qr_caption}</span>
            ) : (
              <span className="text-slate-500">
                Leave empty to hide the caption below the QR code.
              </span>
            )}
            <span className="text-slate-400">
              {formData.qr_caption.length}/120
            </span>
          </div>
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Event logo (center of QR)
          <input
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleLogoChange}
            className="mt-1 block w-full text-sm text-slate-600 file:mr-4 file:rounded-full file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-slate-800"
          />
          <p className="mt-1 text-xs text-slate-500">
            PNG or JPG works best with a transparent or clean background.
          </p>
        </label>

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Registration type</p>
          <div className="flex gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
              <input
                type="radio"
                name="registration_type"
                value="private"
                checked={formData.registration_type === "private"}
                onChange={handleChange}
                className="accent-slate-900"
              />
              Private – admin adds guests manually
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
              <input
                type="radio"
                name="registration_type"
                value="public"
                checked={formData.registration_type === "public"}
                onChange={handleChange}
                className="accent-slate-900"
              />
              Public – anyone with the link can register
            </label>
          </div>
        </div>

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
