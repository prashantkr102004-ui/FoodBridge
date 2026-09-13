import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute";
import DashboardLayout from "./layouts/DashboardLayout";
import PublicLayout from "./layouts/PublicLayout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import DonorDashboard from "./pages/DonorDashboard";
import DonorImpact from "./pages/DonorImpact";
import DonationForm from "./pages/DonationForm";
import MyDonations from "./pages/MyDonations";
import DonationDetails from "./pages/DonationDetails";
import ReceiverDashboard from "./pages/ReceiverDashboard";
import ReceiverImpact from "./pages/ReceiverImpact";
import AvailableFood from "./pages/AvailableFood";
import SmartRecommendations from "./pages/SmartRecommendations";
import MyAcceptedDonations from "./pages/MyAcceptedDonations";
import AdminDashboard from "./pages/AdminDashboard";
import AdminAnalytics from "./pages/AdminAnalytics";
import AdminUsers from "./pages/AdminUsers";
import AdminUserDetails from "./pages/AdminUserDetails";
import AdminDonations from "./pages/AdminDonations";
import AdminDonationDetails from "./pages/AdminDonationDetails";
import Profile from "./pages/Profile";
import Notifications from "./pages/Notifications";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/profile" element={<Profile />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route element={<RoleRoute allowedRoles={["DONOR"]} />}>
            <Route path="/donor" element={<DonorDashboard />} />
            <Route path="/donor/impact" element={<DonorImpact />} />
            <Route path="/donor/post" element={<DonationForm mode="create" />} />
            <Route path="/donor/donations" element={<MyDonations />} />
            <Route path="/donor/donations/:id" element={<DonationDetails />} />
            <Route path="/donor/donations/:id/edit" element={<DonationForm mode="edit" />} />
          </Route>
          <Route element={<RoleRoute allowedRoles={["NGO", "VOLUNTEER"]} />}>
            <Route path="/receiver" element={<ReceiverDashboard />} />
            <Route path="/receiver/impact" element={<ReceiverImpact />} />
            <Route path="/receiver/available" element={<AvailableFood />} />
            <Route path="/receiver/recommendations" element={<SmartRecommendations />} />
            <Route path="/receiver/accepted" element={<MyAcceptedDonations />} />
            <Route path="/receiver/donations/:id" element={<DonationDetails />} />
          </Route>
          <Route element={<RoleRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/analytics" element={<AdminAnalytics />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/users/:id" element={<AdminUserDetails />} />
            <Route path="/admin/donations" element={<AdminDonations />} />
            <Route path="/admin/donations/:id" element={<AdminDonationDetails />} />
          </Route>
          <Route path="/unauthorized" element={<NotFound message="You do not have permission to view this page." />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
