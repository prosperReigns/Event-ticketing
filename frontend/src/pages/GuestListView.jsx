import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import BackButton from "../components/BackButton.jsx";
import StatusAlert from "../components/StatusAlert.jsx";
import { getErrorMessage } from "../api/axios.js";
import { getEvent } from "../services/eventService.js";
import { deleteGuest, getGuests } from "../services/guestService.js";

const GuestListView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [guests, setGuests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [deletingGuestId, setDeletingGuestId] = useState("");
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
      [guest?.name, guest?.email, guest?.phone]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(query)),
    );
  }, [guests, searchTerm]);

  const handleDeleteGuest = async (guest) => {
    if (!guest?.id || deletingGuestId) {
      return;
    }
    const confirmed = window.confirm(
      `Remove ${guest.name || "this guest"} from the event?`,
    );
    if (!confirmed) {
      return;
    }
    setDeletingGuestId(guest.id);
    setError("");
    try {
      await deleteGuest(id, guest.id);
      setSuccessMessage(`${guest.name || "Guest"} removed.`);
      await loadGuests();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to remove guest"));
    } finally {
      setDeletingGuestId("");
    }
  };

  return (
    <section className="space-y-8">
      <BackButton />
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">Guest List</h1>
        <p className="text-sm text-slate-500">
          {event?.name || "Event"} guest roster and details.
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
            placeholder="Search by name, email, or phone"
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
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">Table</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredGuests.map((guest) => {
                const isDeleting = deletingGuestId === guest.id;
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
                    <td className="px-4 py-3 text-slate-600">
                      {guest.phone || "-"}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {guest.table_number || "-"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex flex-wrap justify-end gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            navigate(`/events/${id}/guests/${guest.id}/edit`)
                          }
                          className="rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
                        >
                          Update
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteGuest(guest)}
                          disabled={isDeleting}
                          className="rounded-full border border-rose-200 px-4 py-2 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {isDeleting ? "Removing..." : "Delete"}
                        </button>
                      </div>
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
