import { useEffect, useRef, useState } from "react";
import {
  getLlmSettings,
  saveLlmSettings,
  testLlmConnection,
  type LlmSettingsIn,
  type LlmSettingsOut,
  type LlmTestOut,
} from "../../services/api";
import "./Settings.css";

type ProviderTab = "local" | "external";
type TestStatus = "idle" | "testing" | "ok" | "error";

export function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testStatus, setTestStatus] = useState<TestStatus>("idle");
  const [testResult, setTestResult] = useState<LlmTestOut | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  // Form state
  const [provider, setProvider] = useState<ProviderTab>("local");
  const [baseUrl, setBaseUrl] = useState("https://openrouter.ai/api/v1");
  const [model, setModel] = useState("openai/gpt-4o-mini");
  const [apiKey, setApiKey] = useState("");
  const [quantize, setQuantize] = useState(true);
  const [maxTokens, setMaxTokens] = useState(1024);

  // Populated from GET /settings/llm
  const [current, setCurrent] = useState<LlmSettingsOut | null>(null);

  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* ── Load current settings ── */
  useEffect(() => {
    getLlmSettings()
      .then((s) => {
        setCurrent(s);
        setProvider(s.provider === "external" ? "external" : "local");
        setBaseUrl(s.external_api_base_url);
        setModel(s.external_api_model);
        setQuantize(s.llm_quantize_4bit);
        setMaxTokens(s.llm_max_new_tokens);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  /* ── Toast helper ── */
  function showToast(msg: string, ok: boolean) {
    setToast({ msg, ok });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 4000);
  }

  /* ── Save handler ── */
  async function handleSave() {
    setSaving(true);
    const payload: LlmSettingsIn = {
      provider,
      external_api_base_url: baseUrl,
      external_api_model: model,
      external_api_key: apiKey || undefined,
      llm_quantize_4bit: quantize,
      llm_max_new_tokens: maxTokens,
    };
    try {
      const updated = await saveLlmSettings(payload);
      setCurrent(updated);
      setApiKey(""); // clear after save
      setTestStatus("idle");
      setTestResult(null);
      showToast("Settings saved and adapter hot-swapped ✓", true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Save failed";
      showToast(msg, false);
    } finally {
      setSaving(false);
    }
  }

  /* ── Test connection handler ── */
  async function handleTest() {
    setTestStatus("testing");
    setTestResult(null);
    try {
      const result = await testLlmConnection();
      setTestResult(result);
      setTestStatus(result.ok ? "ok" : "error");
    } catch {
      setTestStatus("error");
      setTestResult({ ok: false, latency_ms: 0, model_used: "", provider, error: "Request failed" });
    }
  }

  /* ── VRAM estimate for local model ── */
  const vramEstimate = quantize ? "~1.2 GB" : "~3.5 GB";

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-loading">
          <output className="settings-spinner" />
          Loading settings…
        </div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <header className="settings-header">
        <h1 className="settings-title">
          <i className="bi bi-gear-wide-connected" aria-hidden="true" />
          AI Settings
        </h1>
        <p className="settings-subtitle">
          Configure the language model used for CV and cover-letter generation.
        </p>
      </header>

      {/* ── Provider toggle ── */}
      <section className="settings-card" aria-labelledby="provider-heading">
        <h2 id="provider-heading" className="settings-card-title">
          <i className="bi bi-cpu" aria-hidden="true" />
          AI Provider
        </h2>

        <div className="settings-toggle-row" role="group" aria-label="Provider selection">
          <button
            id="provider-local-btn"
            type="button"
            className={`settings-tab-btn ${provider === "local" ? "settings-tab-btn--active" : ""}`}
            onClick={() => setProvider("local")}
          >
            <i className="bi bi-hdd-rack" aria-hidden="true" />
            Local Model
          </button>
          <button
            id="provider-external-btn"
            type="button"
            className={`settings-tab-btn ${provider === "external" ? "settings-tab-btn--active" : ""}`}
            onClick={() => setProvider("external")}
          >
            <i className="bi bi-cloud-lightning" aria-hidden="true" />
            External API
          </button>
        </div>

        {/* ── External API fields ── */}
        {provider === "external" && (
          <div className="settings-fields">
            <div className="settings-field">
              <label htmlFor="base-url-input" className="settings-label">
                Base URL
                <span className="settings-hint">Any OpenAI-compatible endpoint</span>
              </label>
              <input
                id="base-url-input"
                type="url"
                className="settings-input"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://openrouter.ai/api/v1"
                spellCheck={false}
              />
            </div>

            <div className="settings-field">
              <label htmlFor="model-input" className="settings-label">
                Model Name
                <span className="settings-hint">Exact model slug from your provider</span>
              </label>
              <input
                id="model-input"
                type="text"
                className="settings-input"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="openai/gpt-4o-mini"
                spellCheck={false}
              />
            </div>

            <div className="settings-field">
              <label htmlFor="api-key-input" className="settings-label">
                API Key
                <span className="settings-hint">
                  {current?.has_api_key ? "🔑 Key configured — enter new to replace" : "Not configured"}
                </span>
              </label>
              <input
                id="api-key-input"
                type="password"
                className="settings-input"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={current?.has_api_key ? "••••••••••••••••" : "sk-…"}
                autoComplete="new-password"
              />
            </div>

            {/* Test connection */}
            <div className="settings-test-row">
              <button
                id="test-connection-btn"
                type="button"
                className="settings-btn settings-btn--ghost"
                onClick={handleTest}
                disabled={testStatus === "testing"}
              >
                {testStatus === "testing" ? (
                  <><output className="settings-spinner settings-spinner--sm" /> Testing…</>
                ) : (
                  <><i className="bi bi-lightning-charge" aria-hidden="true" /> Test Connection</>
                )}
              </button>

              {testResult && (
                <span
                  className={`settings-test-badge ${testResult.ok ? "settings-test-badge--ok" : "settings-test-badge--error"}`}
                >
                  {testResult.ok ? (
                    <><i className="bi bi-check-circle-fill" /> {testResult.latency_ms} ms · {testResult.model_used}</>
                  ) : (
                    <><i className="bi bi-x-circle-fill" /> {testResult.error ?? "Connection failed"}</>
                  )}
                </span>
              )}
            </div>
          </div>
        )}

        {/* ── Local model fields ── */}
        {provider === "local" && (
          <div className="settings-fields">
            <div className="settings-field">
              <div className="settings-toggle-field">
                <div>
                  <span className="settings-label">4-bit Quantization</span>
                  <span className="settings-hint">
                    Reduces VRAM from ~3.5 GB → ~1.2 GB. Requires CUDA GPU + bitsandbytes.
                  </span>
                </div>
                <button
                  id="quantize-toggle-btn"
                  type="button"
                  role="switch"
                  aria-checked={quantize}
                  className={`settings-switch ${quantize ? "settings-switch--on" : ""}`}
                  onClick={() => setQuantize((q) => !q)}
                >
                  <span className="settings-switch-thumb" />
                </button>
              </div>
            </div>

            <div className="settings-field">
              <label htmlFor="max-tokens-slider" className="settings-label">
                Max New Tokens
                <span className="settings-hint">Current: {maxTokens}</span>
              </label>
              <input
                id="max-tokens-slider"
                type="range"
                className="settings-slider"
                min={256}
                max={2048}
                step={128}
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
              />
              <div className="settings-slider-labels">
                <span>256 (fast)</span>
                <span>2048 (full CV)</span>
              </div>
            </div>

            <div className="settings-info-row">
              <i className="bi bi-memory" aria-hidden="true" />
              Estimated VRAM usage: <strong>{vramEstimate}</strong>
            </div>

            <div className="settings-info-row">
              <i className="bi bi-cpu" aria-hidden="true" />
              Active adapter:{" "}
              <strong>{current?.active_adapter ?? "—"}</strong>
            </div>
          </div>
        )}
      </section>

      {/* ── Save button ── */}
      <div className="settings-actions">
        <button
          id="save-settings-btn"
          type="button"
          className="settings-btn settings-btn--primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? (
            <><output className="settings-spinner settings-spinner--sm" /> Applying…</>
          ) : (
            <><i className="bi bi-check2-circle" /> Save & Apply</>
          )}
        </button>
      </div>

      {/* ── Toast ── */}
      {toast && (
        <output
          className={`settings-toast ${toast.ok ? "settings-toast--ok" : "settings-toast--error"}`}
        >
          <i className={`bi ${toast.ok ? "bi-check-circle-fill" : "bi-exclamation-triangle-fill"}`} />
          {toast.msg}
        </output>
      )}
    </div>
  );
}
