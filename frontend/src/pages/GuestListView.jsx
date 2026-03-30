import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvent } from "../services/eventService.js";
import { getGuests } from "../services/guestService.js";
import { checkInGuest } from "../services/checkinService.js";

const getCheckinStatus = (guest) => {
  return Boolean(
    guest?.checked_in ||
      guest?.is_checked_in ||
      guest?.checked_in_at ||
      guest?.check_in_time ||
      guest?.check_in_status === "checked_in" ||
      guest?.has_checked_in,
  );
};

const extractTokenFromQrUrl = (url) => {
  if (!url) {
    return null;
  }

  try {
    const base =
      typeof window !== "undefined"
        ? window.location.origin
        : "http://localhost";
    const parsedUrl = new URL(url, base);
    const fileName = parsedUrl.pathname.split("/").pop();
    return fileName ? fileName.replace(/\.png$/i, "") : null;
  } catch {
    const fileName = url.split("/").pop();
    return fileName ? fileName.replace(/\.png$/i, "") : null;
  }
};

const getGuestToken = (guest) => {
  return (
    guest?.unique_token ||
    guest?.token ||
    guest?.checkin_token ||
    guest?.check_in_token ||
    extractTokenFromQrUrl(guest?.qr_code_url)
  );
};

const GuestListView = () => {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [guests, setGuests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [checkingInToken, setCheckingInToken] = useState("");
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

  const filteredGuests = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) {
      return guests;
    }

    return guests.filter((guest) =>
      [guest?.name, guest?.email]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(query)),
    );
  }, [guests, searchTerm]);

  const handleCheckIn = async (guest) => {
    setError("");
    setSuccessMessage("");

    if (checkingInToken) {
      return;
    }

    const token = getGuestToken(guest);
    if (!token) {
      setError("Check-in token is not available for this guest.");
      return;
    }

    setCheckingInToken(token);
    try {
      const result = await checkInGuest(token);
      setSuccessMessage(result?.message || `${guest.name} checked in.`);
      await loadGuests();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to check in guest"));
    } finally {
      setCheckingInToken("");
    }
  };

  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">
          Guest Check-in List
        </h1>
        <p className="text-sm text-slate-500">
          {event?.name || "Event"} guest roster.
        </p>
      </div>

      <StatusAlert type="success" message={successMessage} />
      <StatusAlert type="error" message={error} />

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="block text-sm font-medium text-slate-700">
          Search guests
          <input
            type="text"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-slate-400 focus:outline-none"
            placeholder="Search by name or email"
          />
        </label>
      </div>

      {isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          Loading guests...
        </div>
      ) : filteredGuests.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
          No guests match your search.
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredGuests.map((guest) => {
                const checkedIn = getCheckinStatus(guest);
                const token = getGuestToken(guest);
                const isCheckingIn = Boolean(token) && checkingInToken === token;
                return (
                  <tr
                    key={guest.id || `${guest.email}-${guest.name}`}
                    className="border-t border-slate-100"
                  >
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {guest.name}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {guest.email || "-"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          checkedIn
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-rose-100 text-rose-700"
                        }`}
                      >
                        {checkedIn ? "Checked in" : "Not checked in"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleCheckIn(guest)}
                        disabled={!token || checkedIn || isCheckingIn}
                        className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                      >
                        {isCheckingIn
                          ? "Checking in..."
                          : checkedIn
                            ? "Checked in"
                            : "Check in"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
};

export default GuestListView;
