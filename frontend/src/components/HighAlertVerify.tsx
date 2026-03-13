interface HighAlertVerifyProps {
  pending: boolean;
  onConfirm?: () => void;
}

export function HighAlertVerify({ pending, onConfirm }: HighAlertVerifyProps) {
  if (!pending) return null;

  return (
    <section className="bg-highalert/10 border border-highalert rounded-lg p-4">
      <h2 className="text-sm font-semibold text-highalert mb-2">High-alert verification</h2>
      <p className="text-sm text-[var(--text)] mb-3">Waiting for secondary confirmation before pick.</p>
      <button
        type="button"
        onClick={onConfirm}
        className="px-3 py-1.5 rounded bg-highalert text-white text-sm font-medium hover:opacity-90"
      >
        Confirm
      </button>
    </section>
  );
}
