import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Layout from "./components/Layout";
import UploadPage from "./pages/UploadPage";
import RunsPage from "./pages/RunsPage";
import ReviewDashboard from "./pages/ReviewDashboard";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <UploadPage />,
      },
      {
        path: "runs",
        element: <RunsPage />,
      },
      {
        path: "review",
        element: <ReviewDashboard />,
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}