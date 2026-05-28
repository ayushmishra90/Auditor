import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import RowDetailModal from "../components/RowDetailModal";

const sourceOptions = [
  { value: "", label: "All sources" },
  { value: "sap", label: "SAP" },
  { value: "utility", label: "Utility" },
  { value: "travel", label: "Travel" },
];

const scopeOptions = [
  { value: "", label: "All scopes" },
  { value: "scope_1", label: "Scope 1" },
  { value: "scope_2", label: "Scope 2" },
  { value: "scope_3", label: "Scope 3" },
];

const statusOptions = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "needs_review", label: "Needs review" },
  { value: "locked", label: "Locked" },
  { value: "rejected", label: "Rejected" },
];

function StatusBadge({ status }) {
  const classes = {
    pending: "bg-blue-100 text-blue-800",
    needs_review: "bg-amber-100 text-amber-800",
    locked: "bg-emerald-100 text-emerald-800",
    rejected: "bg-red-100 text-red-800",
    failed: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium ${
        classes[status] || "bg-slate-100 text-slate-700"
      }`}
    >
      {status}
    </span>
  );
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function ReviewDashboard() {
  const [activities, setActivities] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    source_type: "",
    scope_category: "",
    status: "",
  });

  const queryString = useMemo(() => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });

    return params.toString();
  }, [filters]);

  async function loadData() {
    try {
      setLoading(true);

      const [activitiesResponse, summaryResponse] = await Promise.all([
        api.get(`/activities/${queryString ? `?${queryString}` : ""}`),
        api.get("/dashboard-summary/"),
      ]);

      setActivities(activitiesResponse.data.results || activitiesResponse.data);
      setSummary(summaryResponse.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [queryString]);

  async function refreshSummaryOnly() {
    const summaryResponse = await api.get("/dashboard-summary/");
    setSummary(summaryResponse.data);
  }
  
  async function approveActivity(activity) {
    const scrollY = window.scrollY;
  
    const response = await api.post(`/activities/${activity.id}/approve/`);
    const updatedActivity = response.data;
  
    setActivities((current) =>
      current.map((item) =>
        item.id === updatedActivity.id ? updatedActivity : item
      )
    );
  
    setSelectedActivity((current) =>
      current?.id === updatedActivity.id ? updatedActivity : current
    );
  
    await refreshSummaryOnly();
  
    requestAnimationFrame(() => {
      window.scrollTo({ top: scrollY, behavior: "auto" });
    });
  }
  
  async function rejectActivity(activity) {
    const scrollY = window.scrollY;
  
    const response = await api.post(`/activities/${activity.id}/reject/`);
    const updatedActivity = response.data;
  
    setActivities((current) =>
      current.map((item) =>
        item.id === updatedActivity.id ? updatedActivity : item
      )
    );
  
    setSelectedActivity((current) =>
      current?.id === updatedActivity.id ? updatedActivity : current
    );
  
    await refreshSummaryOnly();
  
    requestAnimationFrame(() => {
      window.scrollTo({ top: scrollY, behavior: "auto" });
    });
  }

  function updateFilter(key, value) {
    setFilters((current) => ({
      ...current,
      [key]: value,
    }));
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">
            Review dashboard
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Analysts can inspect raw rows, review warnings, approve rows, and
            lock them for audit.
          </p>
        </div>

        <button
          onClick={loadData}
          className="rounded-lg border bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-5">
        <SummaryCard label="Total rows" value={summary?.total_activities ?? "—"} />
        <SummaryCard label="Pending" value={summary?.pending_count ?? "—"} />
        <SummaryCard
          label="Needs review"
          value={summary?.needs_review_count ?? "—"}
        />
        <SummaryCard label="Locked" value={summary?.locked_count ?? "—"} />
        <SummaryCard label="Rejected" value={summary?.rejected_count ?? "—"} />
      </div>

      <div className="mb-4 flex flex-wrap gap-3 rounded-2xl border bg-white p-4 shadow-sm">
        <select
          value={filters.source_type}
          onChange={(event) => updateFilter("source_type", event.target.value)}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          {sourceOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={filters.scope_category}
          onChange={(event) =>
            updateFilter("scope_category", event.target.value)
          }
          className="rounded-lg border px-3 py-2 text-sm"
        >
          {scopeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(event) => updateFilter("status", event.target.value)}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-hidden rounded-2xl border bg-white shadow-sm">
        <table className="w-full table-fixed border-collapse text-left text-sm">          
        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
        <tr>
            <th className="w-[12%] px-4 py-3">Source</th>
            <th className="w-[12%] px-4 py-3">Date / Period</th>
            <th className="w-[9%] px-4 py-3">Facility</th>
            <th className="w-[18%] px-4 py-3">Activity</th>
            <th className="w-[9%] px-4 py-3">Scope</th>
            <th className="w-[20%] px-4 py-3">Warnings</th>
            <th className="w-[10%] px-4 py-3">Status</th>
            <th className="w-[10%] px-4 py-3">Actions</th>
        </tr>
        </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" className="px-4 py-8 text-center text-slate-500">
                  Loading...
                </td>
              </tr>
            ) : activities.length === 0 ? (
              <tr>
                <td colSpan="8" className="px-4 py-8 text-center text-slate-500">
                  No activities found.
                </td>
              </tr>
            ) : (
              activities.map((activity) => {
                const dateOrPeriod =
                  activity.activity_date ||
                  [activity.period_start, activity.period_end]
                    .filter(Boolean)
                    .join(" → ") ||
                  "—";

                  const isTerminal = activity.status === "locked" || activity.status === "rejected";
                return (
                  <tr key={activity.id} className="border-t align-top">
                    <td
                        className="truncate px-4 py-3 font-medium"
                        title={activity.source_system_name}
                        >
                        {activity.source_system_name}
                    </td>

                    <td className="truncate px-4 py-3" title={dateOrPeriod}>
                        {dateOrPeriod}
                    </td>

                    <td className="truncate px-4 py-3" title={activity.facility_code || "—"}>
                        {activity.facility_code || "—"}
                    </td>

                    <td className="truncate px-4 py-3" title={activity.activity_type}>
                        {activity.activity_type}
                    </td>

                    <td className="truncate px-4 py-3">{activity.scope_category}</td>

                    <td className="px-4 py-3 align-top">
                        {(activity.warning_flags || []).length === 0 ? (
                            <span className="text-slate-400">None</span>
                        ) : (
                            <div className="flex max-h-24 flex-wrap items-start gap-1 overflow-y-auto pr-1">
                            {(activity.warning_flags || []).map((warning) => (
                                <span
                                key={warning}
                                className="max-w-full break-words rounded-full bg-amber-100 px-2 py-1 text-[11px] leading-tight text-amber-800"
                                title={warning}
                                >
                                {warning}
                                </span>
                            ))}
                            </div>
                        )}
                    </td>

                    <td className="px-4 py-3">
                        <StatusBadge status={activity.status} />
                    </td>
                    <td className="sticky right-0 bg-white px-3 py-3 shadow-[-8px_0_12px_-12px_rgba(15,23,42,0.4)]">
                        <div className="flex min-w-[90px] flex-col gap-2">
                        <button
                          onClick={() => setSelectedActivity(activity)}
                          className="rounded-lg border px-3 py-1 text-xs hover:bg-slate-50"
                        >
                          View
                        </button>

                        {!isTerminal ? (
                            <>
                                <button
                                onClick={() => approveActivity(activity)}
                                className="rounded-lg bg-emerald-600 px-3 py-1 text-xs font-medium text-white"
                                >
                                Approve
                                </button>

                                <button
                                onClick={() => rejectActivity(activity)}
                                className="rounded-lg bg-red-600 px-3 py-1 text-xs font-medium text-white"
                                >
                                Reject
                                </button>
                            </>
                        ) : (
                            <span className="rounded-lg bg-slate-100 px-3 py-1 text-center text-xs text-slate-500">
                                No actions
                            </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <RowDetailModal
        activity={selectedActivity}
        onClose={() => setSelectedActivity(null)}
        onApprove={async (activity) => {
            await approveActivity(activity);
        }}
        onReject={async (activity) => {
            await rejectActivity(activity);
        }}
        />
    </div>
  );
}