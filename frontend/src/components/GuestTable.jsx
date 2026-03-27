const getCheckinStatus = (guest) => {
  return Boolean(
    guest?.checked_in ||
      guest?.is_checked_in ||
      guest?.checked_in_at ||
      guest?.check_in_time ||
      guest?.check_in_status === "checked_in",
  );
};

const GuestTable = ({ guests }) => {
  if (!guests?.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
        No guests have been added yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">Email</th>
            <th className="px-4 py-3">Table</th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {guests.map((guest) => {
            const checkedIn = getCheckinStatus(guest);
            return (
              <tr
                key={guest.id || `${guest.email}-${guest.name}`}
                className="border-t border-slate-100"
              >
                <td className="px-4 py-3 font-medium text-slate-900">
                  {guest.name}
                </td>
                <td className="px-4 py-3 text-slate-600">{guest.email}</td>
                <td className="px-4 py-3 text-slate-600">
                  {guest.table_number || "-"}
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
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default GuestTable;
