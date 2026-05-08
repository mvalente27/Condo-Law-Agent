"use client";
import { StateCode } from "@/lib/api";

export default function StatePicker({
  value,
  onChange,
  states,
}: {
  value: StateCode | "";
  onChange: (s: StateCode | "") => void;
  states: { code: StateCode; name: string }[];
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="label">Jurisdiction</span>
      <select
        className="select max-w-[14rem]"
        value={value}
        onChange={(e) => onChange((e.target.value || "") as StateCode | "")}
      >
        <option value="">— select —</option>
        {states.map((s) => (
          <option key={s.code} value={s.code}>
            {s.code} · {s.name}
          </option>
        ))}
      </select>
    </div>
  );
}
