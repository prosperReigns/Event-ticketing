import { useCallback, useState } from "react";

import QRScanner from "../components/QRScanner.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { checkInGuest } from "../services/checkinService.js";

const extractToken = (rawValue) => {
  if (!rawValue) {
    return "";
  }

  try {
    const url = new URL(rawValue);
    const segments = url.pathname.split("/").filter(Boolean);
    const checkinIndex = segments.indexOf("checkin");
    if (checkinIndex >= 0 && segments[checkinIndex + 1]) {
      return segments[checkinIndex + 1];
    }
    return segments[segments.length - 1] || rawValue;
  } catch {
    const segments = rawValue.split("/").filter(Boolean);
    return segments[segments.length - 1] || rawValue;
  }
};

const CheckIn = () => {
  const [scanKey, setScanKey] = useState(0);
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");
  const [guest, setGuest] = useState(null);
  const [isChecking, setIsChecking] = useState(false);

  const handleScan = useCallback(
    async (rawValue) => {
      if (isChecking) {
        return;
      }

      setIsChecking(true);
      setStatus("");
      setMessage("");
      setGuest(null);

      const token = extractToken(rawValue);
      if (!token) {
        setStatus("error");
        setMessage("Invalid QR");
        setIsChecking(false);
        return;
      }

      try {
        const data = await checkInGuest(token);
        setGuest(data);
        setStatus("success");
        setMessage("Checked in successfully");
      } catch (err) {
        setStatus("error");
        setMessage(getErrorMessage(err, "Invalid QR"));
      } finally {
        setIsChecking(false);
      }
    },
    [isChecking],
  );

  const handleReset = () => {
    setScanKey((prev) => prev + 1);
    setStatus("");
    setMessage("");
    setGuest(null);
  };

  const cardStyles =
    status === "success"
      ? "border-emerald-200 bg-emerald-50"
      : status === "error"
        ? "border-rose-200 bg-rose-50"
        : "border-slate-200 bg-white";

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">QR Check-In</h1>
        <p className="text-sm text-slate-500">
          Scan guest QR codes for instant entry validation.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <QRScanner key={scanKey} onScan={handleScan} />
        </div>

        <div className={`rounded-3xl border p-6 shadow-sm ${cardStyles}`}>
          <h2 className="text-lg font-semibold text-slate-900">
            Scan status
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Results appear here immediately after each scan.
          </p>

          <div className="mt-4 space-y-3">
            <StatusAlert
              type={status === "success" ? "success" : "error"}
              message={message}
            />

            {guest && status === "success" ? (
              <div className="rounded-2xl border border-emerald-200 bg-white px-4 py-3 text-sm text-emerald-700">
                <p className="font-semibold text-emerald-800">
                  {guest.name || guest.guest_name || "Guest"}
                </p>
                <p>
                  Table: {guest.table_number || guest.table || "Not assigned"}
                </p>
              </div>
            ) : null}

            {isChecking ? (
              <p className="text-sm text-slate-500">Checking QR code...</p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={handleReset}
            className="mt-6 w-full rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
          >
            Scan another QR
          </button>
        </div>
      </div>
    </section>
  );
};

export default CheckIn;
