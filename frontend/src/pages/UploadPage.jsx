import { useState } from "react";
import { api } from "../api/client";

const sources = [
  {
    sourceType: "sap",
    title: "SAP Fuel / Procurement",
    description:
      "Upload SAP-style procurement or fuel export with plant, material, quantity, unit, vendor, and posting date.",
    expected:
      "company_code, plant_code, material_code, material_description, posting_date, quantity, unit, cost_center, vendor, document_number, currency, amount",
  },
  {
    sourceType: "utility",
    title: "Utility Electricity",
    description:
      "Upload utility portal / Green Button-style electricity usage export with billing period and meter data.",
    expected:
      "account_number, meter_id, facility_code, bill_start, bill_end, usage, usage_unit, demand_kw, tariff_name, total_cost, currency, estimated",
  },
  {
    sourceType: "travel",
    title: "Corporate Travel",
    description:
      "Upload Concur/Navan-style travel expense export with flights, hotels, and ground transport.",
    expected:
      "report_id, employee_id, expense_type, transaction_date, origin_airport, destination_airport, distance_km, hotel_nights, ground_distance_km, amount, currency, vendor",
  },
];

function UploadCard({ source, onUploaded }) {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleUpload() {
    if (!file) {
      setMessage("Choose a CSV file first.");
      return;
    }

    const formData = new FormData();
    formData.append("source_type", source.sourceType);
    formData.append("file", file);

    try {
      setIsUploading(true);
      setMessage("");

      const response = await api.post("/ingest/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setMessage(
        `Uploaded. Rows: ${response.data.total_rows}, success: ${response.data.success_rows}, failed: ${response.data.failed_rows}`
      );
      setFile(null);
      onUploaded?.();
    } catch (error) {
      const detail =
        error.response?.data?.detail ||
        JSON.stringify(error.response?.data || {}) ||
        error.message;

      const failedRun = error.response?.data?.ingestion_run;

        if (failedRun) {
        setMessage(
            `Upload failed and was recorded as ingestion run #${failedRun.id}: ${detail}`
        );
        } else {
        setMessage(`Upload failed: ${detail}`);
        }
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">{source.title}</h2>
        <p className="mt-1 text-sm text-slate-600">{source.description}</p>
      </div>

      <div className="mb-4 rounded-lg bg-slate-50 p-3">
        <p className="text-xs font-semibold uppercase text-slate-500">
          Expected columns
        </p>
        <p className="mt-1 text-xs text-slate-700">{source.expected}</p>
      </div>

      <input
        type="file"
        accept=".csv"
        onChange={(event) => setFile(event.target.files?.[0] || null)}
        className="mb-4 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
      />

      <button
        onClick={handleUpload}
        disabled={isUploading}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isUploading ? "Uploading..." : "Upload CSV"}
      </button>

      {message && (
        <p className="mt-3 rounded-lg bg-slate-50 p-2 text-sm text-slate-700">
          {message}
        </p>
      )}
    </div>
  );
}

export default function UploadPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Upload data</h2>
        <p className="mt-1 text-sm text-slate-600">
          Upload one CSV per source. Each upload creates an ingestion run, raw
          records, normalized activities, warnings, and audit events.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {sources.map((source) => (
          <UploadCard key={source.sourceType} source={source} />
        ))}
      </div>
    </div>
  );
}