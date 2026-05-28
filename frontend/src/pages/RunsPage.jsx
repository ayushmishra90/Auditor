import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function RunsPage() {
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);

    async function loadRuns() {
        try {
            setLoading(true);
            const response = await api.get("/ingestion-runs/");
            setRuns(response.data.results || response.data);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadRuns();
    }, []);

    return (
        <div>
            <div className="mb-6 flex items-start justify-between">
                <div>
                    <h2 className="text-2xl font-semibold text-slate-900">
                        Ingestion runs
                    </h2>
                    <p className="mt-1 text-sm text-slate-600">
                        Track each uploaded file and whether rows succeeded or failed.
                    </p>
                </div>

                <button
                    onClick={loadRuns}
                    className="rounded-lg border bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                    Refresh
                </button>
            </div>

            <div className="overflow-hidden rounded-2xl border bg-white shadow-sm">
                <table className="w-full border-collapse text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                        <tr>
                            <th className="px-4 py-3">Source</th>
                            <th className="px-4 py-3">File</th>
                            <th className="px-4 py-3">Status</th>
                            <th className="px-4 py-3">Total</th>
                            <th className="px-4 py-3">Success</th>
                            <th className="px-4 py-3">Failed</th>
                            <th className="px-4 py-3">Created</th>
                            <th className="px-4 py-3">Error</th>
                        </tr>
                    </thead>

                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan="8" className="px-4 py-8 text-center text-slate-500">
                                    Loading...
                                </td>
                            </tr>
                        ) : runs.length === 0 ? (
                            <tr>
                                <td colSpan="8" className="px-4 py-8 text-center text-slate-500">
                                    No ingestion runs yet.
                                </td>
                            </tr>
                        ) : (
                            runs.map((run) => (
                                <tr key={run.id} className="border-t">
                                    <td className="px-4 py-3 font-medium">
                                        {run.source_system_name}
                                    </td>
                                    <td className="px-4 py-3">{run.uploaded_file_name}</td>
                                    <td className="px-4 py-3">
                                        <span
                                            className={`rounded-full px-2 py-1 text-xs font-medium ${run.status === "failed"
                                                    ? "bg-red-100 text-red-800"
                                                    : run.status === "completed_with_errors"
                                                        ? "bg-amber-100 text-amber-800"
                                                        : run.status === "completed"
                                                            ? "bg-emerald-100 text-emerald-800"
                                                            : "bg-slate-100 text-slate-700"
                                                }`}
                                        >
                                            {run.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">{run.total_rows}</td>
                                    <td className="px-4 py-3">{run.success_rows}</td>
                                    <td className="px-4 py-3">{run.failed_rows}</td>
                                    <td className="px-4 py-3">
                                        {new Date(run.created_at).toLocaleString()}
                                    </td>
                                    <td className="max-w-xs px-4 py-3 text-red-700">
                                        <div className="line-clamp-2" title={run.error_message || ""}>
                                            {run.error_message || "—"}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}