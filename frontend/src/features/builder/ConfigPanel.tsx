/**
 * Schema-driven node config panel.
 *
 * Reads NodeSpec.config_schema (JSON Schema) and renders form fields generically.
 * Adding a new node type = zero frontend changes. The backend schema drives everything.
 *
 * Supports: string (text/textarea), number (input[type=number]), boolean (checkbox),
 * enum (select). x-widget: "textarea" overrides string to textarea.
 */

import { useEffect } from "react";
import { useForm, type FieldValues } from "react-hook-form";
import { XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { NodeSpec } from "@/lib/api";

interface ConfigPanelProps {
  nodeId: string;
  nodeType: string;
  config: Record<string, unknown>;
  spec: NodeSpec;
  onSave: (nodeId: string, config: Record<string, unknown>) => void;
  onClose: () => void;
}

export function ConfigPanel({
  nodeId,
  nodeType,
  config,
  spec,
  onSave,
  onClose,
}: ConfigPanelProps) {
  const { register, handleSubmit, reset } = useForm({ defaultValues: config });

  useEffect(() => {
    reset(config);
  }, [nodeId, reset, config]);

  function onSubmit(values: FieldValues) {
    onSave(nodeId, values);
  }

  const schema = spec.config_schema as {
    properties?: Record<string, PropertySchema>;
    required?: string[];
  };
  const properties = schema.properties ?? {};
  const required = schema.required ?? [];

  return (
    <div className="flex h-full flex-col border-l border-[hsl(var(--border))] bg-[hsl(var(--bg-surface))] w-[280px] flex-shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[hsl(var(--border))] px-4 py-3">
        <div>
          <p className="text-xs font-medium">{spec.title}</p>
          <p className="text-[10px] text-[hsl(var(--text-faint))]">{nodeType}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <XIcon className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Description */}
      <p className="px-4 py-2 text-[11px] text-[hsl(var(--text-faint))] border-b border-[hsl(var(--border))]">
        {spec.description}
      </p>

      {/* Form fields */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-1 flex-col overflow-y-auto"
      >
        <div className="flex-1 space-y-4 p-4">
          {Object.entries(properties).map(([key, prop]) => (
            <Field
              key={key}
              fieldKey={key}
              prop={prop}
              required={required.includes(key)}
              register={register}
            />
          ))}
          {Object.keys(properties).length === 0 && (
            <p className="text-xs text-[hsl(var(--text-faint))]">
              No configuration needed for this node.
            </p>
          )}
        </div>

        <div className="border-t border-[hsl(var(--border))] p-4">
          <Button type="submit" size="sm" className="w-full">
            Apply
          </Button>
        </div>
      </form>
    </div>
  );
}

interface PropertySchema {
  type?: string | string[];
  title?: string;
  description?: string;
  default?: unknown;
  enum?: string[];
  minimum?: number;
  maximum?: number;
  "x-widget"?: string;
}

function Field({
  fieldKey,
  prop,
  required,
  register,
}: {
  fieldKey: string;
  prop: PropertySchema;
  required: boolean;
  register: ReturnType<typeof useForm>["register"];
}) {
  const label = prop.title ?? fieldKey;
  const isTextarea = prop["x-widget"] === "textarea";
  const isEnum = Array.isArray(prop.enum) && prop.enum.length > 0;
  const isNumber = prop.type === "number" || prop.type === "integer";
  const isBoolean = prop.type === "boolean";

  return (
    <div className="space-y-1">
      <label className="flex items-center gap-1 text-[11px] font-medium text-[hsl(var(--text-muted))]">
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>

      {prop.description && (
        <p className="text-[10px] text-[hsl(var(--text-faint))]">{prop.description}</p>
      )}

      {isBoolean ? (
        <input
          type="checkbox"
          {...register(fieldKey)}
          className="h-4 w-4 rounded border-[hsl(var(--border))] accent-[hsl(var(--accent))]"
        />
      ) : isEnum ? (
        <select
          {...register(fieldKey)}
          className={inputCls}
        >
          {prop.enum!.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : isTextarea ? (
        <textarea
          {...register(fieldKey)}
          rows={4}
          placeholder={String(prop.default ?? "")}
          className={cn(inputCls, "resize-none font-mono text-[11px]")}
        />
      ) : (
        <input
          type={isNumber ? "number" : "text"}
          {...register(fieldKey, { valueAsNumber: isNumber })}
          placeholder={String(prop.default ?? "")}
          min={prop.minimum}
          max={prop.maximum}
          className={inputCls}
        />
      )}
    </div>
  );
}

const inputCls =
  "w-full rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--bg-subtle))] px-2.5 py-1.5 text-xs outline-none transition-colors focus:border-[hsl(var(--accent))] focus:ring-1 focus:ring-[hsl(var(--accent)/0.3)]";
