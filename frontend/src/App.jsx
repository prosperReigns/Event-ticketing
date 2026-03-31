import { Navigate, Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import CheckIn from "./pages/CheckIn.jsx";
import CreateEvent from "./pages/CreateEvent.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import EventDetails from "./pages/EventDetails.jsx";
import GuestCheckinList from "./pages/GuestCheckinList.jsx";
import GuestList from "./pages/GuestList.jsx";
import GuestListView from "./pages/GuestListView.jsx";
import RsvpPage from "./pages/RsvpPage.jsx";
import UpdateEvent from "./pages/UpdateEvent.jsx";
import UpdateGuest from "./pages/UpdateGuest.jsx";

const App = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl px-4 pb-12 pt-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events/create" element={<CreateEvent />} />
          <Route path="/events/:id" element={<EventDetails />} />
          <Route path="/events/:id/edit" element={<UpdateEvent />} />
          <Route path="/events/:id/guests" element={<GuestList />} />
          <Route path="/events/:id/guests/view" element={<GuestListView />} />
          <Route
            path="/events/:id/guests/checkin"
            element={<GuestCheckinList />}
          />
          <Route
            path="/events/:id/guests/:guestId/edit"
            element={<UpdateGuest />}
          />
          <Route path="/checkin" element={<CheckIn />} />
          <Route path="/rsvp/:token" element={<RsvpPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
