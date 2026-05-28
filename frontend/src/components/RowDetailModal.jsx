export default function RowDetailModal({ activity, onClose, onApprove, onReject }) {
    if (!activity) return null;
  
    const isTerminal =
      activity.status === "locked" || activity.status === "rejected";
  
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
        <div className="max-h-[92vh] w-full max-w-5xl overflow-hidden rounded-2xl bg-white shadow-xl">
          <div className="flex items-start justify-between gap-4 border-b bg-white px-6 py-4">
            <div className="min-w-0">
              <h3 className="truncate text-lg font-semibold text-slate-900">
                Activity #{activity.id}
              </h3>
              <p className="truncate text-sm text-slate-500">
                {activity.source_system_name} · {activity.activity_type}
              </p>
            </div>
  
            <div className="flex shrink-0 items-center gap-2">
              {!isTerminal ? (
                <>
                  <button
                    onClick={() => onApprove?.(activity)}
                    className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                  >
                    Approve
                  </button>
  
                  <button
                    onClick={() => onReject?.(activity)}
                    className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
                  >
                    Reject
                  </button>
                </>
              ) : (
                <span className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-500">
                  No actions
                </span>
              )}
  
              <button
                onClick={onClose}
                className="rounded-lg border px-3 py-2 text-sm hover:bg-slate-50"
              >
                Close
              </button>
            </div>
          </div>
  
          <div className="max-h-[calc(92vh-80px)] overflow-y-auto p-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <section>
                <h4 className="mb-2 font-semibold text-slate-900">
                  Review summary
                </h4>
  
                <div className="rounded-xl border bg-slate-50 p-4 text-sm">
                  <dl className="grid grid-cols-2 gap-3">
                    <dt className="text-slate-500">Status</dt>
                    <dd className="font-medium">{activity.status}</dd>
  
                    <dt className="text-slate-500">Scope</dt>
                    <dd className="font-medium">{activity.scope_category}</dd>
  
                    <dt className="text-slate-500">Source</dt>
                    <dd className="font-medium">
                      {activity.source_system_name || "—"}
                    </dd>
  
                    <dt className="text-slate-500">Facility</dt>
                    <dd className="font-medium">
                      {activity.facility_code || "—"}
                    </dd>
  
                    <dt className="text-slate-500">Cost center</dt>
                    <dd className="font-medium">
                      {activity.cost_center || "—"}
                    </dd>
  
                    <dt className="text-slate-500">Activity date</dt>
                    <dd className="font-medium">
                      {activity.activity_date || "—"}
                    </dd>
  
                    <dt className="text-slate-500">Period</dt>
                    <dd className="font-medium">
                      {[activity.period_start, activity.period_end]
                        .filter(Boolean)
                        .join(" → ") || "—"}
                    </dd>
  
                    <dt className="text-slate-500">Vendor</dt>
                    <dd className="font-medium">
                      {activity.supplier_or_vendor || "—"}
                    </dd>
  
                    <dt className="text-slate-500">Amount</dt>
                    <dd className="font-medium">
                      {activity.amount || "—"} {activity.currency}
                    </dd>
  
                  </dl>
                </div>
  
                <h4 className="mb-2 mt-6 font-semibold text-slate-900">
                  Quantity normalization
                </h4>
  
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border bg-white p-4">
                    <p className="text-xs font-semibold uppercase text-slate-500">
                      Original value
                    </p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">
                      {activity.original_quantity || "—"} {activity.original_unit}
                    </p>
                  </div>
  
                  <div className="rounded-xl border bg-white p-4">
                    <p className="text-xs font-semibold uppercase text-slate-500">
                      Normalized value
                    </p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">
                      {activity.normalized_quantity || "—"}{" "}
                      {activity.normalized_unit}
                    </p>
                  </div>
                </div>
  
                <h4 className="mb-2 mt-6 font-semibold text-slate-900">
                  Warning flags
                </h4>
  
                <div className="flex flex-wrap gap-2">
                  {(activity.warning_flags || []).length === 0 ? (
                    <span className="text-sm text-slate-500">No warnings</span>
                  ) : (
                    activity.warning_flags.map((warning) => (
                      <span
                        key={warning}
                        className="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800"
                      >
                        {warning}
                      </span>
                    ))
                  )}
                </div>
              </section>
  
              <section>
                <h4 className="mb-2 font-semibold text-slate-900">
                  Raw source row
                </h4>
  
                <pre className="max-h-72 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
                  {JSON.stringify(activity.raw_record_payload, null, 2)}
                </pre>
  
                <h4 className="mb-2 mt-6 font-semibold text-slate-900">
                  Audit events
                </h4>
  
                <div className="space-y-2">
                  {(activity.audit_events || []).length === 0 ? (
                    <p className="text-sm text-slate-500">No audit events.</p>
                  ) : (
                    activity.audit_events.map((event) => (
                      <div
                        key={event.id}
                        className="rounded-lg border bg-white p-3 text-sm"
                      >
                        <div className="font-medium">{event.event_type}</div>
                        <div className="text-slate-500">{event.message}</div>
                        <div className="mt-1 text-xs text-slate-400">
                          {new Date(event.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    );
  }